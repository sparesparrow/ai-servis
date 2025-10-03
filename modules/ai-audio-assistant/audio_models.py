"""
Audio Assistant Models and Interfaces
"""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from pydantic import BaseModel, Field, validator
import asyncio
import uuid


class AudioDeviceType(str, Enum):
    """Audio device types"""
    SPEAKERS = "speakers"
    HEADPHONES = "headphones"
    BLUETOOTH = "bluetooth"
    USB = "usb"
    HDMI = "hdmi"
    ANALOG = "analog"
    DIGITAL = "digital"


class AudioFormat(str, Enum):
    """Audio format types"""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"
    M4A = "m4a"
    WMA = "wma"


class PlaybackState(str, Enum):
    """Playback states"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class AudioSource(str, Enum):
    """Audio sources"""
    LOCAL = "local"
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    APPLE_MUSIC = "apple_music"
    SOUNDCLOUD = "soundcloud"
    RADIO = "radio"
    PODCAST = "podcast"


class AudioDevice(BaseModel):
    """Audio device information"""
    id: str = Field(..., description="Device ID")
    name: str = Field(..., description="Device name")
    type: AudioDeviceType = Field(..., description="Device type")
    is_default: bool = Field(default=False, description="Is default device")
    is_available: bool = Field(default=True, description="Is device available")
    sample_rate: int = Field(default=44100, description="Sample rate")
    channels: int = Field(default=2, description="Number of channels")
    bit_depth: int = Field(default=16, description="Bit depth")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Device volume")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Device properties")


class AudioTrack(BaseModel):
    """Audio track information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Track ID")
    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    duration: float = Field(..., description="Duration in seconds")
    source: AudioSource = Field(..., description="Audio source")
    format: AudioFormat = Field(..., description="Audio format")
    url: Optional[str] = Field(None, description="Track URL")
    file_path: Optional[str] = Field(None, description="Local file path")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Track metadata")
    artwork_url: Optional[str] = Field(None, description="Artwork URL")
    genre: Optional[str] = Field(None, description="Genre")
    year: Optional[int] = Field(None, description="Release year")
    bitrate: Optional[int] = Field(None, description="Bitrate")
    sample_rate: Optional[int] = Field(None, description="Sample rate")


class Playlist(BaseModel):
    """Playlist information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Playlist ID")
    name: str = Field(..., description="Playlist name")
    description: Optional[str] = Field(None, description="Playlist description")
    tracks: List[AudioTrack] = Field(default_factory=list, description="Playlist tracks")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    is_public: bool = Field(default=False, description="Is playlist public")
    owner_id: Optional[str] = Field(None, description="Playlist owner ID")
    source: AudioSource = Field(..., description="Playlist source")


class AudioZone(BaseModel):
    """Audio zone for multi-room audio"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Zone ID")
    name: str = Field(..., description="Zone name")
    devices: List[AudioDevice] = Field(default_factory=list, description="Zone devices")
    volume: float = Field(default=0.5, ge=0.0, le=1.0, description="Zone volume")
    is_muted: bool = Field(default=False, description="Is zone muted")
    is_active: bool = Field(default=False, description="Is zone active")
    current_track: Optional[AudioTrack] = Field(None, description="Current track")
    playback_state: PlaybackState = Field(default=PlaybackState.STOPPED, description="Playback state")
    position: float = Field(default=0.0, description="Current position in seconds")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")


class AudioSession(BaseModel):
    """Audio playback session"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    zone_id: str = Field(..., description="Zone ID")
    playlist: Optional[Playlist] = Field(None, description="Current playlist")
    current_track: Optional[AudioTrack] = Field(None, description="Current track")
    playback_state: PlaybackState = Field(default=PlaybackState.STOPPED, description="Playback state")
    position: float = Field(default=0.0, description="Current position in seconds")
    volume: float = Field(default=0.5, ge=0.0, le=1.0, description="Session volume")
    is_shuffle: bool = Field(default=False, description="Shuffle mode")
    repeat_mode: str = Field(default="none", description="Repeat mode (none, one, all)")
    created_at: datetime = Field(default_factory=datetime.now, description="Session start time")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity time")


class AudioCommand(BaseModel):
    """Audio control command"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Command ID")
    action: str = Field(..., description="Command action")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    zone_id: Optional[str] = Field(None, description="Target zone ID")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Command timestamp")
    priority: int = Field(default=1, description="Command priority")


