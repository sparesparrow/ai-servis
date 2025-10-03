"""
Audio Format Conversion and Routing
Handles audio format conversion, resampling, and routing
"""
import asyncio
import logging
import numpy as np
import soundfile as sf
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import tempfile
import os
from datetime import datetime
import uuid

from audio_models import AudioFormat, AudioDevice, AudioDeviceType

logger = logging.getLogger(__name__)


class AudioConverter:
    """Audio format conversion and processing"""
    
    def __init__(self):
        self.supported_formats = {
            AudioFormat.MP3: {"read": True, "write": True},
            AudioFormat.WAV: {"read": True, "write": True},
            AudioFormat.FLAC: {"read": True, "write": True},
            AudioFormat.AAC: {"read": True, "write": False},
            AudioFormat.OGG: {"read": True, "write": True},
            AudioFormat.M4A: {"read": True, "write": False},
            AudioFormat.WMA: {"read": False, "write": False}
        }
        
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_audio_converter"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Conversion cache
        self.conversion_cache: Dict[str, str] = {}
        self.cache_max_size = 100
        self.cache_ttl = 3600  # 1 hour
    
    async def convert_audio(self, input_path: str, output_format: AudioFormat, 
                          output_path: Optional[str] = None, 
                          sample_rate: Optional[int] = None,
                          channels: Optional[int] = None,
                          bit_depth: Optional[int] = None) -> str:
        """Convert audio file to different format"""
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Determine output path
            if not output_path:
                output_path = self.temp_dir / f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format.value}"
            else:
                output_path = Path(output_path)
            
            # Check if conversion is supported
            input_format = self._detect_format(input_path)
            if not self._can_convert(input_format, output_format):
                raise ValueError(f"Conversion from {input_format} to {output_format} not supported")
            
            # Check cache first
            cache_key = self._get_cache_key(input_path, output_format, sample_rate, channels, bit_depth)
            if cache_key in self.conversion_cache:
                cached_path = self.conversion_cache[cache_key]
                if Path(cached_path).exists():
                    logger.info(f"Using cached conversion: {cached_path}")
                    return str(cached_path)
            
            # Perform conversion
            logger.info(f"Converting {input_path} to {output_format}")
            
            # Read input file
            audio_data, input_sr = sf.read(str(input_path))
            
            # Apply format conversion
            converted_data = await self._convert_audio_data(
                audio_data, input_sr, output_format, sample_rate, channels, bit_depth
            )
            
            # Write output file
            output_sr = sample_rate or input_sr
            sf.write(str(output_path), converted_data, output_sr)
            
            # Cache the result
            self.conversion_cache[cache_key] = str(output_path)
            self._cleanup_cache()
            
            logger.info(f"Conversion completed: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            raise
    
    async def resample_audio(self, audio_data: np.ndarray, input_sr: int, 
                           output_sr: int) -> np.ndarray:
        """Resample audio data"""
        try:
            if input_sr == output_sr:
                return audio_data
            
            # Simple resampling using numpy (for basic cases)
            # In production, you'd want to use librosa or scipy.signal.resample
            ratio = output_sr / input_sr
            new_length = int(len(audio_data) * ratio)
            
            if ratio > 1:  # Upsampling
                # Linear interpolation
                indices = np.linspace(0, len(audio_data) - 1, new_length)
                resampled = np.interp(indices, np.arange(len(audio_data)), audio_data)
            else:  # Downsampling
                # Simple decimation
                step = int(1 / ratio)
                resampled = audio_data[::step]
            
            return resampled.astype(audio_data.dtype)
            
        except Exception as e:
            logger.error(f"Error resampling audio: {e}")
            raise
    
    async def convert_channels(self, audio_data: np.ndarray, input_channels: int, 
                             output_channels: int) -> np.ndarray:
        """Convert audio channels (mono/stereo)"""
        try:
            if input_channels == output_channels:
                return audio_data
            
            if len(audio_data.shape) == 1:
                # Mono input
                if output_channels == 2:
                    # Mono to stereo
                    return np.column_stack([audio_data, audio_data])
                else:
                    return audio_data
            else:
                # Multi-channel input
                if output_channels == 1:
                    # Stereo to mono (average channels)
                    return np.mean(audio_data, axis=1)
                elif output_channels == 2 and audio_data.shape[1] > 2:
                    # Multi-channel to stereo (take first two channels)
                    return audio_data[:, :2]
                else:
                    return audio_data
            
        except Exception as e:
            logger.error(f"Error converting channels: {e}")
            raise
    
    async def normalize_audio(self, audio_data: np.ndarray, target_level: float = 0.8) -> np.ndarray:
        """Normalize audio to target level"""
        try:
            if len(audio_data) == 0:
                return audio_data
            
            # Calculate current peak level
            peak = np.max(np.abs(audio_data))
            if peak == 0:
                return audio_data
            
            # Calculate normalization factor
            norm_factor = target_level / peak
            
            # Apply normalization
            normalized = audio_data * norm_factor
            
            # Ensure we don't clip
            if np.max(np.abs(normalized)) > 1.0:
                normalized = normalized / np.max(np.abs(normalized))
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            raise
    
    async def apply_fade(self, audio_data: np.ndarray, sample_rate: int, 
                        fade_in_duration: float = 0.0, fade_out_duration: float = 0.0) -> np.ndarray:
        """Apply fade in/out to audio data"""
        try:
            if len(audio_data) == 0:
                return audio_data
            
            result = audio_data.copy()
            
            # Fade in
            if fade_in_duration > 0:
                fade_in_samples = int(fade_in_duration * sample_rate)
                fade_in_samples = min(fade_in_samples, len(result))
                
                if len(result.shape) == 1:
                    # Mono
                    fade_curve = np.linspace(0, 1, fade_in_samples)
                    result[:fade_in_samples] *= fade_curve
                else:
                    # Multi-channel
                    fade_curve = np.linspace(0, 1, fade_in_samples)
                    result[:fade_in_samples] *= fade_curve[:, np.newaxis]
            
            # Fade out
            if fade_out_duration > 0:
                fade_out_samples = int(fade_out_duration * sample_rate)
                fade_out_samples = min(fade_out_samples, len(result))
                
                if len(result.shape) == 1:
                    # Mono
                    fade_curve = np.linspace(1, 0, fade_out_samples)
                    result[-fade_out_samples:] *= fade_curve
                else:
                    # Multi-channel
                    fade_curve = np.linspace(1, 0, fade_out_samples)
                    result[-fade_out_samples:] *= fade_curve[:, np.newaxis]
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying fade: {e}")
            raise
    
    async def crossfade_audio(self, audio1: np.ndarray, audio2: np.ndarray, 
                            sample_rate: int, crossfade_duration: float = 2.0) -> np.ndarray:
        """Create crossfade between two audio segments"""
        try:
            crossfade_samples = int(crossfade_duration * sample_rate)
            
            if len(audio1) < crossfade_samples or len(audio2) < crossfade_samples:
                # Not enough samples for crossfade, just concatenate
                return np.concatenate([audio1, audio2])
            
            # Create crossfade
            fade_out = np.linspace(1, 0, crossfade_samples)
            fade_in = np.linspace(0, 1, crossfade_samples)
            
            if len(audio1.shape) == 1:
                # Mono
                crossfade = (audio1[-crossfade_samples:] * fade_out + 
                           audio2[:crossfade_samples] * fade_in)
            else:
                # Multi-channel
                crossfade = (audio1[-crossfade_samples:] * fade_out[:, np.newaxis] + 
                           audio2[:crossfade_samples] * fade_in[:, np.newaxis])
            
            # Combine audio
            result = np.concatenate([
                audio1[:-crossfade_samples],
                crossfade,
                audio2[crossfade_samples:]
            ])
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating crossfade: {e}")
            raise
    
    def _detect_format(self, file_path: Path) -> AudioFormat:
        """Detect audio format from file extension"""
        extension = file_path.suffix.lower().lstrip('.')
        
        format_map = {
            'mp3': AudioFormat.MP3,
            'wav': AudioFormat.WAV,
            'flac': AudioFormat.FLAC,
            'aac': AudioFormat.AAC,
            'ogg': AudioFormat.OGG,
            'm4a': AudioFormat.M4A,
            'wma': AudioFormat.WMA
        }
        
        return format_map.get(extension, AudioFormat.WAV)
    
    def _can_convert(self, input_format: AudioFormat, output_format: AudioFormat) -> bool:
        """Check if conversion is supported"""
        input_support = self.supported_formats.get(input_format, {"read": False, "write": False})
        output_support = self.supported_formats.get(output_format, {"read": False, "write": False})
        
        return input_support["read"] and output_support["write"]
    
    def _get_cache_key(self, input_path: Path, output_format: AudioFormat, 
                      sample_rate: Optional[int], channels: Optional[int], 
                      bit_depth: Optional[int]) -> str:
        """Generate cache key for conversion"""
        stat = input_path.stat()
        key_parts = [
            str(input_path),
            str(stat.st_mtime),
            str(stat.st_size),
            output_format.value,
            str(sample_rate or ""),
            str(channels or ""),
            str(bit_depth or "")
        ]
        return "|".join(key_parts)
    
    async def _convert_audio_data(self, audio_data: np.ndarray, input_sr: int, 
                                output_format: AudioFormat, sample_rate: Optional[int],
                                channels: Optional[int], bit_depth: Optional[int]) -> np.ndarray:
        """Convert audio data format"""
        try:
            result = audio_data.copy()
            
            # Resample if needed
            if sample_rate and sample_rate != input_sr:
                result = await self.resample_audio(result, input_sr, sample_rate)
            
            # Convert channels if needed
            if channels:
                input_channels = 1 if len(result.shape) == 1 else result.shape[1]
                if channels != input_channels:
                    result = await self.convert_channels(result, input_channels, channels)
            
            # Convert bit depth if needed
            if bit_depth:
                if bit_depth == 16:
                    result = (result * 32767).astype(np.int16)
                elif bit_depth == 24:
                    result = (result * 8388607).astype(np.int32)
                elif bit_depth == 32:
                    result = (result * 2147483647).astype(np.int32)
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting audio data: {e}")
            raise
    
    def _cleanup_cache(self):
        """Clean up old cache entries"""
        try:
            if len(self.conversion_cache) > self.cache_max_size:
                # Remove oldest entries
                cache_items = list(self.conversion_cache.items())
                cache_items.sort(key=lambda x: Path(x[1]).stat().st_mtime if Path(x[1]).exists() else 0)
                
                # Remove oldest half
                for key, path in cache_items[:len(cache_items)//2]:
                    if Path(path).exists():
                        Path(path).unlink()
                    del self.conversion_cache[key]
            
            # Remove expired cache entries
            current_time = datetime.now().timestamp()
            expired_keys = []
            
            for key, path in self.conversion_cache.items():
                if Path(path).exists():
                    file_time = Path(path).stat().st_mtime
                    if current_time - file_time > self.cache_ttl:
                        Path(path).unlink()
                        expired_keys.append(key)
                else:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.conversion_cache[key]
                
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    async def get_supported_formats(self) -> Dict[str, Dict[str, bool]]:
        """Get supported audio formats"""
        return {format.value: support for format, support in self.supported_formats.items()}
    
    async def get_conversion_info(self, input_path: str) -> Dict[str, Any]:
        """Get information about audio file"""
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"File not found: {input_path}")
            
            # Read audio file info
            info = sf.info(str(input_path))
            
            return {
                "format": self._detect_format(input_path).value,
                "sample_rate": info.samplerate,
                "channels": info.channels,
                "duration": info.duration,
                "frames": info.frames,
                "file_size": input_path.stat().st_size,
                "bit_depth": info.subtype
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion info: {e}")
            raise
    
    async def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            
            # Clear cache
            self.conversion_cache.clear()
            
            logger.info("Temporary files cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")


class AudioRouter:
    """Audio routing and device management"""
    
    def __init__(self):
        self.routes: Dict[str, List[str]] = {}  # source -> [destinations]
        self.device_capabilities: Dict[str, Dict[str, Any]] = {}
        self.active_routes: Dict[str, str] = {}  # session_id -> route_id
    
    async def create_route(self, route_id: str, source: str, destinations: List[str]) -> bool:
        """Create audio route"""
        try:
            self.routes[route_id] = {
                "source": source,
                "destinations": destinations,
                "created_at": datetime.now(),
                "active": False
            }
            
            logger.info(f"Created audio route: {route_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating route: {e}")
            return False
    
    async def activate_route(self, route_id: str, session_id: str) -> bool:
        """Activate audio route"""
        try:
            if route_id not in self.routes:
                return False
            
            # Deactivate existing route for session
            if session_id in self.active_routes:
                await self.deactivate_route(self.active_routes[session_id], session_id)
            
            # Activate new route
            self.routes[route_id]["active"] = True
            self.active_routes[session_id] = route_id
            
            logger.info(f"Activated route {route_id} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating route: {e}")
            return False
    
    async def deactivate_route(self, route_id: str, session_id: str) -> bool:
        """Deactivate audio route"""
        try:
            if route_id in self.routes:
                self.routes[route_id]["active"] = False
            
            if session_id in self.active_routes:
                del self.active_routes[session_id]
            
            logger.info(f"Deactivated route {route_id} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating route: {e}")
            return False
    
    async def get_route_info(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Get route information"""
        return self.routes.get(route_id)
    
    async def list_routes(self) -> Dict[str, Dict[str, Any]]:
        """List all routes"""
        return self.routes.copy()
    
    async def delete_route(self, route_id: str) -> bool:
        """Delete audio route"""
        try:
            if route_id in self.routes:
                del self.routes[route_id]
                
                # Remove from active routes
                for session_id, active_route in list(self.active_routes.items()):
                    if active_route == route_id:
                        del self.active_routes[session_id]
                
                logger.info(f"Deleted route: {route_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting route: {e}")
            return False
    
    async def set_device_capabilities(self, device_id: str, capabilities: Dict[str, Any]):
        """Set device capabilities"""
        self.device_capabilities[device_id] = capabilities
    
    async def get_device_capabilities(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device capabilities"""
        return self.device_capabilities.get(device_id)
    
    async def find_compatible_devices(self, requirements: Dict[str, Any]) -> List[str]:
        """Find devices compatible with requirements"""
        compatible_devices = []
        
        for device_id, capabilities in self.device_capabilities.items():
            compatible = True
            
            # Check sample rate
            if "sample_rate" in requirements:
                if capabilities.get("max_sample_rate", 0) < requirements["sample_rate"]:
                    compatible = False
            
            # Check channels
            if "channels" in requirements:
                if capabilities.get("max_channels", 0) < requirements["channels"]:
                    compatible = False
            
            # Check format support
            if "formats" in requirements:
                device_formats = capabilities.get("supported_formats", [])
                if not any(fmt in device_formats for fmt in requirements["formats"]):
                    compatible = False
            
            if compatible:
                compatible_devices.append(device_id)
        
        return compatible_devices
