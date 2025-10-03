"""
Wake Word Detection for Audio Assistant
Handles wake word detection using multiple methods
"""
import asyncio
import logging
import numpy as np
import struct
import wave
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import tempfile
import os

logger = logging.getLogger(__name__)


class WakeWordMethod(Enum):
    """Wake word detection methods"""
    PORCUPINE = "porcupine"
    SNOWBOY = "snowboy"
    CUSTOM_ML = "custom_ml"
    KEYWORD_SPOTTING = "keyword_spotting"


class WakeWordDetector:
    """Wake word detection system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Detection settings
        self.method = WakeWordMethod.PORCUPINE
        self.wake_words = ["hey assistant", "okay assistant", "computer"]
        self.sensitivity = 0.5
        self.timeout = 5.0  # seconds
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.bit_depth = 16
        
        # Detection state
        self.is_detecting = False
        self.detection_callbacks: List[Callable[[str], None]] = []
        self.last_detection_time = 0.0
        self.detection_count = 0
        
        # Models and engines
        self.porcupine_engine = None
        self.snowboy_engine = None
        self.custom_model = None
        
        # Performance tracking
        self.detection_times = []
        self.false_positives = 0
        self.missed_detections = 0
        
        # Initialize detection engine
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the wake word detection engine"""
        try:
            if self.method == WakeWordMethod.PORCUPINE:
                self._init_porcupine()
            elif self.method == WakeWordMethod.SNOWBOY:
                self._init_snowboy()
            elif self.method == WakeWordMethod.CUSTOM_ML:
                self._init_custom_model()
            elif self.method == WakeWordMethod.KEYWORD_SPOTTING:
                self._init_keyword_spotting()
            
            logger.info(f"Wake word detector initialized with method: {self.method.value}")
            
        except Exception as e:
            logger.error(f"Error initializing wake word detector: {e}")
            self.method = WakeWordMethod.KEYWORD_SPOTTING  # Fallback
    
    def _init_porcupine(self):
        """Initialize Porcupine wake word detection"""
        try:
            import pvporcupine
            
            # Create Porcupine instance
            self.porcupine_engine = pvporcupine.create(
                keywords=self.wake_words,
                sensitivities=[self.sensitivity] * len(self.wake_words)
            )
            
            logger.info("Porcupine wake word detector initialized")
            
        except ImportError:
            logger.warning("Porcupine not available. Install with: pip install pvporcupine")
            raise
        except Exception as e:
            logger.error(f"Error initializing Porcupine: {e}")
            raise
    
    def _init_snowboy(self):
        """Initialize Snowboy wake word detection"""
        try:
            import snowboydecoder
            
            # Create Snowboy detector
            model_paths = self._get_snowboy_models()
            self.snowboy_engine = snowboydecoder.HotwordDetector(
                model_paths,
                sensitivity=[self.sensitivity] * len(model_paths)
            )
            
            logger.info("Snowboy wake word detector initialized")
            
        except ImportError:
            logger.warning("Snowboy not available. Install with: pip install snowboy")
            raise
        except Exception as e:
            logger.error(f"Error initializing Snowboy: {e}")
            raise
    
    def _init_custom_model(self):
        """Initialize custom ML model for wake word detection"""
        try:
            # Placeholder for custom model initialization
            # In real implementation, this would load a trained model
            logger.info("Custom ML model initialized (placeholder)")
            
        except Exception as e:
            logger.error(f"Error initializing custom model: {e}")
            raise
    
    def _init_keyword_spotting(self):
        """Initialize keyword spotting fallback"""
        try:
            # Simple keyword spotting using audio analysis
            logger.info("Keyword spotting detector initialized")
            
        except Exception as e:
            logger.error(f"Error initializing keyword spotting: {e}")
            raise
    
    def _get_snowboy_models(self) -> List[str]:
        """Get Snowboy model paths for wake words"""
        # In real implementation, this would return actual model file paths
        # For now, return placeholder paths
        return [f"models/{word.replace(' ', '_')}.pmdl" for word in self.wake_words]
    
    async def start_detection(self, callback: Callable[[str], None]) -> bool:
        """Start wake word detection"""
        try:
            self.detection_callbacks.append(callback)
            self.is_detecting = True
            
            # Start detection loop
            asyncio.create_task(self._detection_loop())
            
            logger.info("Wake word detection started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting wake word detection: {e}")
            return False
    
    async def stop_detection(self) -> bool:
        """Stop wake word detection"""
        try:
            self.is_detecting = False
            self.detection_callbacks.clear()
            
            logger.info("Wake word detection stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping wake word detection: {e}")
            return False
    
    async def _detection_loop(self):
        """Main detection loop"""
        while self.is_detecting:
            try:
                # Get audio chunk (in real implementation, this would come from microphone)
                audio_chunk = await self._get_audio_chunk()
                
                if audio_chunk:
                    # Process audio chunk
                    detected_word = await self._process_audio_chunk(audio_chunk)
                    
                    if detected_word:
                        await self._handle_wake_word_detected(detected_word)
                
                await asyncio.sleep(0.1)  # 100ms intervals
                
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _get_audio_chunk(self) -> Optional[bytes]:
        """Get audio chunk from microphone"""
        # Placeholder for actual audio capture
        # In real implementation, this would capture audio from microphone
        return None
    
    async def _process_audio_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """Process audio chunk for wake word detection"""
        try:
            if self.method == WakeWordMethod.PORCUPINE:
                return await self._detect_with_porcupine(audio_chunk)
            elif self.method == WakeWordMethod.SNOWBOY:
                return await self._detect_with_snowboy(audio_chunk)
            elif self.method == WakeWordMethod.CUSTOM_ML:
                return await self._detect_with_custom_model(audio_chunk)
            elif self.method == WakeWordMethod.KEYWORD_SPOTTING:
                return await self._detect_with_keyword_spotting(audio_chunk)
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    async def _detect_with_porcupine(self, audio_chunk: bytes) -> Optional[str]:
        """Detect wake word using Porcupine"""
        try:
            if not self.porcupine_engine:
                return None
            
            # Convert audio to numpy array
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            
            # Process with Porcupine
            keyword_index = self.porcupine_engine.process(audio_data)
            
            if keyword_index >= 0:
                return self.wake_words[keyword_index]
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Porcupine detection: {e}")
            return None
    
    async def _detect_with_snowboy(self, audio_chunk: bytes) -> Optional[str]:
        """Detect wake word using Snowboy"""
        try:
            if not self.snowboy_engine:
                return None
            
            # Convert audio to numpy array
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            
            # Process with Snowboy
            detection = self.snowboy_engine.detector.RunDetection(audio_data.tobytes())
            
            if detection > 0:
                return self.wake_words[detection - 1]
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Snowboy detection: {e}")
            return None
    
    async def _detect_with_custom_model(self, audio_chunk: bytes) -> Optional[str]:
        """Detect wake word using custom ML model"""
        try:
            # Placeholder for custom model inference
            # In real implementation, this would run inference on the model
            return None
            
        except Exception as e:
            logger.error(f"Error in custom model detection: {e}")
            return None
    
    async def _detect_with_keyword_spotting(self, audio_chunk: bytes) -> Optional[str]:
        """Detect wake word using keyword spotting"""
        try:
            # Simple keyword spotting implementation
            # In real implementation, this would use audio analysis techniques
            
            # Convert audio to numpy array
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            
            # Simple energy-based detection
            energy = np.mean(np.abs(audio_data))
            
            if energy > 1000:  # Threshold for speech detection
                # Placeholder for actual keyword recognition
                return "hey assistant"  # Simplified detection
            
            return None
            
        except Exception as e:
            logger.error(f"Error in keyword spotting: {e}")
            return None
    
    async def _handle_wake_word_detected(self, wake_word: str):
        """Handle wake word detection"""
        try:
            current_time = asyncio.get_event_loop().time()
            
            # Prevent duplicate detections within timeout period
            if current_time - self.last_detection_time < self.timeout:
                return
            
            self.last_detection_time = current_time
            self.detection_count += 1
            
            # Track detection time
            self.detection_times.append(current_time)
            
            # Keep only recent detection times
            if len(self.detection_times) > 100:
                self.detection_times = self.detection_times[-100:]
            
            logger.info(f"Wake word detected: {wake_word}")
            
            # Notify callbacks
            for callback in self.detection_callbacks:
                try:
                    callback(wake_word)
                except Exception as e:
                    logger.error(f"Error in wake word callback: {e}")
            
        except Exception as e:
            logger.error(f"Error handling wake word detection: {e}")
    
    def set_wake_words(self, wake_words: List[str]):
        """Set wake words for detection"""
        self.wake_words = wake_words
        logger.info(f"Wake words updated: {wake_words}")
    
    def set_sensitivity(self, sensitivity: float):
        """Set detection sensitivity (0.0 to 1.0)"""
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        logger.info(f"Detection sensitivity set to {self.sensitivity}")
    
    def set_timeout(self, timeout: float):
        """Set detection timeout in seconds"""
        self.timeout = timeout
        logger.info(f"Detection timeout set to {timeout}s")
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return {
            "method": self.method.value,
            "wake_words": self.wake_words,
            "sensitivity": self.sensitivity,
            "timeout": self.timeout,
            "is_detecting": self.is_detecting,
            "detection_count": self.detection_count,
            "false_positives": self.false_positives,
            "missed_detections": self.missed_detections,
            "recent_detections": len(self.detection_times)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.porcupine_engine:
                self.porcupine_engine.delete()
                self.porcupine_engine = None
            
            if self.snowboy_engine:
                self.snowboy_engine.terminate()
                self.snowboy_engine = None
            
            logger.info("Wake word detector cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up wake word detector: {e}")
