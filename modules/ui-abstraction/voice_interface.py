"""
Voice Interface Handler for AI-SERVIS
Handles voice input/output with WebRTC and audio processing
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
import websockets
from websockets.server import WebSocketServerProtocol
import base64
import io
import wave
import numpy as np
from datetime import datetime

from ui_models import (
    UIAdapter, UIAdapterConfig, InterfaceType, MessageType,
    CommandMessage, ResponseMessage, StatusMessage, ErrorMessage, UIMessage
)

logger = logging.getLogger(__name__)


class VoiceInterface(UIAdapter):
    """Voice interface adapter with WebRTC support"""
    
    def __init__(self, config: UIAdapterConfig):
        super().__init__(config)
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.audio_buffers: Dict[str, List[bytes]] = {}
        self.voice_activity_detection = VoiceActivityDetector()
        self.audio_processor = AudioProcessor()
        self.server = None
    
    async def start(self) -> None:
        """Start voice interface server"""
        if not self.config.enabled:
            return
        
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                self.config.host,
                self.config.port or 8081,
                max_size=10 * 1024 * 1024,  # 10MB max message size
                ping_interval=20,
                ping_timeout=10
            )
            
            self.is_running = True
            logger.info(f"Voice interface started on {self.config.host}:{self.config.port or 8081}")
            
            # Start background tasks
            asyncio.create_task(self._process_audio_streams())
            asyncio.create_task(self._cleanup_inactive_connections())
            
        except Exception as e:
            logger.error(f"Failed to start voice interface: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop voice interface server"""
        self.is_running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Close all connections
        for connection in self.connections.values():
            await connection.close()
        
        self.connections.clear()
        self.audio_buffers.clear()
        
        logger.info("Voice interface stopped")
    
    async def send_message(self, message: UIMessage, connection_id: Optional[str] = None) -> bool:
        """Send message to voice interface"""
        try:
            if connection_id and connection_id in self.connections:
                connection = self.connections[connection_id]
                await connection.send(json.dumps(message.dict()))
                self.stats.messages_sent += 1
                return True
            elif not connection_id:
                # Broadcast to all connections
                return await self.broadcast_message(message) > 0
            return False
        except Exception as e:
            logger.error(f"Error sending message to voice interface: {e}")
            self.stats.errors += 1
            return False
    
    async def broadcast_message(self, message: UIMessage) -> int:
        """Broadcast message to all voice connections"""
        sent_count = 0
        disconnected = []
        
        for connection_id, connection in self.connections.items():
            try:
                await connection.send(json.dumps(message.dict()))
                sent_count += 1
                self.stats.messages_sent += 1
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(connection_id)
            except Exception as e:
                logger.error(f"Error broadcasting to connection {connection_id}: {e}")
                self.stats.errors += 1
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self._handle_disconnection(connection_id)
        
        return sent_count
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = websocket
        self.audio_buffers[connection_id] = []
        
        await self.handle_connection(connection_id)
        
        try:
            async for message in websocket:
                await self._process_websocket_message(connection_id, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error handling connection {connection_id}: {e}")
            self.stats.errors += 1
        finally:
            await self._handle_disconnection(connection_id)
    
    async def _process_websocket_message(self, connection_id: str, message: str) -> None:
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "audio_data":
                await self._handle_audio_data(connection_id, data)
            elif message_type == "voice_command":
                await self._handle_voice_command(connection_id, data)
            elif message_type == "heartbeat":
                await self._handle_heartbeat(connection_id, data)
            elif message_type == "config":
                await self._handle_config_update(connection_id, data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from {connection_id}")
            self.stats.errors += 1
        except Exception as e:
            logger.error(f"Error processing message from {connection_id}: {e}")
            self.stats.errors += 1
    
    async def _handle_audio_data(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle incoming audio data"""
        try:
            audio_data = data.get("audio_data")
            if not audio_data:
                return
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Add to buffer
            if connection_id not in self.audio_buffers:
                self.audio_buffers[connection_id] = []
            
            self.audio_buffers[connection_id].append(audio_bytes)
            
            # Check for voice activity
            if self.voice_activity_detection.detect_voice_activity(audio_bytes):
                # Process audio for speech recognition
                await self._process_audio_for_speech(connection_id, audio_bytes)
            
        except Exception as e:
            logger.error(f"Error handling audio data from {connection_id}: {e}")
            self.stats.errors += 1
    
    async def _handle_voice_command(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle voice command"""
        try:
            command_text = data.get("command", "")
            user_id = data.get("user_id")
            session_id = data.get("session_id")
            context = data.get("context", {})
            
            # Create command message
            command_message = CommandMessage(
                id=str(uuid.uuid4()),
                interface_type=InterfaceType.VOICE,
                user_id=user_id,
                session_id=session_id,
                command=command_text,
                context=context,
                data={"connection_id": connection_id}
            )
            
            # Send status update
            status_message = StatusMessage(
                id=str(uuid.uuid4()),
                interface_type=InterfaceType.VOICE,
                user_id=user_id,
                session_id=session_id,
                status="Processing voice command...",
                data={"connection_id": connection_id}
            )
            await self.send_message(status_message, connection_id)
            
            # Handle the command
            await self.handle_message(command_message, connection_id)
            
        except Exception as e:
            logger.error(f"Error handling voice command from {connection_id}: {e}")
            self.stats.errors += 1
    
    async def _handle_heartbeat(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle heartbeat message"""
        try:
            heartbeat_message = UIMessage(
                id=str(uuid.uuid4()),
                type=MessageType.HEARTBEAT,
                interface_type=InterfaceType.VOICE,
                user_id=data.get("user_id"),
                session_id=data.get("session_id"),
                data={"connection_id": connection_id}
            )
            
            await self.handle_message(heartbeat_message, connection_id)
            
        except Exception as e:
            logger.error(f"Error handling heartbeat from {connection_id}: {e}")
            self.stats.errors += 1
    
    async def _handle_config_update(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle configuration update"""
        try:
            # Update voice activity detection settings
            if "vad_threshold" in data:
                self.voice_activity_detection.threshold = data["vad_threshold"]
            
            if "audio_format" in data:
                self.audio_processor.set_format(data["audio_format"])
            
            # Send confirmation
            response = {
                "type": "config_updated",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            if connection_id in self.connections:
                await self.connections[connection_id].send(json.dumps(response))
                
        except Exception as e:
            logger.error(f"Error handling config update from {connection_id}: {e}")
            self.stats.errors += 1
    
    async def _process_audio_for_speech(self, connection_id: str, audio_bytes: bytes) -> None:
        """Process audio for speech recognition"""
        try:
            # Convert audio to text (placeholder - would integrate with actual STT service)
            # For now, we'll simulate speech recognition
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # In a real implementation, this would call a speech-to-text service
            # For now, we'll create a mock response
            mock_commands = [
                "play music",
                "turn on lights",
                "what's the weather",
                "set volume to 50",
                "open browser"
            ]
            
            # Simulate command detection
            import random
            detected_command = random.choice(mock_commands)
            
            # Create voice command message
            command_data = {
                "type": "voice_command",
                "command": detected_command,
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat()
            }
            
            await self._handle_voice_command(connection_id, command_data)
            
        except Exception as e:
            logger.error(f"Error processing audio for speech: {e}")
            self.stats.errors += 1
    
    async def _process_audio_streams(self) -> None:
        """Process audio streams in background"""
        while self.is_running:
            try:
                await asyncio.sleep(0.1)
                
                # Process buffered audio data
                for connection_id, buffer in self.audio_buffers.items():
                    if len(buffer) > 10:  # Process when buffer has enough data
                        # Combine audio chunks
                        combined_audio = b''.join(buffer[-10:])  # Last 10 chunks
                        
                        # Process for voice activity
                        if self.voice_activity_detection.detect_voice_activity(combined_audio):
                            await self._process_audio_for_speech(connection_id, combined_audio)
                        
                        # Clear processed buffer
                        self.audio_buffers[connection_id] = buffer[-5:]  # Keep last 5 chunks
                
            except Exception as e:
                logger.error(f"Error processing audio streams: {e}")
                self.stats.errors += 1
    
    async def _cleanup_inactive_connections(self) -> None:
        """Clean up inactive connections"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                current_time = time.time()
                inactive_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Check if connection is still alive
                    try:
                        await connection.ping()
                    except:
                        inactive_connections.append(connection_id)
                
                # Remove inactive connections
                for connection_id in inactive_connections:
                    await self._handle_disconnection(connection_id)
                
            except Exception as e:
                logger.error(f"Error cleaning up connections: {e}")
                self.stats.errors += 1
    
    async def _handle_disconnection(self, connection_id: str) -> None:
        """Handle connection disconnection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        if connection_id in self.audio_buffers:
            del self.audio_buffers[connection_id]
        
        await self.handle_disconnection(connection_id)


class VoiceActivityDetector:
    """Simple voice activity detection"""
    
    def __init__(self, threshold: float = 0.01):
        self.threshold = threshold
        self.energy_history = []
        self.history_size = 10
    
    def detect_voice_activity(self, audio_data: bytes) -> bool:
        """Detect voice activity in audio data"""
        try:
            # Convert audio bytes to numpy array (assuming 16-bit PCM)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate energy
            energy = np.mean(audio_array.astype(np.float32) ** 2)
            
            # Update history
            self.energy_history.append(energy)
            if len(self.energy_history) > self.history_size:
                self.energy_history.pop(0)
            
            # Calculate average energy
            avg_energy = np.mean(self.energy_history)
            
            # Voice activity if energy is above threshold
            return energy > (avg_energy * 1.5) and energy > self.threshold
            
        except Exception as e:
            logger.error(f"Error in voice activity detection: {e}")
            return False


class AudioProcessor:
    """Audio processing utilities"""
    
    def __init__(self):
        self.sample_rate = 16000
        self.channels = 1
        self.sample_width = 2
    
    def set_format(self, format_config: Dict[str, Any]) -> None:
        """Set audio format"""
        self.sample_rate = format_config.get("sample_rate", 16000)
        self.channels = format_config.get("channels", 1)
        self.sample_width = format_config.get("sample_width", 2)
    
    def process_audio(self, audio_data: bytes) -> bytes:
        """Process audio data"""
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply simple noise reduction (placeholder)
            # In a real implementation, this would include proper noise reduction
            
            # Convert back to bytes
            return audio_array.astype(np.int16).tobytes()
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return audio_data
    
    def create_wav_header(self, data_length: int) -> bytes:
        """Create WAV file header"""
        try:
            # WAV header for 16-bit PCM
            header = wave.open(io.BytesIO(), 'wb')
            header.setnchannels(self.channels)
            header.setsampwidth(self.sample_width)
            header.setframerate(self.sample_rate)
            header.setnframes(data_length // (self.sample_width * self.channels))
            
            # Get header bytes
            header_bytes = header.getfp().getvalue()
            header.close()
            
            return header_bytes
            
        except Exception as e:
            logger.error(f"Error creating WAV header: {e}")
            return b''