class AudioResponse(BaseModel):
    """Audio command response"""
    command_id: str = Field(..., description="Command ID")
    success: bool = Field(..., description="Command success")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class AudioConfig(BaseModel):
    """Audio system configuration"""
    default_device: Optional[str] = Field(None, description="Default audio device")
    default_volume: float = Field(default=0.5, ge=0.0, le=1.0, description="Default volume")
    max_volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Maximum volume")
    buffer_size: int = Field(default=4096, description="Audio buffer size")
    sample_rate: int = Field(default=44100, description="Default sample rate")
    channels: int = Field(default=2, description="Default channels")
    bit_depth: int = Field(default=16, description="Default bit depth")
    crossfade_duration: float = Field(default=2.0, description="Crossfade duration in seconds")
    fade_in_duration: float = Field(default=1.0, description="Fade in duration in seconds")
    fade_out_duration: float = Field(default=1.0, description="Fade out duration in seconds")
    auto_play: bool = Field(default=True, description="Auto-play next track")
    gapless_playback: bool = Field(default=True, description="Enable gapless playback")
    equalizer_enabled: bool = Field(default=False, description="Enable equalizer")
    equalizer_presets: Dict[str, List[float]] = Field(default_factory=dict, description="Equalizer presets")
    spotify_client_id: Optional[str] = Field(None, description="Spotify client ID")
    spotify_client_secret: Optional[str] = Field(None, description="Spotify client secret")
    youtube_api_key: Optional[str] = Field(None, description="YouTube API key")


class AudioStats(BaseModel):
    """Audio system statistics"""
    total_tracks_played: int = Field(default=0, description="Total tracks played")
    total_play_time: float = Field(default=0.0, description="Total play time in seconds")
    current_session_time: float = Field(default=0.0, description="Current session time")
    active_zones: int = Field(default=0, description="Number of active zones")
    active_sessions: int = Field(default=0, description="Number of active sessions")
    available_devices: int = Field(default=0, description="Number of available devices")
    memory_usage: float = Field(default=0.0, description="Memory usage in MB")
    cpu_usage: float = Field(default=0.0, description="CPU usage percentage")
    network_usage: float = Field(default=0.0, description="Network usage in MB/s")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")


class AudioEngine(ABC):
    """Abstract audio engine interface"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the audio engine"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the audio engine"""
        pass
    
    @abstractmethod
    async def get_devices(self) -> List[AudioDevice]:
        """Get available audio devices"""
        pass
    
    @abstractmethod
    async def set_default_device(self, device_id: str) -> bool:
        """Set default audio device"""
        pass
    
    @abstractmethod
    async def get_volume(self, device_id: Optional[str] = None) -> float:
        """Get device volume"""
        pass
    
    @abstractmethod
    async def set_volume(self, volume: float, device_id: Optional[str] = None) -> bool:
        """Set device volume"""
        pass
    
    @abstractmethod
    async def mute(self, device_id: Optional[str] = None) -> bool:
        """Mute device"""
        pass
    
    @abstractmethod
    async def unmute(self, device_id: Optional[str] = None) -> bool:
        """Unmute device"""
        pass


class MusicPlayer(ABC):
    """Abstract music player interface"""
    
    @abstractmethod
    async def play(self, track: AudioTrack, zone_id: str) -> AudioResponse:
        """Play a track"""
        pass
    
    @abstractmethod
    async def pause(self, zone_id: str) -> AudioResponse:
        """Pause playback"""
        pass
    
    @abstractmethod
    async def resume(self, zone_id: str) -> AudioResponse:
        """Resume playback"""
        pass
    
    @abstractmethod
    async def stop(self, zone_id: str) -> AudioResponse:
        """Stop playback"""
        pass
    
    @abstractmethod
    async def next_track(self, zone_id: str) -> AudioResponse:
        """Play next track"""
        pass
    
    @abstractmethod
    async def previous_track(self, zone_id: str) -> AudioResponse:
        """Play previous track"""
        pass
    
    @abstractmethod
    async def seek(self, position: float, zone_id: str) -> AudioResponse:
        """Seek to position"""
        pass
    
    @abstractmethod
    async def set_volume(self, volume: float, zone_id: str) -> AudioResponse:
        """Set zone volume"""
        pass
    
    @abstractmethod
    async def get_status(self, zone_id: str) -> AudioResponse:
        """Get playback status"""
        pass


