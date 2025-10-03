"""
Enhanced Music Player with Service Integration
Integrates with multiple music services and provides advanced playback features
"""
import asyncio
import logging
import os
import json
import tempfile
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import pygame
import aiohttp
import aiofiles

from music_service_abstraction import (
    MusicServiceManager, MusicServiceType, Track, Album, Artist, Playlist, 
    SearchResult, PlaybackState
)
from audio_models import AudioZone, AudioSession

logger = logging.getLogger(__name__)


class RepeatMode(Enum):
    """Repeat modes"""
    NONE = "none"
    ONE = "one"
    ALL = "all"


class ShuffleMode(Enum):
    """Shuffle modes"""
    OFF = "off"
    ON = "on"


class EnhancedMusicPlayer:
    """Enhanced music player with service integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Music service manager
        self.service_manager = MusicServiceManager(config)
        
        # Playback state
        self.current_track: Optional[Track] = None
        self.current_playlist: Optional[Playlist] = None
        self.playlist_tracks: List[Track] = []
        self.current_index = 0
        self.playback_state = PlaybackState.STOPPED
        
        # Playback settings
        self.volume = 0.7
        self.repeat_mode = RepeatMode.NONE
        self.shuffle_mode = ShuffleMode.OFF
        self.shuffled_indices: List[int] = []
        
        # Audio zones
        self.zones: Dict[str, AudioZone] = {}
        self.active_zone: Optional[str] = None
        
        # Sessions
        self.sessions: Dict[str, AudioSession] = {}
        self.active_session: Optional[str] = None
        
        # Playback control
        self.is_playing = False
        self.is_paused = False
        self.position = 0.0  # seconds
        self.duration = 0.0  # seconds
        
        # Callbacks
        self.track_change_callbacks: List[Callable[[Track], None]] = []
        self.playback_state_callbacks: List[Callable[[PlaybackState], None]] = []
        self.position_callbacks: List[Callable[[float], None]] = []
        
        # Audio engine
        self.audio_engine = None
        self.mixer_initialized = False
        
        # Cache
        self.track_cache: Dict[str, str] = {}  # track_id -> local_file_path
        self.cache_directory = config.get("cache_directory", "/tmp/music_cache")
        
        # Initialize
        self._initialize_audio()
        self._ensure_cache_directory()
    
    def _initialize_audio(self):
        """Initialize audio system"""
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            self.mixer_initialized = True
            logger.info("Audio mixer initialized")
        except Exception as e:
            logger.error(f"Error initializing audio mixer: {e}")
            self.mixer_initialized = False
    
    def _ensure_cache_directory(self):
        """Ensure cache directory exists"""
        try:
            os.makedirs(self.cache_directory, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating cache directory: {e}")
    
    async def initialize(self) -> bool:
        """Initialize the music player"""
        try:
            # Authenticate with music services
            auth_results = await self.service_manager.authenticate_all()
            logger.info(f"Music service authentication results: {auth_results}")
            
            # Create default zone
            await self.create_zone("default", "Default Zone")
            self.active_zone = "default"
            
            logger.info("Enhanced music player initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing music player: {e}")
            return False
    
    async def search_music(self, query: str, service_type: Optional[MusicServiceType] = None, limit: int = 20) -> SearchResult:
        """Search for music across services"""
        try:
            if service_type:
                # Search specific service
                service = self.service_manager.services.get(service_type)
                if service and service.is_authenticated:
                    return await service.search(query, limit)
                else:
                    logger.warning(f"Service {service_type.value} not available")
                    return SearchResult([], [], [], [], 0, 0, 0, 0)
            else:
                # Search all services
                return await self.service_manager.search_all(query, limit)
                
        except Exception as e:
            logger.error(f"Error searching music: {e}")
            return SearchResult([], [], [], [], 0, 0, 0, 0)
    
    async def play_track(self, track: Track, zone: Optional[str] = None) -> bool:
        """Play a specific track"""
        try:
            if not self.mixer_initialized:
                logger.error("Audio mixer not initialized")
                return False
            
            # Set active zone
            if zone and zone in self.zones:
                self.active_zone = zone
            
            # Get playable URL
            audio_url = await self._get_playable_url(track)
            if not audio_url:
                logger.error(f"No playable URL for track: {track.title}")
                return False
            
            # Download and cache track if needed
            local_file = await self._ensure_track_cached(track, audio_url)
            if not local_file:
                logger.error(f"Failed to cache track: {track.title}")
                return False
            
            # Stop current playback
            await self.stop()
            
            # Load and play track
            try:
                pygame.mixer.music.load(local_file)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                
                self.current_track = track
                self.current_playlist = None
                self.playlist_tracks = [track]
                self.current_index = 0
                self.playback_state = PlaybackState.PLAYING
                self.is_playing = True
                self.is_paused = False
                self.duration = track.duration
                self.position = 0.0
                
                # Notify callbacks
                await self._notify_track_change(track)
                await self._notify_playback_state_change(PlaybackState.PLAYING)
                
                # Start position tracking
                asyncio.create_task(self._track_position())
                
                logger.info(f"Playing track: {track.title} by {track.artist}")
                return True
                
            except Exception as e:
                logger.error(f"Error playing track: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error in play_track: {e}")
            return False
    
    async def play_playlist(self, playlist: Playlist, start_index: int = 0, zone: Optional[str] = None) -> bool:
        """Play a playlist"""
        try:
            if not playlist.tracks:
                logger.error("Playlist has no tracks")
                return False
            
            # Set active zone
            if zone and zone in self.zones:
                self.active_zone = zone
            
            # Set up playlist
            self.current_playlist = playlist
            self.playlist_tracks = playlist.tracks.copy()
            self.current_index = start_index
            
            # Apply shuffle if enabled
            if self.shuffle_mode == ShuffleMode.ON:
                self._shuffle_playlist()
            
            # Play first track
            if self.current_index < len(self.playlist_tracks):
                track = self.playlist_tracks[self.current_index]
                return await self.play_track(track, zone)
            
            return False
            
        except Exception as e:
            logger.error(f"Error playing playlist: {e}")
            return False
    
    async def pause(self) -> bool:
        """Pause playback"""
        try:
            if self.is_playing and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                self.playback_state = PlaybackState.PAUSED
                await self._notify_playback_state_change(PlaybackState.PAUSED)
                logger.info("Playback paused")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
            return False
    
    async def resume(self) -> bool:
        """Resume playback"""
        try:
            if self.is_playing and self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.playback_state = PlaybackState.PLAYING
                await self._notify_playback_state_change(PlaybackState.PLAYING)
                logger.info("Playback resumed")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error resuming playback: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop playback"""
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.playback_state = PlaybackState.STOPPED
            self.position = 0.0
            
            await self._notify_playback_state_change(PlaybackState.STOPPED)
            logger.info("Playback stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return False
    
    async def next_track(self) -> bool:
        """Play next track in playlist"""
        try:
            if not self.playlist_tracks:
                return False
            
            # Determine next index
            if self.shuffle_mode == ShuffleMode.ON and self.shuffled_indices:
                current_shuffle_index = self.shuffled_indices.index(self.current_index)
                if current_shuffle_index < len(self.shuffled_indices) - 1:
                    next_index = self.shuffled_indices[current_shuffle_index + 1]
                else:
                    # End of shuffled playlist
                    if self.repeat_mode == RepeatMode.ALL:
                        self._shuffle_playlist()
                        next_index = self.shuffled_indices[0]
                    else:
                        return False
            else:
                # Normal order
                if self.current_index < len(self.playlist_tracks) - 1:
                    next_index = self.current_index + 1
                else:
                    # End of playlist
                    if self.repeat_mode == RepeatMode.ALL:
                        next_index = 0
                    else:
                        return False
            
            # Play next track
            self.current_index = next_index
            track = self.playlist_tracks[self.current_index]
            return await self.play_track(track)
            
        except Exception as e:
            logger.error(f"Error playing next track: {e}")
            return False
    
    async def previous_track(self) -> bool:
        """Play previous track in playlist"""
        try:
            if not self.playlist_tracks:
                return False
            
            # Determine previous index
            if self.shuffle_mode == ShuffleMode.ON and self.shuffled_indices:
                current_shuffle_index = self.shuffled_indices.index(self.current_index)
                if current_shuffle_index > 0:
                    prev_index = self.shuffled_indices[current_shuffle_index - 1]
                else:
                    # Beginning of shuffled playlist
                    if self.repeat_mode == RepeatMode.ALL:
                        prev_index = self.shuffled_indices[-1]
                    else:
                        return False
            else:
                # Normal order
                if self.current_index > 0:
                    prev_index = self.current_index - 1
                else:
                    # Beginning of playlist
                    if self.repeat_mode == RepeatMode.ALL:
                        prev_index = len(self.playlist_tracks) - 1
                    else:
                        return False
            
            # Play previous track
            self.current_index = prev_index
            track = self.playlist_tracks[self.current_index]
            return await self.play_track(track)
            
        except Exception as e:
            logger.error(f"Error playing previous track: {e}")
            return False
    
    async def seek(self, position: float) -> bool:
        """Seek to position in current track"""
        try:
            if not self.current_track or not self.is_playing:
                return False
            
            # Pygame doesn't support seeking directly
            # This is a limitation - would need a more advanced audio library
            logger.warning("Seeking not supported with pygame mixer")
            return False
            
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set playback volume"""
        try:
            volume = max(0.0, min(1.0, volume))
            self.volume = volume
            
            if self.mixer_initialized:
                pygame.mixer.music.set_volume(volume)
            
            logger.info(f"Volume set to {volume:.1%}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    def set_repeat_mode(self, mode: RepeatMode) -> bool:
        """Set repeat mode"""
        try:
            self.repeat_mode = mode
            logger.info(f"Repeat mode set to {mode.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting repeat mode: {e}")
            return False
    
    def set_shuffle_mode(self, mode: ShuffleMode) -> bool:
        """Set shuffle mode"""
        try:
            self.shuffle_mode = mode
            
            if mode == ShuffleMode.ON and self.playlist_tracks:
                self._shuffle_playlist()
            elif mode == ShuffleMode.OFF:
                self.shuffled_indices.clear()
            
            logger.info(f"Shuffle mode set to {mode.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting shuffle mode: {e}")
            return False
    
    def _shuffle_playlist(self):
        """Shuffle playlist indices"""
        import random
        self.shuffled_indices = list(range(len(self.playlist_tracks)))
        random.shuffle(self.shuffled_indices)
    
    async def _get_playable_url(self, track: Track) -> Optional[str]:
        """Get playable URL for track"""
        try:
            # For local files, return the file path
            if track.service == MusicServiceType.LOCAL_FILES:
                return track.external_url
            
            # For streaming services, get audio URL
            return await self.service_manager.get_playable_url(track.id, track.service)
            
        except Exception as e:
            logger.error(f"Error getting playable URL: {e}")
            return None
    
    async def _ensure_track_cached(self, track: Track, audio_url: str) -> Optional[str]:
        """Ensure track is cached locally"""
        try:
            # Check if already cached
            if track.id in self.track_cache:
                cached_file = self.track_cache[track.id]
                if os.path.exists(cached_file):
                    return cached_file
            
            # Download and cache track
            if track.service == MusicServiceType.LOCAL_FILES:
                # Local file, just return the path
                return audio_url
            
            # Download from URL
            cache_file = os.path.join(self.cache_directory, f"{track.id}.mp3")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(cache_file, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        self.track_cache[track.id] = cache_file
                        logger.info(f"Cached track: {track.title}")
                        return cache_file
                    else:
                        logger.error(f"Failed to download track: {response.status}")
                        return None
            
        except Exception as e:
            logger.error(f"Error caching track: {e}")
            return None
    
    async def _track_position(self):
        """Track playback position"""
        try:
            while self.is_playing and not self.is_paused:
                # Pygame doesn't provide position info
                # This is a limitation - would need a more advanced audio library
                self.position += 0.1
                
                # Check if track ended
                if self.position >= self.duration:
                    await self._handle_track_end()
                    break
                
                # Notify position callbacks
                await self._notify_position_change(self.position)
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error tracking position: {e}")
    
    async def _handle_track_end(self):
        """Handle track end"""
        try:
            if self.repeat_mode == RepeatMode.ONE:
                # Repeat current track
                await self.play_track(self.current_track)
            else:
                # Play next track
                await self.next_track()
                
        except Exception as e:
            logger.error(f"Error handling track end: {e}")
    
    async def create_zone(self, zone_id: str, name: str) -> bool:
        """Create audio zone"""
        try:
            zone = AudioZone(
                id=zone_id,
                name=name,
                volume=1.0,
                muted=False,
                active_tracks=[]
            )
            self.zones[zone_id] = zone
            logger.info(f"Created audio zone: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating zone: {e}")
            return False
    
    async def set_active_zone(self, zone_id: str) -> bool:
        """Set active audio zone"""
        try:
            if zone_id in self.zones:
                self.active_zone = zone_id
                logger.info(f"Active zone set to: {zone_id}")
                return True
            else:
                logger.error(f"Zone not found: {zone_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting active zone: {e}")
            return False
    
    async def set_zone_volume(self, zone_id: str, volume: float) -> bool:
        """Set zone volume"""
        try:
            if zone_id in self.zones:
                self.zones[zone_id].volume = max(0.0, min(1.0, volume))
                logger.info(f"Zone {zone_id} volume set to {volume:.1%}")
                return True
            else:
                logger.error(f"Zone not found: {zone_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting zone volume: {e}")
            return False
    
    # Callback management
    def add_track_change_callback(self, callback: Callable[[Track], None]):
        """Add track change callback"""
        self.track_change_callbacks.append(callback)
    
    def add_playback_state_callback(self, callback: Callable[[PlaybackState], None]):
        """Add playback state callback"""
        self.playback_state_callbacks.append(callback)
    
    def add_position_callback(self, callback: Callable[[float], None]):
        """Add position callback"""
        self.position_callbacks.append(callback)
    
    async def _notify_track_change(self, track: Track):
        """Notify track change callbacks"""
        for callback in self.track_change_callbacks:
            try:
                callback(track)
            except Exception as e:
                logger.error(f"Error in track change callback: {e}")
    
    async def _notify_playback_state_change(self, state: PlaybackState):
        """Notify playback state callbacks"""
        for callback in self.playback_state_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"Error in playback state callback: {e}")
    
    async def _notify_position_change(self, position: float):
        """Notify position callbacks"""
        for callback in self.position_callbacks:
            try:
                callback(position)
            except Exception as e:
                logger.error(f"Error in position callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get player status"""
        return {
            "current_track": {
                "id": self.current_track.id if self.current_track else None,
                "title": self.current_track.title if self.current_track else None,
                "artist": self.current_track.artist if self.current_track else None,
                "album": self.current_track.album if self.current_track else None,
                "duration": self.current_track.duration if self.current_track else 0,
                "service": self.current_track.service.value if self.current_track else None
            },
            "playback": {
                "state": self.playback_state.value,
                "is_playing": self.is_playing,
                "is_paused": self.is_paused,
                "position": self.position,
                "duration": self.duration,
                "volume": self.volume,
                "repeat_mode": self.repeat_mode.value,
                "shuffle_mode": self.shuffle_mode.value
            },
            "playlist": {
                "current_index": self.current_index,
                "total_tracks": len(self.playlist_tracks),
                "playlist_name": self.current_playlist.name if self.current_playlist else None
            },
            "zones": {
                "active_zone": self.active_zone,
                "available_zones": list(self.zones.keys())
            }
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.stop()
            await self.service_manager.close_all()
            
            if self.mixer_initialized:
                pygame.mixer.quit()
            
            logger.info("Enhanced music player cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up music player: {e}")
