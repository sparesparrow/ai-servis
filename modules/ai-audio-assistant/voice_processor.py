"""
Voice Command Processing for Audio Assistant
Handles speech recognition and text-to-speech
"""
import asyncio
import logging
import tempfile
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
import json

from audio_models import VoiceProcessor, AudioCommand, AudioResponse

logger = logging.getLogger(__name__)


class AudioVoiceProcessor(VoiceProcessor):
    """Voice processor for audio commands"""
    
    def __init__(self):
        self.is_listening = False
        self.recognition_callbacks: List[Callable[[str], None]] = []
        self.available_voices: List[str] = []
        self.current_voice: Optional[str] = None
        self.is_initialized = False
        
        # Speech recognition
        self.recognizer = None
        self.microphone = None
        
        # Text-to-speech
        self.tts_engine = None
        
        # Voice command patterns
        self.command_patterns = self._initialize_command_patterns()
    
    def _initialize_command_patterns(self) -> Dict[str, List[str]]:
        """Initialize voice command patterns"""
        return {
            "play": [
                "play", "start", "begin", "turn on", "put on",
                "play music", "play song", "play track", "play album"
            ],
            "pause": [
                "pause", "hold", "stop", "halt", "freeze"
            ],
            "resume": [
                "resume", "continue", "unpause", "play again", "start again"
            ],
            "stop": [
                "stop", "end", "quit", "turn off", "shut off"
            ],
            "next": [
                "next", "skip", "next song", "next track", "skip song"
            ],
            "previous": [
                "previous", "back", "last song", "previous track", "go back"
            ],
            "volume": [
                "volume", "loud", "quiet", "louder", "quieter", "mute", "unmute"
            ],
            "shuffle": [
                "shuffle", "random", "mix", "shuffle mode"
            ],
            "repeat": [
                "repeat", "loop", "repeat song", "repeat playlist"
            ],
            "search": [
                "search", "find", "look for", "play something by"
            ]
        }
    
    async def initialize(self) -> bool:
        """Initialize voice processor"""
        try:
            # Initialize speech recognition
            await self._initialize_speech_recognition()
            
            # Initialize text-to-speech
            await self._initialize_tts()
            
            self.is_initialized = True
            logger.info("Voice processor initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize voice processor: {e}")
            return False
    
    async def _initialize_speech_recognition(self):
        """Initialize speech recognition"""
        try:
            import speech_recognition as sr
            
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info("Speech recognition initialized")
            
        except ImportError:
            logger.warning("SpeechRecognition not available, using fallback")
            self.recognizer = None
            self.microphone = None
        except Exception as e:
            logger.error(f"Error initializing speech recognition: {e}")
            self.recognizer = None
            self.microphone = None
    
    async def _initialize_tts(self):
        """Initialize text-to-speech"""
        try:
            import pyttsx3
            
            self.tts_engine = pyttsx3.init()
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            self.available_voices = [voice.id for voice in voices] if voices else []
            
            # Set default voice
            if self.available_voices:
                self.current_voice = self.available_voices[0]
                self.tts_engine.setProperty('voice', self.current_voice)
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 150)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.8)  # Volume level
            
            logger.info(f"Text-to-speech initialized with {len(self.available_voices)} voices")
            
        except ImportError:
            logger.warning("pyttsx3 not available, using fallback")
            self.tts_engine = None
        except Exception as e:
            logger.error(f"Error initializing TTS: {e}")
            self.tts_engine = None
    
    async def start_listening(self, callback: Callable[[str], None]) -> bool:
        """Start voice recognition"""
        try:
            if not self.is_initialized:
                logger.error("Voice processor not initialized")
                return False
            
            if self.is_listening:
                logger.warning("Already listening")
                return True
            
            # Add callback
            self.recognition_callbacks.append(callback)
            
            # Start listening in background
            asyncio.create_task(self._listen_loop())
            
            self.is_listening = True
            logger.info("Started voice recognition")
            return True
            
        except Exception as e:
            logger.error(f"Error starting voice recognition: {e}")
            return False
    
    async def stop_listening(self) -> bool:
        """Stop voice recognition"""
        try:
            self.is_listening = False
            self.recognition_callbacks.clear()
            logger.info("Stopped voice recognition")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping voice recognition: {e}")
            return False
    
    async def _listen_loop(self):
        """Main listening loop"""
        while self.is_listening:
            try:
                if self.recognizer and self.microphone:
                    # Use speech recognition
                    with self.microphone as source:
                        # Listen for audio with timeout
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    try:
                        # Recognize speech
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            logger.info(f"Recognized: {text}")
                            
                            # Process command
                            command = await self.process_voice_command(text)
                            
                            # Notify callbacks
                            for callback in self.recognition_callbacks:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(text)
                                    else:
                                        callback(text)
                                except Exception as e:
                                    logger.error(f"Error in recognition callback: {e}")
                    
                    except Exception as e:
                        # Recognition failed, continue listening
                        logger.debug(f"Recognition failed: {e}")
                
                else:
                    # Fallback: simulate voice input
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                await asyncio.sleep(1)
    
    async def process_voice_command(self, command: str) -> AudioCommand:
        """Process voice command and return audio command"""
        try:
            command_lower = command.lower().strip()
            
            # Parse command
            action, parameters = await self._parse_voice_command(command_lower)
            
            # Create audio command
            audio_command = AudioCommand(
                action=action,
                parameters=parameters,
                timestamp=datetime.now()
            )
            
            logger.info(f"Processed voice command: {action} with parameters: {parameters}")
            return audio_command
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return AudioCommand(
                action="error",
                parameters={"error": str(e), "original_command": command}
            )
    
    async def _parse_voice_command(self, command: str) -> tuple[str, Dict[str, Any]]:
        """Parse voice command into action and parameters"""
        try:
            # Find matching action
            action = "unknown"
            parameters = {}
            
            for action_name, patterns in self.command_patterns.items():
                for pattern in patterns:
                    if pattern in command:
                        action = action_name
                        break
                if action != "unknown":
                    break
            
            # Extract parameters based on action
            if action == "play":
                parameters = await self._extract_play_parameters(command)
            elif action == "volume":
                parameters = await self._extract_volume_parameters(command)
            elif action == "search":
                parameters = await self._extract_search_parameters(command)
            elif action in ["next", "previous", "pause", "resume", "stop"]:
                parameters = {"command": command}
            elif action == "shuffle":
                parameters = {"enabled": "on" in command or "enable" in command}
            elif action == "repeat":
                parameters = {"mode": "one" if "song" in command else "all"}
            
            return action, parameters
            
        except Exception as e:
            logger.error(f"Error parsing voice command: {e}")
            return "error", {"error": str(e)}
    
    async def _extract_play_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters for play command"""
        parameters = {}
        
        # Extract artist
        if "by" in command:
            parts = command.split("by")
            if len(parts) > 1:
                parameters["artist"] = parts[1].strip()
        
        # Extract song/track
        if "song" in command:
            song_start = command.find("song")
            if song_start != -1:
                song_part = command[song_start + 4:].strip()
                if "by" in song_part:
                    song_part = song_part.split("by")[0].strip()
                parameters["track"] = song_part
        
        # Extract album
        if "album" in command:
            album_start = command.find("album")
            if album_start != -1:
                album_part = command[album_start + 5:].strip()
                if "by" in album_part:
                    album_part = album_part.split("by")[0].strip()
                parameters["album"] = album_part
        
        # Extract genre
        genres = ["rock", "pop", "jazz", "classical", "country", "hip hop", "electronic", "blues"]
        for genre in genres:
            if genre in command:
                parameters["genre"] = genre
                break
        
        return parameters
    
    async def _extract_volume_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters for volume command"""
        parameters = {}
        
        # Extract volume level
        if "mute" in command:
            parameters["action"] = "mute"
        elif "unmute" in command:
            parameters["action"] = "unmute"
        elif "louder" in command or "up" in command:
            parameters["action"] = "increase"
        elif "quieter" in command or "down" in command:
            parameters["action"] = "decrease"
        else:
            # Extract specific volume level
            import re
            volume_match = re.search(r'(\d+)', command)
            if volume_match:
                volume = int(volume_match.group(1))
                parameters["action"] = "set"
                parameters["level"] = min(100, max(0, volume))
            else:
                parameters["action"] = "get"
        
        return parameters
    
    async def _extract_search_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters for search command"""
        parameters = {}
        
        # Extract search query
        search_keywords = ["search", "find", "look for", "play something by"]
        for keyword in search_keywords:
            if keyword in command:
                query = command.split(keyword, 1)[1].strip()
                parameters["query"] = query
                break
        
        return parameters
    
    async def speak(self, text: str, voice: Optional[str] = None) -> bool:
        """Text-to-speech"""
        try:
            if not self.tts_engine:
                logger.warning("TTS engine not available")
                return False
            
            # Set voice if specified
            if voice and voice in self.available_voices:
                self.tts_engine.setProperty('voice', voice)
                self.current_voice = voice
            
            # Speak text
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            logger.info(f"Spoke: {text}")
            return True
            
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return False
    
    async def get_available_voices(self) -> List[str]:
        """Get available TTS voices"""
        return self.available_voices.copy()
    
    async def set_voice(self, voice: str) -> bool:
        """Set TTS voice"""
        try:
            if voice in self.available_voices and self.tts_engine:
                self.tts_engine.setProperty('voice', voice)
                self.current_voice = voice
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            return False
    
    async def set_speech_rate(self, rate: int) -> bool:
        """Set speech rate"""
        try:
            if self.tts_engine:
                self.tts_engine.setProperty('rate', rate)
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting speech rate: {e}")
            return False
    
    async def set_speech_volume(self, volume: float) -> bool:
        """Set speech volume"""
        try:
            if self.tts_engine:
                self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting speech volume: {e}")
            return False
    
    async def get_voice_status(self) -> Dict[str, Any]:
        """Get voice processor status"""
        return {
            "is_initialized": self.is_initialized,
            "is_listening": self.is_listening,
            "available_voices": self.available_voices,
            "current_voice": self.current_voice,
            "recognition_callbacks": len(self.recognition_callbacks),
            "command_patterns": list(self.command_patterns.keys())
        }
    
    async def add_command_pattern(self, action: str, pattern: str):
        """Add custom command pattern"""
        if action not in self.command_patterns:
            self.command_patterns[action] = []
        self.command_patterns[action].append(pattern)
    
    async def remove_command_pattern(self, action: str, pattern: str):
        """Remove command pattern"""
        if action in self.command_patterns:
            try:
                self.command_patterns[action].remove(pattern)
            except ValueError:
                pass
    
    async def test_voice_recognition(self) -> Dict[str, Any]:
        """Test voice recognition"""
        try:
            if not self.recognizer or not self.microphone:
                return {
                    "success": False,
                    "message": "Speech recognition not available"
                }
            
            # Test recognition
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio)
            
            return {
                "success": True,
                "message": "Voice recognition test successful",
                "recognized_text": text
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Voice recognition test failed: {str(e)}"
            }
    
    async def test_tts(self, text: str = "Hello, this is a test of the text-to-speech system.") -> Dict[str, Any]:
        """Test text-to-speech"""
        try:
            if not self.tts_engine:
                return {
                    "success": False,
                    "message": "TTS engine not available"
                }
            
            # Test TTS
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            return {
                "success": True,
                "message": "TTS test successful",
                "spoken_text": text
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"TTS test failed: {str(e)}"
            }
