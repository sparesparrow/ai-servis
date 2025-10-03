"""
AI Audio Assistant MCP Server
Main entry point for the audio assistant module
"""
import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from mcp_framework import MCPServer, create_tool, MCPMessage

from audio_models import (
    AudioConfig, AudioManager, AudioDevice, AudioTrack, AudioZone,
    AudioSession, Playlist, AudioSource, AudioFormat, PlaybackState,
    AudioDeviceType
)
from audio_engine import CrossPlatformAudioEngine
from music_player import PyGameMusicPlayer
from voice_processor import AudioVoiceProcessor
from enhanced_voice_processor import EnhancedVoiceProcessor, VoiceProvider
from wake_word_detector import WakeWordDetector, WakeWordMethod
from voice_activity_detector import VoiceActivityDetector, VADMethod
from audio_converter import AudioConverter, AudioRouter
from music_service_abstraction import MusicServiceManager, MusicServiceType, Track, Playlist, SearchResult
from enhanced_music_player import EnhancedMusicPlayer, RepeatMode, ShuffleMode
from audio_zone_manager import AudioZoneManager, ZoneConfiguration, SyncMode, ContentFilter
from audio_sync_engine import AudioSyncEngine, SyncAlgorithm, SyncQuality

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AudioAssistantMCP(MCPServer):
    """Audio Assistant MCP Server"""
    
    def __init__(self):
        super().__init__("ai-audio-assistant", "1.0.0")
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.audio_engine = CrossPlatformAudioEngine(self.config)
        self.music_player = PyGameMusicPlayer(self.config)
        self.enhanced_music_player = EnhancedMusicPlayer(self.config)
        self.voice_processor = AudioVoiceProcessor()
        self.enhanced_voice_processor = EnhancedVoiceProcessor(self.config)
        self.wake_word_detector = WakeWordDetector(self.config)
        self.voice_activity_detector = VoiceActivityDetector(self.config)
        self.audio_converter = AudioConverter()
        self.audio_router = AudioRouter()
        self.audio_zone_manager = AudioZoneManager(self.config)
        self.audio_sync_engine = AudioSyncEngine(self.config)
        self.audio_manager = AudioManager(self.config)
        
        # Set up components
        self.audio_manager.engine = self.audio_engine
        self.audio_manager.player = self.music_player
        self.audio_manager.voice_processor = self.voice_processor
        
        # Setup tools
        self.setup_tools()
    
    def _load_config(self) -> AudioConfig:
        """Load configuration from environment or defaults"""
        return AudioConfig(
            default_volume=float(os.getenv("AUDIO_DEFAULT_VOLUME", "0.5")),
            max_volume=float(os.getenv("AUDIO_MAX_VOLUME", "1.0")),
            buffer_size=int(os.getenv("AUDIO_BUFFER_SIZE", "4096")),
            sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "44100")),
            channels=int(os.getenv("AUDIO_CHANNELS", "2")),
            bit_depth=int(os.getenv("AUDIO_BIT_DEPTH", "16")),
            crossfade_duration=float(os.getenv("AUDIO_CROSSFADE_DURATION", "2.0")),
            fade_in_duration=float(os.getenv("AUDIO_FADE_IN_DURATION", "1.0")),
            fade_out_duration=float(os.getenv("AUDIO_FADE_OUT_DURATION", "1.0")),
            auto_play=os.getenv("AUDIO_AUTO_PLAY", "true").lower() == "true",
            gapless_playback=os.getenv("AUDIO_GAPLESS_PLAYBACK", "true").lower() == "true",
            equalizer_enabled=os.getenv("AUDIO_EQUALIZER_ENABLED", "false").lower() == "true",
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY")
        )
    
    def setup_tools(self):
        """Setup MCP tools"""
        
        # Audio device management
        self.add_tool(create_tool(
            "list_audio_devices",
            "List available audio devices",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "set_default_device",
            "Set default audio device",
            {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "Device ID"}
                },
                "required": ["device_id"]
            }
        ))
        
        # Volume control
        self.add_tool(create_tool(
            "get_volume",
            "Get current volume",
            {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "Device ID (optional)"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "set_volume",
            "Set volume",
            {
                "type": "object",
                "properties": {
                    "volume": {"type": "number", "minimum": 0, "maximum": 1, "description": "Volume level (0-1)"},
                    "device_id": {"type": "string", "description": "Device ID (optional)"}
                },
                "required": ["volume"]
            }
        ))
        
        # Music playback
        self.add_tool(create_tool(
            "play_track",
            "Play a track",
            {
                "type": "object",
                "properties": {
                    "track": {"type": "object", "description": "Track information"},
                    "zone_id": {"type": "string", "description": "Zone ID"}
                },
                "required": ["track", "zone_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "pause_playback",
            "Pause playback",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone ID"}
                },
                "required": ["zone_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "resume_playback",
            "Resume playback",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone ID"}
                },
                "required": ["zone_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "stop_playback",
            "Stop playback",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone ID"}
                },
                "required": ["zone_id"]
            }
        ))
        
        # Voice processing
        self.add_tool(create_tool(
            "start_voice_recognition",
            "Start voice recognition",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "speak_text",
            "Text-to-speech",
            {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to speak"},
                    "voice": {"type": "string", "description": "Voice to use (optional)"}
                },
                "required": ["text"]
            }
        ))
        
        # Audio conversion and routing
        self.add_tool(create_tool(
            "convert_audio",
            "Convert audio file to different format",
            {
                "type": "object",
                "properties": {
                    "input_path": {"type": "string", "description": "Input file path"},
                    "output_format": {"type": "string", "description": "Output format (mp3, wav, flac, etc.)"},
                    "output_path": {"type": "string", "description": "Output file path (optional)"},
                    "sample_rate": {"type": "integer", "description": "Target sample rate (optional)"},
                    "channels": {"type": "integer", "description": "Target channels (optional)"},
                    "bit_depth": {"type": "integer", "description": "Target bit depth (optional)"}
                },
                "required": ["input_path", "output_format"]
            }
        ))
        
        self.add_tool(create_tool(
            "get_audio_info",
            "Get audio file information",
            {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Audio file path"}
                },
                "required": ["file_path"]
            }
        ))
        
        self.add_tool(create_tool(
            "create_audio_route",
            "Create audio routing configuration",
            {
                "type": "object",
                "properties": {
                    "route_id": {"type": "string", "description": "Route identifier"},
                    "source": {"type": "string", "description": "Source device or application"},
                    "destinations": {"type": "array", "description": "List of destination devices"}
                },
                "required": ["route_id", "source", "destinations"]
            }
        ))
        
        self.add_tool(create_tool(
            "activate_audio_route",
            "Activate audio route for session",
            {
                "type": "object",
                "properties": {
                    "route_id": {"type": "string", "description": "Route identifier"},
                    "session_id": {"type": "string", "description": "Session identifier"}
                },
                "required": ["route_id", "session_id"]
            }
        ))
        
        # Enhanced voice processing tools
        self.add_tool(create_tool(
            "set_voice_provider",
            "Set voice processing provider",
            {
                "type": "object",
                "properties": {
                    "stt_provider": {"type": "string", "description": "Speech-to-text provider (google, elevenlabs, whisper, openai)"},
                    "tts_provider": {"type": "string", "description": "Text-to-speech provider (google, elevenlabs)"}
                },
                "required": ["stt_provider", "tts_provider"]
            }
        ))
        
        self.add_tool(create_tool(
            "configure_wake_word",
            "Configure wake word detection",
            {
                "type": "object",
                "properties": {
                    "wake_words": {"type": "array", "description": "List of wake words"},
                    "sensitivity": {"type": "number", "description": "Detection sensitivity (0.0-1.0)"},
                    "method": {"type": "string", "description": "Detection method (porcupine, snowboy, custom_ml, keyword_spotting)"}
                },
                "required": ["wake_words"]
            }
        ))
        
        self.add_tool(create_tool(
            "configure_voice_activity",
            "Configure voice activity detection",
            {
                "type": "object",
                "properties": {
                    "method": {"type": "string", "description": "VAD method (energy_based, spectral_based, ml_based, webrtc)"},
                    "energy_threshold": {"type": "number", "description": "Energy threshold for detection"},
                    "spectral_threshold": {"type": "number", "description": "Spectral threshold for detection"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "start_enhanced_listening",
            "Start enhanced voice recognition with wake word and VAD",
            {
                "type": "object",
                "properties": {
                    "enable_wake_word": {"type": "boolean", "description": "Enable wake word detection"},
                    "enable_vad": {"type": "boolean", "description": "Enable voice activity detection"},
                    "buffer_commands": {"type": "boolean", "description": "Enable command buffering"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "get_voice_processing_status",
            "Get comprehensive voice processing status",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        # Music service integration tools
        self.add_tool(create_tool(
            "search_music",
            "Search for music across all services",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "service": {"type": "string", "description": "Service to search (spotify, apple_music, local_files, all)"},
                    "limit": {"type": "integer", "description": "Maximum number of results"}
                },
                "required": ["query"]
            }
        ))
        
        self.add_tool(create_tool(
            "play_track",
            "Play a specific track",
            {
                "type": "object",
                "properties": {
                    "track_id": {"type": "string", "description": "Track ID"},
                    "service": {"type": "string", "description": "Music service"},
                    "zone": {"type": "string", "description": "Audio zone"}
                },
                "required": ["track_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "play_playlist",
            "Play a playlist",
            {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Playlist ID"},
                    "service": {"type": "string", "description": "Music service"},
                    "start_index": {"type": "integer", "description": "Starting track index"},
                    "zone": {"type": "string", "description": "Audio zone"}
                },
                "required": ["playlist_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "control_playback",
            "Control music playback",
            {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action (play, pause, stop, next, previous, seek)"},
                    "position": {"type": "number", "description": "Seek position in seconds (for seek action)"}
                },
                "required": ["action"]
            }
        ))
        
        self.add_tool(create_tool(
            "set_playback_settings",
            "Set playback settings",
            {
                "type": "object",
                "properties": {
                    "volume": {"type": "number", "description": "Volume (0.0-1.0)"},
                    "repeat_mode": {"type": "string", "description": "Repeat mode (none, one, all)"},
                    "shuffle_mode": {"type": "string", "description": "Shuffle mode (off, on)"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "get_music_status",
            "Get music player status",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        # Audio zone management tools
        self.add_tool(create_tool(
            "create_audio_zone",
            "Create a new audio zone",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone identifier"},
                    "name": {"type": "string", "description": "Zone name"},
                    "description": {"type": "string", "description": "Zone description"},
                    "devices": {"type": "array", "description": "List of device IDs to assign to zone"},
                    "volume": {"type": "number", "description": "Initial volume (0.0-1.0)"},
                    "max_volume": {"type": "number", "description": "Maximum volume (0.0-1.0)"},
                    "min_volume": {"type": "number", "description": "Minimum volume (0.0-1.0)"}
                },
                "required": ["zone_id", "name"]
            }
        ))
        
        self.add_tool(create_tool(
            "delete_audio_zone",
            "Delete an audio zone",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone identifier"}
                },
                "required": ["zone_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "assign_device_to_zone",
            "Assign a device to an audio zone",
            {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "Device identifier"},
                    "zone_id": {"type": "string", "description": "Zone identifier"}
                },
                "required": ["device_id", "zone_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "set_zone_volume",
            "Set volume for an audio zone",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone identifier"},
                    "volume": {"type": "number", "description": "Volume level (0.0-1.0)"}
                },
                "required": ["zone_id", "volume"]
            }
        ))
        
        self.add_tool(create_tool(
            "mute_zone",
            "Mute or unmute an audio zone",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone identifier"},
                    "muted": {"type": "boolean", "description": "Mute state"}
                },
                "required": ["zone_id", "muted"]
            }
        ))
        
        self.add_tool(create_tool(
            "create_sync_group",
            "Create an audio synchronization group",
            {
                "type": "object",
                "properties": {
                    "group_id": {"type": "string", "description": "Sync group identifier"},
                    "name": {"type": "string", "description": "Sync group name"},
                    "zones": {"type": "array", "description": "List of zone IDs in the group"},
                    "master_zone": {"type": "string", "description": "Master zone ID"},
                    "sync_mode": {"type": "string", "description": "Sync mode (master_slave, peer_to_peer, time_based)"}
                },
                "required": ["group_id", "name", "zones", "master_zone"]
            }
        ))
        
        self.add_tool(create_tool(
            "set_zone_content_filter",
            "Set content filters for an audio zone",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone identifier"},
                    "filters": {"type": "array", "description": "Content filter types (explicit, genre, language, age_rating)"},
                    "allowed_genres": {"type": "array", "description": "Allowed music genres"},
                    "blocked_genres": {"type": "array", "description": "Blocked music genres"}
                },
                "required": ["zone_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "get_zone_status",
            "Get status of an audio zone",
            {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone identifier"}
                },
                "required": ["zone_id"]
            }
        ))
        
        self.add_tool(create_tool(
            "get_all_zones_status",
            "Get status of all audio zones",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        # System status
        self.add_tool(create_tool(
            "get_audio_status",
            "Get audio system status",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
    
    async def start(self):
        """Start the audio assistant"""
        try:
            logger.info("Starting AI Audio Assistant MCP Server")
            
            # Initialize audio manager
            await self.audio_manager.initialize()
            
            # Initialize enhanced music player
            await self.enhanced_music_player.initialize()
            
            # Initialize audio zone manager
            # (Zone manager initializes itself with default zones)
            
            # Initialize audio sync engine
            await self.audio_sync_engine.start()
            
            # Start MCP server
            await super().start()
            
            logger.info("AI Audio Assistant MCP Server started")
            
        except Exception as e:
            logger.error(f"Failed to start audio assistant: {e}")
            raise
    
    async def stop(self):
        """Stop the audio assistant"""
        try:
            logger.info("Stopping AI Audio Assistant MCP Server")
            
            # Stop audio manager
            await self.audio_manager.stop()
            
            # Stop MCP server
            await super().stop()
            
            logger.info("AI Audio Assistant MCP Server stopped")

        except Exception as e:
            logger.error(f"Error stopping audio assistant: {e}")
    
    # Tool handlers
    async def handle_list_audio_devices(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle list audio devices request"""
        try:
            devices = await self.audio_engine.get_devices()
            return {
                "success": True,
                "devices": [device.dict() for device in devices]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_set_volume(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle set volume request"""
        try:
            volume = message.params.get("volume")
            device_id = message.params.get("device_id")
            success = await self.audio_engine.set_volume(volume, device_id)
            return {
                "success": success,
                "message": f"Volume set to {volume:.1%}" if success else "Failed to set volume"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_play_track(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle play track request"""
        try:
            track_data = message.params.get("track")
            zone_id = message.params.get("zone_id")
            
            # Create track object
            track = AudioTrack(**track_data)
            
            # Play track
            result = await self.music_player.play(track, zone_id)
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_pause_playback(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle pause playback request"""
        try:
            zone_id = message.params.get("zone_id")
            result = await self.music_player.pause(zone_id)
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_resume_playback(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle resume playback request"""
        try:
            zone_id = message.params.get("zone_id")
            result = await self.music_player.resume(zone_id)
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_stop_playback(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle stop playback request"""
        try:
            zone_id = message.params.get("zone_id")
            result = await self.music_player.stop(zone_id)
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_start_voice_recognition(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle start voice recognition request"""
        try:
            def voice_callback(text: str):
                logger.info(f"Voice command received: {text}")
            
            success = await self.voice_processor.start_listening(voice_callback)
            
            return {
                "success": success,
                "message": "Voice recognition started" if success else "Failed to start voice recognition"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_speak_text(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle speak text request"""
        try:
            text = message.params.get("text")
            voice = message.params.get("voice")
            success = await self.voice_processor.speak(text, voice)

            return {
                "success": success,
                "message": f"Spoke: {text}" if success else "Failed to speak text"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_get_audio_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle get audio status request"""
        try:
            voice_status = await self.voice_processor.get_voice_status()
            
            return {
                "success": True,
                "status": {
                    "audio_engine": {
                        "initialized": self.audio_engine.is_initialized,
                        "devices": len(await self.audio_engine.get_devices())
                    },
                    "music_player": {
                        "initialized": self.music_player.is_initialized,
                        "zones": len(self.music_player.zones)
                    },
                    "voice_processor": voice_status
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_convert_audio(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle audio format conversion"""
        try:
            input_path = message.params.get("input_path", "")
            output_format = message.params.get("output_format", "")
            output_path = message.params.get("output_path")
            sample_rate = message.params.get("sample_rate")
            channels = message.params.get("channels")
            bit_depth = message.params.get("bit_depth")
            
            if not input_path or not output_format:
                return {"error": "Input path and output format are required"}
            
            # Convert string format to AudioFormat enum
            try:
                audio_format = AudioFormat(output_format.lower())
            except ValueError:
                return {"error": f"Unsupported audio format: {output_format}"}
            
            result = await self.audio_converter.convert_audio(
                input_path=input_path,
                output_format=audio_format,
                output_dir=os.path.dirname(output_path) if output_path else None,
                sample_rate=sample_rate,
                channels=channels,
                bitrate=f"{bit_depth}k" if bit_depth else None
            )
            
            if result.success:
                return {
                    "success": True,
                    "output_path": result.output_path,
                    "message": result.message
                }
            else:
                return {"error": result.error}
        except Exception as e:
            logger.error(f"Error in audio conversion: {e}")
            return {"error": str(e)}
    
    async def handle_get_audio_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting audio file information"""
        try:
            file_path = message.params.get("file_path", "")
            if not file_path:
                return {"error": "File path is required"}
            
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Try to get audio metadata using FFmpeg
            try:
                result = await asyncio.create_subprocess_exec(
                    "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    import json
                    metadata = json.loads(stdout.decode())
                    return {
                        "success": True,
                        "file_path": file_path,
                        "file_size": file_size,
                        "metadata": metadata
                    }
                else:
                    return {
                        "success": True,
                        "file_path": file_path,
                        "file_size": file_size,
                        "metadata": None,
                        "note": "Could not extract audio metadata"
                    }
            except Exception as e:
                logger.warning(f"Could not get audio metadata: {e}")
                return {
                    "success": True,
                    "file_path": file_path,
                    "file_size": file_size,
                    "metadata": None,
                    "note": "Could not extract audio metadata"
                }
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {"error": str(e)}
    
    async def handle_create_audio_route(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle creating audio routing configuration"""
        try:
            route_id = message.params.get("route_id", "")
            source = message.params.get("source", "")
            destinations = message.params.get("destinations", [])
            
            if not route_id or not source or not destinations:
                return {"error": "Route ID, source, and destinations are required"}
            
            # Create route configuration
            route_config = {
                "id": route_id,
                "source": source,
                "destinations": destinations,
                "created_at": asyncio.get_event_loop().time(),
                "active": False
            }
            
            # Store route configuration (in a real implementation, this would be persisted)
            if not hasattr(self, 'audio_routes'):
                self.audio_routes = {}
            self.audio_routes[route_id] = route_config
            
            return {
                "success": True,
                "route_id": route_id,
                "message": f"Audio route '{route_id}' created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating audio route: {e}")
            return {"error": str(e)}
    
    async def handle_activate_audio_route(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle activating audio route for session"""
        try:
            route_id = message.params.get("route_id", "")
            session_id = message.params.get("session_id", "")
            
            if not route_id or not session_id:
                return {"error": "Route ID and session ID are required"}
            
            # Check if route exists
            if not hasattr(self, 'audio_routes') or route_id not in self.audio_routes:
                return {"error": f"Audio route '{route_id}' not found"}
            
            # Activate route
            self.audio_routes[route_id]["active"] = True
            self.audio_routes[route_id]["session_id"] = session_id
            self.audio_routes[route_id]["activated_at"] = asyncio.get_event_loop().time()
            
            # Simulate routing activation
            route_config = self.audio_routes[route_id]
            success = await self.audio_router.route_audio_to_device(
                audio_stream=f"session_{session_id}",
                device_id=route_config["destinations"][0] if route_config["destinations"] else "default"
            )
            
            if success:
                return {
                    "success": True,
                    "route_id": route_id,
                    "session_id": session_id,
                    "message": f"Audio route '{route_id}' activated for session '{session_id}'"
                }
            else:
                return {"error": f"Failed to activate audio route '{route_id}'"}
        except Exception as e:
            logger.error(f"Error activating audio route: {e}")
            return {"error": str(e)}
    
    async def handle_set_voice_provider(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle setting voice processing provider"""
        try:
            stt_provider = message.params.get("stt_provider", "")
            tts_provider = message.params.get("tts_provider", "")
            
            if not stt_provider or not tts_provider:
                return {"error": "Both STT and TTS providers are required"}
            
            # Convert string to enum
            try:
                stt_enum = VoiceProvider(stt_provider.lower())
                tts_enum = VoiceProvider(tts_provider.lower())
            except ValueError as e:
                return {"error": f"Invalid provider: {e}"}
            
            # Set providers
            self.enhanced_voice_processor.set_provider(stt_enum, tts_enum)
            
            return {
                "success": True,
                "stt_provider": stt_provider,
                "tts_provider": tts_provider,
                "message": f"Voice providers set to STT={stt_provider}, TTS={tts_provider}"
            }
        except Exception as e:
            logger.error(f"Error setting voice provider: {e}")
            return {"error": str(e)}
    
    async def handle_configure_wake_word(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle configuring wake word detection"""
        try:
            wake_words = message.params.get("wake_words", [])
            sensitivity = message.params.get("sensitivity", 0.5)
            method = message.params.get("method", "porcupine")
            
            if not wake_words:
                return {"error": "Wake words are required"}
            
            # Set wake words
            self.wake_word_detector.set_wake_words(wake_words)
            self.enhanced_voice_processor.set_wake_words(wake_words)
            
            # Set sensitivity
            self.wake_word_detector.set_sensitivity(sensitivity)
            
            # Set method if provided
            if method:
                try:
                    method_enum = WakeWordMethod(method.lower())
                    self.wake_word_detector.method = method_enum
                except ValueError:
                    return {"error": f"Invalid wake word method: {method}"}
            
            return {
                "success": True,
                "wake_words": wake_words,
                "sensitivity": sensitivity,
                "method": method,
                "message": f"Wake word detection configured with {len(wake_words)} words"
            }
        except Exception as e:
            logger.error(f"Error configuring wake word: {e}")
            return {"error": str(e)}
    
    async def handle_configure_voice_activity(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle configuring voice activity detection"""
        try:
            method = message.params.get("method", "energy_based")
            energy_threshold = message.params.get("energy_threshold")
            spectral_threshold = message.params.get("spectral_threshold")
            
            # Set method if provided
            if method:
                try:
                    method_enum = VADMethod(method.lower())
                    self.voice_activity_detector.method = method_enum
                except ValueError:
                    return {"error": f"Invalid VAD method: {method}"}
            
            # Set thresholds if provided
            if energy_threshold is not None:
                self.voice_activity_detector.set_energy_threshold(energy_threshold)
            
            if spectral_threshold is not None:
                self.voice_activity_detector.set_spectral_threshold(spectral_threshold)
            
            return {
                "success": True,
                "method": method,
                "energy_threshold": energy_threshold,
                "spectral_threshold": spectral_threshold,
                "message": f"Voice activity detection configured with method {method}"
            }
        except Exception as e:
            logger.error(f"Error configuring voice activity: {e}")
            return {"error": str(e)}
    
    async def handle_start_enhanced_listening(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle starting enhanced voice recognition"""
        try:
            enable_wake_word = message.params.get("enable_wake_word", True)
            enable_vad = message.params.get("enable_vad", True)
            buffer_commands = message.params.get("buffer_commands", True)
            
            # Configure enhanced voice processor
            self.enhanced_voice_processor.vad_enabled = enable_vad
            self.enhanced_voice_processor.wake_word_enabled = enable_wake_word
            
            # Start enhanced listening
            def voice_callback(text: str):
                logger.info(f"Enhanced voice command received: {text}")
                if buffer_commands:
                    self.enhanced_voice_processor.add_command_to_buffer(text)
            
            success = await self.enhanced_voice_processor.start_listening(voice_callback)
            
            if success:
                return {
                    "success": True,
                    "enable_wake_word": enable_wake_word,
                    "enable_vad": enable_vad,
                    "buffer_commands": buffer_commands,
                    "message": "Enhanced voice recognition started successfully"
                }
            else:
                return {"error": "Failed to start enhanced voice recognition"}
        except Exception as e:
            logger.error(f"Error starting enhanced listening: {e}")
            return {"error": str(e)}
    
    async def handle_get_voice_processing_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting comprehensive voice processing status"""
        try:
            # Get status from all voice processing components
            enhanced_status = await self.enhanced_voice_processor.get_voice_status()
            wake_word_stats = self.wake_word_detector.get_detection_stats()
            vad_stats = self.voice_activity_detector.get_detection_stats()
            
            return {
                "success": True,
                "enhanced_voice_processor": enhanced_status,
                "wake_word_detector": wake_word_stats,
                "voice_activity_detector": vad_stats,
                "overall_status": {
                    "initialized": enhanced_status["initialized"],
                    "listening": enhanced_status["listening"],
                    "wake_word_enabled": enhanced_status["wake_word"]["enabled"],
                    "vad_enabled": enhanced_status["voice_activity"]["enabled"],
                    "meets_latency_target": enhanced_status["performance"]["meets_target"]
                }
            }
        except Exception as e:
            logger.error(f"Error getting voice processing status: {e}")
            return {"error": str(e)}
    
    async def handle_search_music(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle music search"""
        try:
            query = message.params.get("query", "")
            service = message.params.get("service", "all")
            limit = message.params.get("limit", 20)
            
            if not query:
                return {"error": "Search query is required"}
            
            # Convert service string to enum
            service_type = None
            if service != "all":
                try:
                    service_type = MusicServiceType(service.lower())
                except ValueError:
                    return {"error": f"Invalid service: {service}"}
            
            # Search music
            result = await self.enhanced_music_player.search_music(query, service_type, limit)
            
            return {
                "success": True,
                "query": query,
                "service": service,
                "results": {
                    "tracks": [
                        {
                            "id": track.id,
                            "title": track.title,
                            "artist": track.artist,
                            "album": track.album,
                            "duration": track.duration,
                            "service": track.service.value,
                            "preview_url": track.preview_url,
                            "image_url": track.image_url
                        } for track in result.tracks
                    ],
                    "albums": [
                        {
                            "id": album.id,
                            "title": album.title,
                            "artist": album.artist,
                            "service": album.service.value,
                            "image_url": album.image_url
                        } for album in result.albums
                    ],
                    "artists": [
                        {
                            "id": artist.id,
                            "name": artist.name,
                            "service": artist.service.value,
                            "image_url": artist.image_url
                        } for artist in result.artists
                    ],
                    "playlists": [
                        {
                            "id": playlist.id,
                            "name": playlist.name,
                            "description": playlist.description,
                            "service": playlist.service.value,
                            "total_tracks": playlist.total_tracks,
                            "image_url": playlist.image_url
                        } for playlist in result.playlists
                    ]
                },
                "totals": {
                    "tracks": result.total_tracks,
                    "albums": result.total_albums,
                    "artists": result.total_artists,
                    "playlists": result.total_playlists
                }
            }
        except Exception as e:
            logger.error(f"Error searching music: {e}")
            return {"error": str(e)}
    
    async def handle_play_track(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle playing a track"""
        try:
            track_id = message.params.get("track_id", "")
            service = message.params.get("service", "")
            zone = message.params.get("zone")
            
            if not track_id:
                return {"error": "Track ID is required"}
            
            # Get track from service
            service_type = None
            if service:
                try:
                    service_type = MusicServiceType(service.lower())
                except ValueError:
                    return {"error": f"Invalid service: {service}"}
            
            track = await self.enhanced_music_player.service_manager.get_track(track_id, service_type)
            if not track:
                return {"error": f"Track not found: {track_id}"}
            
            # Play track
            success = await self.enhanced_music_player.play_track(track, zone)
            
            if success:
                return {
                    "success": True,
                    "track": {
                        "id": track.id,
                        "title": track.title,
                        "artist": track.artist,
                        "album": track.album,
                        "duration": track.duration,
                        "service": track.service.value
                    },
                    "message": f"Playing: {track.title} by {track.artist}"
                }
            else:
                return {"error": "Failed to play track"}
        except Exception as e:
            logger.error(f"Error playing track: {e}")
            return {"error": str(e)}
    
    async def handle_play_playlist(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle playing a playlist"""
        try:
            playlist_id = message.params.get("playlist_id", "")
            service = message.params.get("service", "")
            start_index = message.params.get("start_index", 0)
            zone = message.params.get("zone")
            
            if not playlist_id:
                return {"error": "Playlist ID is required"}
            
            # Get playlist from service
            service_type = None
            if service:
                try:
                    service_type = MusicServiceType(service.lower())
                except ValueError:
                    return {"error": f"Invalid service: {service}"}
            
            playlist = await self.enhanced_music_player.service_manager.services.get(service_type).get_playlist(playlist_id)
            if not playlist:
                return {"error": f"Playlist not found: {playlist_id}"}
            
            # Play playlist
            success = await self.enhanced_music_player.play_playlist(playlist, start_index, zone)
            
            if success:
                return {
                    "success": True,
                    "playlist": {
                        "id": playlist.id,
                        "name": playlist.name,
                        "description": playlist.description,
                        "total_tracks": playlist.total_tracks,
                        "service": playlist.service.value
                    },
                    "start_index": start_index,
                    "message": f"Playing playlist: {playlist.name}"
                }
            else:
                return {"error": "Failed to play playlist"}
        except Exception as e:
            logger.error(f"Error playing playlist: {e}")
            return {"error": str(e)}
    
    async def handle_control_playback(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle playback control"""
        try:
            action = message.params.get("action", "").lower()
            position = message.params.get("position")
            
            if not action:
                return {"error": "Action is required"}
            
            success = False
            message_text = ""
            
            if action == "play":
                success = await self.enhanced_music_player.resume()
                message_text = "Playback resumed"
            elif action == "pause":
                success = await self.enhanced_music_player.pause()
                message_text = "Playback paused"
            elif action == "stop":
                success = await self.enhanced_music_player.stop()
                message_text = "Playback stopped"
            elif action == "next":
                success = await self.enhanced_music_player.next_track()
                message_text = "Playing next track"
            elif action == "previous":
                success = await self.enhanced_music_player.previous_track()
                message_text = "Playing previous track"
            elif action == "seek":
                if position is not None:
                    success = await self.enhanced_music_player.seek(position)
                    message_text = f"Seeked to {position} seconds"
                else:
                    return {"error": "Position required for seek action"}
            else:
                return {"error": f"Invalid action: {action}"}
            
            if success:
                return {
                    "success": True,
                    "action": action,
                    "message": message_text
                }
            else:
                return {"error": f"Failed to {action}"}
        except Exception as e:
            logger.error(f"Error controlling playback: {e}")
            return {"error": str(e)}
    
    async def handle_set_playback_settings(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle setting playback settings"""
        try:
            volume = message.params.get("volume")
            repeat_mode = message.params.get("repeat_mode")
            shuffle_mode = message.params.get("shuffle_mode")
            
            settings_changed = []
            
            if volume is not None:
                success = self.enhanced_music_player.set_volume(volume)
                if success:
                    settings_changed.append(f"volume={volume:.1%}")
            
            if repeat_mode:
                try:
                    repeat_enum = RepeatMode(repeat_mode.lower())
                    success = self.enhanced_music_player.set_repeat_mode(repeat_enum)
                    if success:
                        settings_changed.append(f"repeat_mode={repeat_mode}")
                except ValueError:
                    return {"error": f"Invalid repeat mode: {repeat_mode}"}
            
            if shuffle_mode:
                try:
                    shuffle_enum = ShuffleMode(shuffle_mode.lower())
                    success = self.enhanced_music_player.set_shuffle_mode(shuffle_enum)
                    if success:
                        settings_changed.append(f"shuffle_mode={shuffle_mode}")
                except ValueError:
                    return {"error": f"Invalid shuffle mode: {shuffle_mode}"}
            
            return {
                "success": True,
                "settings_changed": settings_changed,
                "message": f"Updated settings: {', '.join(settings_changed)}"
            }
        except Exception as e:
            logger.error(f"Error setting playback settings: {e}")
            return {"error": str(e)}

    async def handle_get_music_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting music player status"""
        try:
            status = self.enhanced_music_player.get_status()

            return {
                "success": True,
                "status": status
            }
        except Exception as e:
            logger.error(f"Error getting music status: {e}")
            return {"error": str(e)}
    
    async def handle_create_audio_zone(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle creating an audio zone"""
        try:
            zone_id = message.params.get("zone_id", "")
            name = message.params.get("name", "")
            description = message.params.get("description", "")
            devices = message.params.get("devices", [])
            volume = message.params.get("volume", 1.0)
            max_volume = message.params.get("max_volume", 1.0)
            min_volume = message.params.get("min_volume", 0.0)
            
            if not zone_id or not name:
                return {"error": "Zone ID and name are required"}
            
            # Create zone
            success = await self.audio_zone_manager.create_zone(
                zone_id=zone_id,
                name=name,
                description=description,
                devices=devices,
                volume=volume,
                max_volume=max_volume,
                min_volume=min_volume
            )
            
            if success:
                return {
                    "success": True,
                    "zone_id": zone_id,
                    "name": name,
                    "message": f"Created audio zone: {name}"
                }
            else:
                return {"error": f"Failed to create zone: {zone_id}"}
        except Exception as e:
            logger.error(f"Error creating audio zone: {e}")
            return {"error": str(e)}
    
    async def handle_delete_audio_zone(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle deleting an audio zone"""
        try:
            zone_id = message.params.get("zone_id", "")
            
            if not zone_id:
                return {"error": "Zone ID is required"}
            
            success = await self.audio_zone_manager.delete_zone(zone_id)
            
            if success:
                return {
                    "success": True,
                    "zone_id": zone_id,
                    "message": f"Deleted audio zone: {zone_id}"
                }
            else:
                return {"error": f"Failed to delete zone: {zone_id}"}
        except Exception as e:
            logger.error(f"Error deleting audio zone: {e}")
            return {"error": str(e)}
    
    async def handle_assign_device_to_zone(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle assigning a device to a zone"""
        try:
            device_id = message.params.get("device_id", "")
            zone_id = message.params.get("zone_id", "")
            
            if not device_id or not zone_id:
                return {"error": "Device ID and zone ID are required"}
            
            success = await self.audio_zone_manager.assign_device_to_zone(device_id, zone_id)
            
            if success:
                return {
                    "success": True,
                    "device_id": device_id,
                    "zone_id": zone_id,
                    "message": f"Assigned device {device_id} to zone {zone_id}"
                }
            else:
                return {"error": f"Failed to assign device {device_id} to zone {zone_id}"}
        except Exception as e:
            logger.error(f"Error assigning device to zone: {e}")
            return {"error": str(e)}
    
    async def handle_set_zone_volume(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle setting zone volume"""
        try:
            zone_id = message.params.get("zone_id", "")
            volume = message.params.get("volume")
            
            if not zone_id or volume is None:
                return {"error": "Zone ID and volume are required"}
            
            success = await self.audio_zone_manager.set_zone_volume(zone_id, volume)
            
            if success:
                return {
                    "success": True,
                    "zone_id": zone_id,
                    "volume": volume,
                    "message": f"Zone {zone_id} volume set to {volume:.1%}"
                }
            else:
                return {"error": f"Failed to set volume for zone {zone_id}"}
        except Exception as e:
            logger.error(f"Error setting zone volume: {e}")
            return {"error": str(e)}
    
    async def handle_mute_zone(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle muting/unmuting a zone"""
        try:
            zone_id = message.params.get("zone_id", "")
            muted = message.params.get("muted")
            
            if not zone_id or muted is None:
                return {"error": "Zone ID and muted state are required"}
            
            success = await self.audio_zone_manager.mute_zone(zone_id, muted)
            
            if success:
                return {
                    "success": True,
                    "zone_id": zone_id,
                    "muted": muted,
                    "message": f"Zone {zone_id} {'muted' if muted else 'unmuted'}"
                }
            else:
                return {"error": f"Failed to mute/unmute zone {zone_id}"}
        except Exception as e:
            logger.error(f"Error muting zone: {e}")
            return {"error": str(e)}
    
    async def handle_create_sync_group(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle creating a sync group"""
        try:
            group_id = message.params.get("group_id", "")
            name = message.params.get("name", "")
            zones = message.params.get("zones", [])
            master_zone = message.params.get("master_zone", "")
            sync_mode_str = message.params.get("sync_mode", "master_slave")
            
            if not all([group_id, name, zones, master_zone]):
                return {"error": "Group ID, name, zones, and master zone are required"}
            
            # Convert sync mode string to enum
            try:
                sync_mode = SyncMode(sync_mode_str.lower())
            except ValueError:
                return {"error": f"Invalid sync mode: {sync_mode_str}"}
            
            # Create sync group in zone manager
            success = await self.audio_zone_manager.create_sync_group(
                group_id=group_id,
                name=name,
                zones=zones,
                master_zone=master_zone,
                sync_mode=sync_mode
            )
            
            if success:
                # Create sync group in sync engine
                slave_zones = [z for z in zones if z != master_zone]
                await self.audio_sync_engine.add_sync_group(group_id, master_zone, slave_zones)
                
                return {
                    "success": True,
                    "group_id": group_id,
                    "name": name,
                    "zones": zones,
                    "master_zone": master_zone,
                    "sync_mode": sync_mode.value,
                    "message": f"Created sync group: {name}"
                }
            else:
                return {"error": f"Failed to create sync group: {group_id}"}
        except Exception as e:
            logger.error(f"Error creating sync group: {e}")
            return {"error": str(e)}
    
    async def handle_set_zone_content_filter(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle setting zone content filters"""
        try:
            zone_id = message.params.get("zone_id", "")
            filters = message.params.get("filters", [])
            allowed_genres = message.params.get("allowed_genres", [])
            blocked_genres = message.params.get("blocked_genres", [])
            
            if not zone_id:
                return {"error": "Zone ID is required"}
            
            # Convert filter strings to enums
            content_filters = []
            for filter_str in filters:
                try:
                    content_filters.append(ContentFilter(filter_str.lower()))
                except ValueError:
                    logger.warning(f"Invalid content filter: {filter_str}")
            
            # Set content filters
            if content_filters:
                success = await self.audio_zone_manager.set_zone_content_filter(zone_id, content_filters)
                if not success:
                    return {"error": f"Failed to set content filters for zone {zone_id}"}
            
            # Set genre filters
            if allowed_genres or blocked_genres:
                success = await self.audio_zone_manager.set_zone_genre_filters(
                    zone_id, allowed_genres, blocked_genres
                )
                if not success:
                    return {"error": f"Failed to set genre filters for zone {zone_id}"}
            
            return {
                "success": True,
                "zone_id": zone_id,
                "content_filters": [f.value for f in content_filters],
                "allowed_genres": allowed_genres,
                "blocked_genres": blocked_genres,
                "message": f"Set content filters for zone {zone_id}"
            }
        except Exception as e:
            logger.error(f"Error setting zone content filters: {e}")
            return {"error": str(e)}
    
    async def handle_get_zone_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting zone status"""
        try:
            zone_id = message.params.get("zone_id", "")
            
            if not zone_id:
                return {"error": "Zone ID is required"}
            
            status = await self.audio_zone_manager.get_zone_status(zone_id)
            
            if status:
                return {
                    "success": True,
                    "zone_id": zone_id,
                    "status": status
                }
            else:
                return {"error": f"Zone not found: {zone_id}"}
        except Exception as e:
            logger.error(f"Error getting zone status: {e}")
            return {"error": str(e)}
    
    async def handle_get_all_zones_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting all zones status"""
        try:
            status = await self.audio_zone_manager.get_all_zones_status()
            
            return {
                "success": True,
                "status": status
            }
        except Exception as e:
            logger.error(f"Error getting all zones status: {e}")
            return {"error": str(e)}


async def main():
    """Main entry point"""
    logger.info("Starting AI Audio Assistant MCP Server")

    # Create and start audio assistant
    audio_assistant = AudioAssistantMCP()
    
    try:
        await audio_assistant.start()
        
        # Keep running
        logger.info("Audio Assistant is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down Audio Assistant")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await audio_assistant.stop()


if __name__ == "__main__":
    asyncio.run(main())