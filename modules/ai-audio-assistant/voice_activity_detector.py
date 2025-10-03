"""
Voice Activity Detection for Audio Assistant
Handles voice activity detection and audio analysis
"""
import asyncio
import logging
import numpy as np
import struct
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import collections

logger = logging.getLogger(__name__)


class VADState(Enum):
    """Voice activity detection states"""
    SILENT = "silent"
    SPEECH = "speech"
    NOISE = "noise"
    UNKNOWN = "unknown"


class VADMethod(Enum):
    """Voice activity detection methods"""
    ENERGY_BASED = "energy_based"
    SPECTRAL_BASED = "spectral_based"
    ML_BASED = "ml_based"
    WEBRTC = "webrtc"


class VoiceActivityDetector:
    """Voice activity detection system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Detection settings
        self.method = VADMethod.ENERGY_BASED
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.bit_depth = 16
        
        # Thresholds and parameters
        self.energy_threshold = 0.01
        self.spectral_threshold = 0.5
        self.silence_duration_threshold = 1.0  # seconds
        self.speech_duration_threshold = 0.1   # seconds
        
        # State tracking
        self.current_state = VADState.SILENT
        self.previous_state = VADState.SILENT
        self.state_duration = 0.0
        self.silence_duration = 0.0
        self.speech_duration = 0.0
        
        # Audio analysis
        self.energy_history = collections.deque(maxlen=100)
        self.spectral_history = collections.deque(maxlen=100)
        self.zero_crossing_history = collections.deque(maxlen=100)
        
        # Callbacks
        self.state_change_callbacks: List[Callable[[VADState, VADState], None]] = []
        self.speech_start_callbacks: List[Callable[[], None]] = []
        self.speech_end_callbacks: List[Callable[[], None]] = []
        
        # Performance tracking
        self.detection_times = []
        self.false_positives = 0
        self.missed_detections = 0
        
        # Initialize detector
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize the voice activity detector"""
        try:
            if self.method == VADMethod.WEBRTC:
                self._init_webrtc_vad()
            elif self.method == VADMethod.ML_BASED:
                self._init_ml_vad()
            
            logger.info(f"Voice activity detector initialized with method: {self.method.value}")
            
        except Exception as e:
            logger.error(f"Error initializing VAD: {e}")
            self.method = VADMethod.ENERGY_BASED  # Fallback
    
    def _init_webrtc_vad(self):
        """Initialize WebRTC VAD"""
        try:
            import webrtcvad
            
            # Create WebRTC VAD instance
            self.webrtc_vad = webrtcvad.Vad()
            self.webrtc_vad.set_mode(2)  # Aggressiveness level 0-3
            
            logger.info("WebRTC VAD initialized")
            
        except ImportError:
            logger.warning("WebRTC VAD not available. Install with: pip install webrtcvad")
            raise
        except Exception as e:
            logger.error(f"Error initializing WebRTC VAD: {e}")
            raise
    
    def _init_ml_vad(self):
        """Initialize ML-based VAD"""
        try:
            # Placeholder for ML model initialization
            # In real implementation, this would load a trained model
            logger.info("ML-based VAD initialized (placeholder)")
            
        except Exception as e:
            logger.error(f"Error initializing ML VAD: {e}")
            raise
    
    async def process_audio_chunk(self, audio_chunk: bytes) -> VADState:
        """Process audio chunk and return VAD state"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Convert audio to numpy array
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            
            # Detect voice activity based on method
            if self.method == VADMethod.WEBRTC:
                new_state = await self._detect_with_webrtc(audio_chunk)
            elif self.method == VADMethod.ML_BASED:
                new_state = await self._detect_with_ml(audio_data)
            elif self.method == VADMethod.SPECTRAL_BASED:
                new_state = await self._detect_with_spectral(audio_data)
            else:  # ENERGY_BASED
                new_state = await self._detect_with_energy(audio_data)
            
            # Update state if changed
            if new_state != self.current_state:
                await self._update_state(new_state)
            
            # Track processing time
            processing_time = asyncio.get_event_loop().time() - start_time
            self.detection_times.append(processing_time)
            
            # Keep only recent processing times
            if len(self.detection_times) > 100:
                self.detection_times = self.detection_times[-100:]
            
            return self.current_state
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return self.current_state
    
    async def _detect_with_webrtc(self, audio_chunk: bytes) -> VADState:
        """Detect voice activity using WebRTC VAD"""
        try:
            if not hasattr(self, 'webrtc_vad'):
                return VADState.UNKNOWN
            
            # WebRTC VAD expects specific frame sizes
            frame_size = 160  # 10ms at 16kHz
            if len(audio_chunk) < frame_size * 2:  # 2 bytes per sample
                return VADState.UNKNOWN
            
            # Process audio chunk
            is_speech = self.webrtc_vad.is_speech(audio_chunk, self.sample_rate)
            
            return VADState.SPEECH if is_speech else VADState.SILENT
            
        except Exception as e:
            logger.error(f"Error in WebRTC VAD: {e}")
            return VADState.UNKNOWN
    
    async def _detect_with_ml(self, audio_data: np.ndarray) -> VADState:
        """Detect voice activity using ML model"""
        try:
            # Placeholder for ML model inference
            # In real implementation, this would extract features and run inference
            
            # Simple fallback to energy-based detection
            energy = np.mean(np.abs(audio_data))
            
            if energy > self.energy_threshold * 1000:
                return VADState.SPEECH
            else:
                return VADState.SILENT
            
        except Exception as e:
            logger.error(f"Error in ML VAD: {e}")
            return VADState.UNKNOWN
    
    async def _detect_with_spectral(self, audio_data: np.ndarray) -> VADState:
        """Detect voice activity using spectral analysis"""
        try:
            # Calculate spectral features
            fft = np.fft.fft(audio_data)
            magnitude = np.abs(fft)
            
            # Calculate spectral centroid
            freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
            spectral_centroid = np.sum(freqs[:len(freqs)//2] * magnitude[:len(magnitude)//2]) / np.sum(magnitude[:len(magnitude)//2])
            
            # Calculate spectral rolloff
            cumulative_magnitude = np.cumsum(magnitude[:len(magnitude)//2])
            total_energy = cumulative_magnitude[-1]
            rolloff_threshold = 0.85 * total_energy
            spectral_rolloff = np.where(cumulative_magnitude >= rolloff_threshold)[0]
            spectral_rolloff = spectral_rolloff[0] if len(spectral_rolloff) > 0 else len(magnitude)//2
            
            # Calculate zero crossing rate
            zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
            zcr = zero_crossings / len(audio_data)
            
            # Update history
            self.spectral_history.append(spectral_centroid)
            self.zero_crossing_history.append(zcr)
            
            # Determine state based on spectral features
            if (spectral_centroid > 1000 and  # Typical speech spectral centroid
                zcr > 0.1 and  # Typical speech zero crossing rate
                spectral_rolloff > 1000):  # Typical speech spectral rolloff
                return VADState.SPEECH
            else:
                return VADState.SILENT
            
        except Exception as e:
            logger.error(f"Error in spectral VAD: {e}")
            return VADState.UNKNOWN
    
    async def _detect_with_energy(self, audio_data: np.ndarray) -> VADState:
        """Detect voice activity using energy-based method"""
        try:
            # Calculate RMS energy
            energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            
            # Update energy history
            self.energy_history.append(energy)
            
            # Calculate energy threshold dynamically
            if len(self.energy_history) > 10:
                energy_mean = np.mean(list(self.energy_history))
                energy_std = np.std(list(self.energy_history))
                dynamic_threshold = energy_mean + 2 * energy_std
            else:
                dynamic_threshold = self.energy_threshold
            
            # Determine state based on energy
            if energy > dynamic_threshold:
                return VADState.SPEECH
            else:
                return VADState.SILENT
            
        except Exception as e:
            logger.error(f"Error in energy VAD: {e}")
            return VADState.UNKNOWN
    
    async def _update_state(self, new_state: VADState):
        """Update VAD state and handle transitions"""
        try:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_duration = 0.0
            
            # Handle state transitions
            if self.previous_state == VADState.SILENT and new_state == VADState.SPEECH:
                # Speech started
                await self._handle_speech_start()
            elif self.previous_state == VADState.SPEECH and new_state == VADState.SILENT:
                # Speech ended
                await self._handle_speech_end()
            
            # Notify state change callbacks
            for callback in self.state_change_callbacks:
                try:
                    callback(self.previous_state, new_state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")
            
            logger.debug(f"VAD state changed: {self.previous_state.value} -> {new_state.value}")
            
        except Exception as e:
            logger.error(f"Error updating VAD state: {e}")
    
    async def _handle_speech_start(self):
        """Handle speech start event"""
        try:
            self.speech_duration = 0.0
            
            # Notify speech start callbacks
            for callback in self.speech_start_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in speech start callback: {e}")
            
            logger.debug("Speech started")
            
        except Exception as e:
            logger.error(f"Error handling speech start: {e}")
    
    async def _handle_speech_end(self):
        """Handle speech end event"""
        try:
            self.silence_duration = 0.0
            
            # Notify speech end callbacks
            for callback in self.speech_end_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in speech end callback: {e}")
            
            logger.debug("Speech ended")
            
        except Exception as e:
            logger.error(f"Error handling speech end: {e}")
    
    def add_state_change_callback(self, callback: Callable[[VADState, VADState], None]):
        """Add callback for state changes"""
        self.state_change_callbacks.append(callback)
    
    def add_speech_start_callback(self, callback: Callable[[], None]):
        """Add callback for speech start"""
        self.speech_start_callbacks.append(callback)
    
    def add_speech_end_callback(self, callback: Callable[[], None]):
        """Add callback for speech end"""
        self.speech_end_callbacks.append(callback)
    
    def set_energy_threshold(self, threshold: float):
        """Set energy threshold for detection"""
        self.energy_threshold = threshold
        logger.info(f"Energy threshold set to {threshold}")
    
    def set_spectral_threshold(self, threshold: float):
        """Set spectral threshold for detection"""
        self.spectral_threshold = threshold
        logger.info(f"Spectral threshold set to {threshold}")
    
    def set_duration_thresholds(self, silence_duration: float, speech_duration: float):
        """Set duration thresholds for state transitions"""
        self.silence_duration_threshold = silence_duration
        self.speech_duration_threshold = speech_duration
        logger.info(f"Duration thresholds set: silence={silence_duration}s, speech={speech_duration}s")
    
    def get_current_state(self) -> VADState:
        """Get current VAD state"""
        return self.current_state
    
    def get_state_duration(self) -> float:
        """Get duration of current state"""
        return self.state_duration
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get VAD detection statistics"""
        avg_processing_time = (
            sum(self.detection_times) / len(self.detection_times)
            if self.detection_times else 0.0
        )
        
        return {
            "method": self.method.value,
            "current_state": self.current_state.value,
            "state_duration": self.state_duration,
            "energy_threshold": self.energy_threshold,
            "spectral_threshold": self.spectral_threshold,
            "energy_history_size": len(self.energy_history),
            "spectral_history_size": len(self.spectral_history),
            "zero_crossing_history_size": len(self.zero_crossing_history),
            "false_positives": self.false_positives,
            "missed_detections": self.missed_detections,
            "avg_processing_time": avg_processing_time
        }
    
    def reset(self):
        """Reset VAD state and history"""
        self.current_state = VADState.SILENT
        self.previous_state = VADState.SILENT
        self.state_duration = 0.0
        self.silence_duration = 0.0
        self.speech_duration = 0.0
        
        self.energy_history.clear()
        self.spectral_history.clear()
        self.zero_crossing_history.clear()
        
        logger.info("VAD state reset")