class AudioService(ABC):
    """Abstract audio service interface"""
    
    @abstractmethod
    async def search_tracks(self, query: str, source: AudioSource) -> List[AudioTrack]:
        """Search for tracks"""
        pass
    
    @abstractmethod
    async def get_track_info(self, track_id: str, source: AudioSource) -> Optional[AudioTrack]:
        """Get track information"""
        pass
    
    @abstractmethod
    async def get_playlist(self, playlist_id: str, source: AudioSource) -> Optional[Playlist]:
        """Get playlist"""
        pass
    
    @abstractmethod
    async def create_playlist(self, name: str, tracks: List[AudioTrack], source: AudioSource) -> Optional[Playlist]:
        """Create playlist"""
        pass
    
    @abstractmethod
    async def authenticate(self, source: AudioSource, credentials: Dict[str, str]) -> bool:
        """Authenticate with service"""
        pass


class VoiceProcessor(ABC):
    """Abstract voice processor interface"""
    
    @abstractmethod
    async def start_listening(self, callback: Callable[[str], None]) -> bool:
        """Start voice recognition"""
        pass
    
    @abstractmethod
    async def stop_listening(self) -> bool:
        """Stop voice recognition"""
        pass
    
    @abstractmethod
    async def process_voice_command(self, command: str) -> AudioCommand:
        """Process voice command"""
        pass
    
    @abstractmethod
    async def speak(self, text: str, voice: Optional[str] = None) -> bool:
        """Text-to-speech"""
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> List[str]:
        """Get available TTS voices"""
        pass


class AudioManager:
    """Main audio management class"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.engine: Optional[AudioEngine] = None
        self.player: Optional[MusicPlayer] = None
        self.services: Dict[AudioSource, AudioService] = {}
        self.voice_processor: Optional[VoiceProcessor] = None
        self.zones: Dict[str, AudioZone] = {}
        self.sessions: Dict[str, AudioSession] = {}
        self.stats = AudioStats()
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize audio manager"""
        try:
            # Initialize audio engine
            if self.engine:
                await self.engine.initialize()
            
            # Initialize music player
            if self.player:
                await self.player.initialize()
            
            # Initialize voice processor
            if self.voice_processor:
                await self.voice_processor.initialize()
            
            # Initialize audio services
            for service in self.services.values():
                await service.initialize()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing audio manager: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown audio manager"""
        try:
            # Stop all playback
            for zone in self.zones.values():
                if zone.playback_state == PlaybackState.PLAYING:
                    await self.stop_playback(zone.id)
            
            # Shutdown components
            if self.engine:
                await self.engine.shutdown()
            
            if self.player:
                await self.player.shutdown()
            
            if self.voice_processor:
                await self.voice_processor.shutdown()
            
            self.is_initialized = False
            return True
            
        except Exception as e:
            print(f"Error shutting down audio manager: {e}")
            return False
    
    async def create_zone(self, name: str, devices: List[AudioDevice]) -> AudioZone:
        """Create audio zone"""
        zone = AudioZone(name=name, devices=devices)
        self.zones[zone.id] = zone
        return zone
    
    async def get_zone(self, zone_id: str) -> Optional[AudioZone]:
        """Get audio zone"""
        return self.zones.get(zone_id)
    
    async def play_track(self, track: AudioTrack, zone_id: str) -> AudioResponse:
        """Play track in zone"""
        if not self.player:
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message="Music player not available"
            )
        
        return await self.player.play(track, zone_id)
    
    async def pause_playback(self, zone_id: str) -> AudioResponse:
        """Pause playback in zone"""
        if not self.player:
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message="Music player not available"
            )
        
        return await self.player.pause(zone_id)
    
    async def resume_playback(self, zone_id: str) -> AudioResponse:
        """Resume playback in zone"""
        if not self.player:
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message="Music player not available"
            )
        
        return await self.player.resume(zone_id)
    
    async def stop_playback(self, zone_id: str) -> AudioResponse:
        """Stop playback in zone"""
        if not self.player:
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message="Music player not available"
            )
        
        return await self.player.stop(zone_id)
    
    async def set_zone_volume(self, zone_id: str, volume: float) -> AudioResponse:
        """Set zone volume"""
        zone = self.zones.get(zone_id)
        if not zone:
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message="Zone not found"
            )
        
        zone.volume = max(0.0, min(1.0, volume))
        
        if self.player:
            return await self.player.set_volume(volume, zone_id)
        
        return AudioResponse(
            command_id=str(uuid.uuid4()),
            success=True,
            message=f"Zone volume set to {volume:.1%}"
        )
    
    async def get_stats(self) -> AudioStats:
        """Get audio system statistics"""
        self.stats.active_zones = len([z for z in self.zones.values() if z.is_active])
        self.stats.active_sessions = len(self.sessions)
        self.stats.available_devices = len(await self.engine.get_devices()) if self.engine else 0
        self.stats.last_updated = datetime.now()
        return self.stats
