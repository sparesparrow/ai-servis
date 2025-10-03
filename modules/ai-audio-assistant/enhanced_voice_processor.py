"""
Enhanced Voice Processing for Audio Assistant
Handles speech recognition and text-to-speech with multiple providers
"""
import asyncio
import logging
import tempfile
import os
import json
import base64
import wave
import struct
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
import uuid
import aiohttp
import numpy as np
from enum import Enum

from audio_models import VoiceProcessor, AudioCommand, AudioResponse

logger = logging.getLogger(__name__)


class VoiceProvider(Enum):
    """Voice processing providers"""
    GOOGLE = "google"
    ELEVENLABS = "elevenlabs"
    WHISPER = "whisper"
    OPENAI = "openai"


class VoiceActivityState(Enum):
    """Voice activity detection states"""
    SILENT = "silent"
    SPEECH = "speech"
    NOISE = "noise"
    UNKNOWN = "unknown"


class WakeWordState(Enum):
    """Wake word detection states"""
    LISTENING = "listening"
    DETECTED = "detected"
    PROCESSING = "processing"
    TIMEOUT = "timeout"


class EnhancedVoiceProcessor(VoiceProcessor):
    """Enhanced voice processor with multiple providers and advanced features"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        
        # Provider configurations
        self.providers = {
            VoiceProvider.GOOGLE: self._init_google_provider(),
            VoiceProvider.ELEVENLABS: self._init_elevenlabs_provider(),
            VoiceProvider.WHISPER: self._init_whisper_provider(),
            VoiceProvider.OPENAI: self._init_openai_provider()
        }
        
        # Current active providers
        self.active_stt_provider = VoiceProvider.GOOGLE
        self.active_tts_provider = VoiceProvider.GOOGLE
        
        # Voice activity detection
        self.vad_enabled = True
        self.vad_threshold = 0.5
        self.vad_state = VoiceActivityState.SILENT
        self.silence_duration = 0.0
        self.speech_duration = 0.0
        
        # Wake word detection
        self.wake_word_enabled = True
        self.wake_words = ["hey assistant", "okay assistant", "computer"]
        self.wake_word_state = WakeWordState.LISTENING
        self.wake_word_detected = False
        
        # Command buffering
        self.command_buffer = []
        self.buffer_size = 10
        self.buffer_timeout = 5.0  # seconds
        
        # Audio processing
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_buffer = []
        self.is_recording = False
        
        # Performance tracking
        self.latency_target = 0.5  # 500ms target
        self.processing_times = []
        
        # Initialize components
        self._initialize_components()
    
    def _init_google_provider(self) -> Dict[str, Any]:
        """Initialize Google Cloud Speech/TTS provider"""
        return {
            "enabled": True,
            "api_key": self.config.get("google_api_key"),
            "project_id": self.config.get("google_project_id"),
            "language": self.config.get("language", "en-US"),
            "voices": [
                "en-US-Wavenet-A", "en-US-Wavenet-B", "en-US-Wavenet-C",
                "en-US-Wavenet-D", "en-US-Wavenet-E", "en-US-Wavenet-F"
            ]
        }
    
    def _init_elevenlabs_provider(self) -> Dict[str, Any]:
        """Initialize ElevenLabs provider"""
        return {
            "enabled": bool(self.config.get("elevenlabs_api_key")),
            "api_key": self.config.get("elevenlabs_api_key"),
            "base_url": "https://api.elevenlabs.io/v1",
            "voices": [],
            "model_id": "eleven_multilingual_v2"
        }
    
    def _init_whisper_provider(self) -> Dict[str, Any]:
        """Initialize Whisper offline provider"""
        return {
            "enabled": True,
            "model_size": self.config.get("whisper_model", "base"),
            "model_path": self.config.get("whisper_model_path"),
            "language": self.config.get("language", "en"),
            "device": self.config.get("whisper_device", "cpu")
        }
    
    def _init_openai_provider(self) -> Dict[str, Any]:
        """Initialize OpenAI provider"""
        return {
            "enabled": bool(self.config.get("openai_api_key")),
            "api_key": self.config.get("openai_api_key"),
            "model": "whisper-1",
            "language": self.config.get("language", "en")
        }
    
    def _initialize_components(self):
        """Initialize voice processing components"""
        try:
            # Initialize Whisper if available
            if self.providers[VoiceProvider.WHISPER]["enabled"]:
                self._load_whisper_model()
            
            # Load ElevenLabs voices if API key is available
            if self.providers[VoiceProvider.ELEVENLABS]["enabled"]:
                asyncio.create_task(self._load_elevenlabs_voices())
            
            self.is_initialized = True
            logger.info("Enhanced voice processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing voice processor: {e}")
            self.is_initialized = False
    
    def _load_whisper_model(self):
        """Load Whisper model for offline processing"""
        try:
            import whisper
            model_size = self.providers[VoiceProvider.WHISPER]["model_size"]
            self.whisper_model = whisper.load_model(model_size)
            logger.info(f"Whisper model {model_size} loaded successfully")
        except ImportError:
            logger.warning("Whisper not available. Install with: pip install openai-whisper")
            self.providers[VoiceProvider.WHISPER]["enabled"] = False
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            self.providers[VoiceProvider.WHISPER]["enabled"] = False
    
    async def _load_elevenlabs_voices(self):
        """Load available ElevenLabs voices"""
        try:
            api_key = self.providers[VoiceProvider.ELEVENLABS]["api_key"]
            base_url = self.providers[VoiceProvider.ELEVENLABS]["base_url"]
            
            async with aiohttp.ClientSession() as session:
                headers = {"xi-api-key": api_key}
                async with session.get(f"{base_url}/voices", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        voices = data.get("voices", [])
                        self.providers[VoiceProvider.ELEVENLABS]["voices"] = [
                            {"id": voice["voice_id"], "name": voice["name"]} 
                            for voice in voices
                        ]
                        logger.info(f"Loaded {len(voices)} ElevenLabs voices")
                    else:
                        logger.error(f"Failed to load ElevenLabs voices: {response.status}")
        except Exception as e:
            logger.error(f"Error loading ElevenLabs voices: {e}")
    
    async def start_listening(self, callback: Callable[[str], None]) -> bool:
        """Start voice recognition with enhanced features"""
        try:
            if not self.is_initialized:
                logger.error("Voice processor not initialized")
                return False
            
            self.recognition_callbacks.append(callback)
            self.is_listening = True
            self.wake_word_state = WakeWordState.LISTENING
            
            # Start voice activity detection
            if self.vad_enabled:
                asyncio.create_task(self._voice_activity_detection())
            
            # Start wake word detection
            if self.wake_word_enabled:
                asyncio.create_task(self._wake_word_detection())
            
            # Start command buffering
            asyncio.create_task(self._command_buffer_processor())
            
            logger.info("Enhanced voice recognition started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting voice recognition: {e}")
            return False
    
    async def stop_listening(self) -> bool:
        """Stop voice recognition"""
        try:
            self.is_listening = False
            self.wake_word_state = WakeWordState.LISTENING
            self.wake_word_detected = False
            
            # Process any remaining commands in buffer
            if self.command_buffer:
                await self._process_command_buffer()
            
            logger.info("Voice recognition stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping voice recognition: {e}")
            return False
    
    async def _voice_activity_detection(self):
        """Voice activity detection loop"""
        while self.is_listening:
            try:
                # Simulate audio analysis (in real implementation, this would analyze audio chunks)
                audio_level = await self._get_audio_level()
                
                if audio_level > self.vad_threshold:
                    if self.vad_state == VoiceActivityState.SILENT:
                        self.vad_state = VoiceActivityState.SPEECH
                        self.speech_duration = 0.0
                        logger.debug("Speech detected")
                    self.speech_duration += 0.1
                else:
                    if self.vad_state == VoiceActivityState.SPEECH:
                        self.vad_state = VoiceActivityState.SILENT
                        self.silence_duration = 0.0
                        logger.debug("Speech ended")
                    self.silence_duration += 0.1
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in voice activity detection: {e}")
                await asyncio.sleep(0.1)
    
    async def _wake_word_detection(self):
        """Wake word detection loop"""
        while self.is_listening:
            try:
                if self.wake_word_state == WakeWordState.LISTENING:
                    # Simulate wake word detection (in real implementation, this would use ML models)
                    detected = await self._detect_wake_word()
                    if detected:
                        self.wake_word_detected = True
                        self.wake_word_state = WakeWordState.DETECTED
                        logger.info("Wake word detected")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in wake word detection: {e}")
                await asyncio.sleep(0.1)
    
    async def _detect_wake_word(self) -> bool:
        """Detect wake words in audio stream"""
        # Placeholder for actual wake word detection
        # In real implementation, this would use models like Porcupine or custom ML models
        return False
    
    async def _get_audio_level(self) -> float:
        """Get current audio level for VAD"""
        # Placeholder for actual audio level detection
        # In real implementation, this would analyze audio chunks
        return 0.0
    
    async def _command_buffer_processor(self):
        """Process commands in buffer"""
        while self.is_listening:
            try:
                if self.command_buffer:
                    await self._process_command_buffer()
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in command buffer processor: {e}")
                await asyncio.sleep(0.5)
    
    async def _process_command_buffer(self):
        """Process all commands in buffer"""
        if not self.command_buffer:
            return
        
        # Combine commands if they're close in time
        combined_commands = self._combine_commands()
        
        for command in combined_commands:
            for callback in self.recognition_callbacks:
                try:
                    callback(command)
                except Exception as e:
                    logger.error(f"Error in recognition callback: {e}")
        
        self.command_buffer.clear()
    
    def _combine_commands(self) -> List[str]:
        """Combine related commands from buffer"""
        if not self.command_buffer:
            return []
        
        # Simple combination logic - in real implementation, this would be more sophisticated
        combined = []
        current_command = ""
        
        for command in self.command_buffer:
            if current_command:
                current_command += " " + command
            else:
                current_command = command
        
        if current_command:
            combined.append(current_command)
        
        return combined
    
    async def recognize_speech(self, audio_data: bytes, provider: Optional[VoiceProvider] = None) -> str:
        """Recognize speech using specified provider"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            provider = provider or self.active_stt_provider
            
            if provider == VoiceProvider.WHISPER and self.providers[VoiceProvider.WHISPER]["enabled"]:
                result = await self._recognize_with_whisper(audio_data)
            elif provider == VoiceProvider.GOOGLE and self.providers[VoiceProvider.GOOGLE]["enabled"]:
                result = await self._recognize_with_google(audio_data)
            elif provider == VoiceProvider.OPENAI and self.providers[VoiceProvider.OPENAI]["enabled"]:
                result = await self._recognize_with_openai(audio_data)
            else:
                result = await self._recognize_with_google(audio_data)  # Fallback
            
            # Track processing time
            processing_time = asyncio.get_event_loop().time() - start_time
            self.processing_times.append(processing_time)
            
            # Keep only recent processing times
            if len(self.processing_times) > 100:
                self.processing_times = self.processing_times[-100:]
            
            logger.debug(f"Speech recognition completed in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return ""
    
    async def _recognize_with_whisper(self, audio_data: bytes) -> str:
        """Recognize speech using Whisper"""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe using Whisper
            result = self.whisper_model.transcribe(
                temp_file_path,
                language=self.providers[VoiceProvider.WHISPER]["language"]
            )
            
            # Clean up
            os.unlink(temp_file_path)
            
            return result["text"].strip()
            
        except Exception as e:
            logger.error(f"Error in Whisper recognition: {e}")
            return ""
    
    async def _recognize_with_google(self, audio_data: bytes) -> str:
        """Recognize speech using Google Cloud Speech"""
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.sample_rate,
                language_code=self.providers[VoiceProvider.GOOGLE]["language"]
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Perform recognition
            response = client.recognize(config=config, audio=audio)
            
            if response.results:
                return response.results[0].alternatives[0].transcript
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error in Google Speech recognition: {e}")
            return ""
    
    async def _recognize_with_openai(self, audio_data: bytes) -> str:
        """Recognize speech using OpenAI Whisper API"""
        try:
            api_key = self.providers[VoiceProvider.OPENAI]["api_key"]
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe using OpenAI API
            async with aiohttp.ClientSession() as session:
                with open(temp_file_path, 'rb') as audio_file:
                    files = {'file': audio_file}
                    data = {
                        'model': self.providers[VoiceProvider.OPENAI]["model"],
                        'language': self.providers[VoiceProvider.OPENAI]["language"]
                    }
                    headers = {'Authorization': f'Bearer {api_key}'}
                    
                    async with session.post(
                        'https://api.openai.com/v1/audio/transcriptions',
                        files=files,
                        data=data,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            text = result.get('text', '').strip()
                            
                            # Clean up
                            os.unlink(temp_file_path)
                            
                            return text
                        else:
                            logger.error(f"OpenAI API error: {response.status}")
                            return ""
            
        except Exception as e:
            logger.error(f"Error in OpenAI recognition: {e}")
            return ""
    
    async def synthesize_speech(self, text: str, provider: Optional[VoiceProvider] = None, voice: Optional[str] = None) -> bytes:
        """Synthesize speech using specified provider"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            provider = provider or self.active_tts_provider
            
            if provider == VoiceProvider.ELEVENLABS and self.providers[VoiceProvider.ELEVENLABS]["enabled"]:
                result = await self._synthesize_with_elevenlabs(text, voice)
            elif provider == VoiceProvider.GOOGLE and self.providers[VoiceProvider.GOOGLE]["enabled"]:
                result = await self._synthesize_with_google(text, voice)
            else:
                result = await self._synthesize_with_google(text, voice)  # Fallback
            
            # Track processing time
            processing_time = asyncio.get_event_loop().time() - start_time
            self.processing_times.append(processing_time)
            
            logger.debug(f"Speech synthesis completed in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}")
            return b""
    
    async def _synthesize_with_elevenlabs(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize speech using ElevenLabs"""
        try:
            api_key = self.providers[VoiceProvider.ELEVENLABS]["api_key"]
            base_url = self.providers[VoiceProvider.ELEVENLABS]["base_url"]
            model_id = self.providers[VoiceProvider.ELEVENLABS]["model_id"]
            
            # Use default voice if not specified
            if not voice:
                voices = self.providers[VoiceProvider.ELEVENLABS]["voices"]
                voice = voices[0]["id"] if voices else "21m00Tcm4TlvDq8ikWAM"
            
            url = f"{base_url}/text-to-speech/{voice}"
            
            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"ElevenLabs API error: {response.status}")
                        return b""
            
        except Exception as e:
            logger.error(f"Error in ElevenLabs synthesis: {e}")
            return b""
    
    async def _synthesize_with_google(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize speech using Google Cloud TTS"""
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            # Configure synthesis
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice_config = texttospeech.VoiceSelectionParams(
                language_code=self.providers[VoiceProvider.GOOGLE]["language"],
                name=voice or "en-US-Wavenet-A"
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Perform synthesis
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Error in Google TTS synthesis: {e}")
            return b""
    
    async def speak(self, text: str, voice: Optional[str] = None) -> bool:
        """Speak text using current TTS provider"""
        try:
            audio_data = await self.synthesize_speech(text, voice=voice)
            if audio_data:
                # Play audio (this would integrate with the audio engine)
                logger.info(f"Speaking: {text}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error in speak: {e}")
            return False
    
    def add_command_to_buffer(self, command: str):
        """Add command to buffer for processing"""
        if len(self.command_buffer) >= self.buffer_size:
            self.command_buffer.pop(0)  # Remove oldest command
        
        self.command_buffer.append({
            "command": command,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def set_provider(self, stt_provider: VoiceProvider, tts_provider: VoiceProvider):
        """Set active providers"""
        self.active_stt_provider = stt_provider
        self.active_tts_provider = tts_provider
        logger.info(f"Providers set: STT={stt_provider.value}, TTS={tts_provider.value}")
    
    def set_wake_words(self, wake_words: List[str]):
        """Set wake words for detection"""
        self.wake_words = wake_words
        logger.info(f"Wake words set: {wake_words}")
    
    def set_vad_threshold(self, threshold: float):
        """Set voice activity detection threshold"""
        self.vad_threshold = threshold
        logger.info(f"VAD threshold set to {threshold}")
    
    async def get_voice_status(self) -> Dict[str, Any]:
        """Get comprehensive voice processor status"""
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times else 0.0
        )
        
        return {
            "initialized": self.is_initialized,
            "listening": self.is_listening,
            "providers": {
                "stt": self.active_stt_provider.value,
                "tts": self.active_tts_provider.value
            },
            "voice_activity": {
                "enabled": self.vad_enabled,
                "state": self.vad_state.value,
                "threshold": self.vad_threshold
            },
            "wake_word": {
                "enabled": self.wake_word_enabled,
                "state": self.wake_word_state.value,
                "detected": self.wake_word_detected,
                "words": self.wake_words
            },
            "command_buffer": {
                "size": len(self.command_buffer),
                "max_size": self.buffer_size
            },
            "performance": {
                "avg_processing_time": avg_processing_time,
                "latency_target": self.latency_target,
                "meets_target": avg_processing_time <= self.latency_target
            }
        }
