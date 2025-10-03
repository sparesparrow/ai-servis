"""
Music Player Implementation
Handles audio playback, playlists, and zone management
"""
import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
import os
from pathlib import Path

from audio_models import (
    MusicPlayer, AudioTrack, AudioResponse, AudioZone, AudioSession,
    PlaybackState, AudioSource, AudioFormat, AudioConfig
)

logger = logging.getLogger(__name__)


class PyGameMusicPlayer(MusicPlayer):
    """Music player using PyGame for audio playback"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.zones: Dict[str, AudioZone] = {}
        self.sessions: Dict[str, AudioSession] = {}
        self.playback_callbacks: Dict[str, List[Callable]] = {}
        self.is_initialized = False
        
        # PyGame mixer for audio playback
        self.mixer = None
        self.current_tracks: Dict[str, AudioTrack] = {}
        self.playback_positions: Dict[str, float] = {}
        self.playback_start_times: Dict[str, float] = {}
        
        # Background tasks
        self._position_tracker_task = None
        self._playback_monitor_task = None
    
    async def initialize(self) -> bool:
        """Initialize the music player"""
        try:
            import pygame
            pygame.mixer.pre_init(
                frequency=self.config.sample_rate,
                size=-16,  # 16-bit signed
                channels=self.config.channels,
                buffer=self.config.buffer_size
            )
            pygame.mixer.init()
            
            self.mixer = pygame.mixer
            self.is_initialized = True
            
            # Start background tasks
            self._position_tracker_task = asyncio.create_task(self._track_positions())
            self._playback_monitor_task = asyncio.create_task(self._monitor_playback())
            
            logger.info("Music player initialized with PyGame")
            return True
            
        except ImportError:
            logger.error("PyGame not available, falling back to basic player")
            return await self._initialize_basic_player()
        except Exception as e:
            logger.error(f"Failed to initialize music player: {e}")
            return False
    
    async def _initialize_basic_player(self) -> bool:
        """Initialize basic music player without PyGame"""
        try:
            # Basic player implementation without PyGame
            self.is_initialized = True
            logger.info("Basic music player initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize basic player: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the music player"""
        try:
            # Stop all playback
            for zone_id in list(self.zones.keys()):
                await self.stop(zone_id)
            
            # Cancel background tasks
            if self._position_tracker_task:
                self._position_tracker_task.cancel()
            if self._playback_monitor_task:
                self._playback_monitor_task.cancel()
            
            # Shutdown PyGame mixer
            if self.mixer:
                self.mixer.quit()
            
            self.is_initialized = False
            logger.info("Music player shutdown")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down music player: {e}")
            return False
    
    async def play(self, track: AudioTrack, zone_id: str) -> AudioResponse:
        """Play a track in the specified zone"""
        try:
            command_id = str(uuid.uuid4())
            
            # Get or create zone
            zone = await self._get_or_create_zone(zone_id)
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Failed to create zone {zone_id}"
                )
            
            # Stop current playback if any
            if zone.playback_state == PlaybackState.PLAYING:
                await self.stop(zone_id)
            
            # Load and play track
            success = await self._load_and_play_track(track, zone_id)
            
            if success:
                zone.current_track = track
                zone.playback_state = PlaybackState.PLAYING
                zone.position = 0.0
                self.current_tracks[zone_id] = track
                self.playback_positions[zone_id] = 0.0
                self.playback_start_times[zone_id] = time.time()
                
                # Notify callbacks
                await self._notify_callbacks(zone_id, "play", track)
                
                return AudioResponse(
                    command_id=command_id,
                    success=True,
                    message=f"Playing {track.title} by {track.artist}",
                    data={
                        "track": track.dict(),
                        "zone_id": zone_id,
                        "position": 0.0
                    }
                )
            else:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Failed to play {track.title}"
                )
                
        except Exception as e:
            logger.error(f"Error playing track: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error playing track: {str(e)}"
            )
    
    async def pause(self, zone_id: str) -> AudioResponse:
        """Pause playback in the specified zone"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            if zone.playback_state != PlaybackState.PLAYING:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message="No track is currently playing"
                )
            
            # Pause playback
            if self.mixer:
                self.mixer.music.pause()
            
            zone.playback_state = PlaybackState.PAUSED
            
            # Notify callbacks
            await self._notify_callbacks(zone_id, "pause", zone.current_track)
            
            return AudioResponse(
                command_id=command_id,
                success=True,
                message="Playback paused",
                data={
                    "zone_id": zone_id,
                    "position": zone.position
                }
            )
            
        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error pausing playback: {str(e)}"
            )
    
    async def resume(self, zone_id: str) -> AudioResponse:
        """Resume playback in the specified zone"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            if zone.playback_state != PlaybackState.PAUSED:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message="No track is currently paused"
                )
            
            # Resume playback
            if self.mixer:
                self.mixer.music.unpause()
            
            zone.playback_state = PlaybackState.PLAYING
            self.playback_start_times[zone_id] = time.time() - zone.position
            
            # Notify callbacks
            await self._notify_callbacks(zone_id, "resume", zone.current_track)
            
            return AudioResponse(
                command_id=command_id,
                success=True,
                message="Playback resumed",
                data={
                    "zone_id": zone_id,
                    "position": zone.position
                }
            )
            
        except Exception as e:
            logger.error(f"Error resuming playback: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error resuming playback: {str(e)}"
            )
    
    async def stop(self, zone_id: str) -> AudioResponse:
        """Stop playback in the specified zone"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            # Stop playback
            if self.mixer:
                self.mixer.music.stop()
            
            zone.playback_state = PlaybackState.STOPPED
            zone.position = 0.0
            
            # Clean up
            if zone_id in self.current_tracks:
                del self.current_tracks[zone_id]
            if zone_id in self.playback_positions:
                del self.playback_positions[zone_id]
            if zone_id in self.playback_start_times:
                del self.playback_start_times[zone_id]
            
            # Notify callbacks
            await self._notify_callbacks(zone_id, "stop", zone.current_track)
            
            return AudioResponse(
                command_id=command_id,
                success=True,
                message="Playback stopped",
                data={"zone_id": zone_id}
            )
            
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error stopping playback: {str(e)}"
            )
    
    async def next_track(self, zone_id: str) -> AudioResponse:
        """Play next track in the specified zone"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            # Get session for this zone
            session = self._get_session_for_zone(zone_id)
            if not session or not session.playlist:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message="No playlist available"
                )
            
            # Find next track
            current_track = zone.current_track
            if not current_track:
                # Play first track
                if session.playlist.tracks:
                    next_track = session.playlist.tracks[0]
                else:
                    return AudioResponse(
                        command_id=command_id,
                        success=False,
                        message="No tracks in playlist"
                    )
            else:
                # Find current track index
                current_index = -1
                for i, track in enumerate(session.playlist.tracks):
                    if track.id == current_track.id:
                        current_index = i
                        break
                
                if current_index == -1:
                    return AudioResponse(
                        command_id=command_id,
                        success=False,
                        message="Current track not found in playlist"
                    )
                
                # Get next track
                if session.is_shuffle:
                    # Shuffle mode: pick random track
                    available_tracks = [t for t in session.playlist.tracks if t.id != current_track.id]
                    if available_tracks:
                        next_track = random.choice(available_tracks)
                    else:
                        return AudioResponse(
                            command_id=command_id,
                            success=False,
                            message="No more tracks in playlist"
                        )
                else:
                    # Normal mode: next track in sequence
                    next_index = current_index + 1
                    if next_index < len(session.playlist.tracks):
                        next_track = session.playlist.tracks[next_index]
                    else:
                        # End of playlist
                        if session.repeat_mode == "all":
                            next_track = session.playlist.tracks[0]
                        else:
                            return AudioResponse(
                                command_id=command_id,
                                success=False,
                                message="End of playlist"
                            )
            
            # Play next track
            return await self.play(next_track, zone_id)
            
        except Exception as e:
            logger.error(f"Error playing next track: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error playing next track: {str(e)}"
            )
    
    async def previous_track(self, zone_id: str) -> AudioResponse:
        """Play previous track in the specified zone"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            # Get session for this zone
            session = self._get_session_for_zone(zone_id)
            if not session or not session.playlist:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message="No playlist available"
                )
            
            # Find previous track
            current_track = zone.current_track
            if not current_track:
                # Play last track
                if session.playlist.tracks:
                    prev_track = session.playlist.tracks[-1]
                else:
                    return AudioResponse(
                        command_id=command_id,
                        success=False,
                        message="No tracks in playlist"
                    )
            else:
                # Find current track index
                current_index = -1
                for i, track in enumerate(session.playlist.tracks):
                    if track.id == current_track.id:
                        current_index = i
                        break
                
                if current_index == -1:
                    return AudioResponse(
                        command_id=command_id,
                        success=False,
                        message="Current track not found in playlist"
                    )
                
                # Get previous track
                if session.is_shuffle:
                    # Shuffle mode: pick random track
                    available_tracks = [t for t in session.playlist.tracks if t.id != current_track.id]
                    if available_tracks:
                        prev_track = random.choice(available_tracks)
                    else:
                        return AudioResponse(
                            command_id=command_id,
                            success=False,
                            message="No more tracks in playlist"
                        )
                else:
                    # Normal mode: previous track in sequence
                    prev_index = current_index - 1
                    if prev_index >= 0:
                        prev_track = session.playlist.tracks[prev_index]
                    else:
                        # Beginning of playlist
                        if session.repeat_mode == "all":
                            prev_track = session.playlist.tracks[-1]
                        else:
                            return AudioResponse(
                                command_id=command_id,
                                success=False,
                                message="Beginning of playlist"
                            )
            
            # Play previous track
            return await self.play(prev_track, zone_id)
            
        except Exception as e:
            logger.error(f"Error playing previous track: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error playing previous track: {str(e)}"
            )
    
    async def seek(self, position: float, zone_id: str) -> AudioResponse:
        """Seek to position in the current track"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            if not zone.current_track:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message="No track is currently playing"
                )
            
            # Validate position
            max_position = zone.current_track.duration
            position = max(0.0, min(position, max_position))
            
            # Seek to position
            if self.mixer:
                self.mixer.music.set_pos(position)
            
            zone.position = position
            self.playback_positions[zone_id] = position
            self.playback_start_times[zone_id] = time.time() - position
            
            # Notify callbacks
            await self._notify_callbacks(zone_id, "seek", zone.current_track)
            
            return AudioResponse(
                command_id=command_id,
                success=True,
                message=f"Seeked to {position:.1f} seconds",
                data={
                    "zone_id": zone_id,
                    "position": position
                }
            )
            
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error seeking: {str(e)}"
            )
    
    async def set_volume(self, volume: float, zone_id: str) -> AudioResponse:
        """Set zone volume"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            # Validate volume
            volume = max(0.0, min(1.0, volume))
            
            # Set zone volume
            zone.volume = volume
            
            # Set mixer volume if available
            if self.mixer:
                self.mixer.music.set_volume(volume)
            
            # Notify callbacks
            await self._notify_callbacks(zone_id, "volume_change", zone.current_track)
            
            return AudioResponse(
                command_id=command_id,
                success=True,
                message=f"Volume set to {volume:.1%}",
                data={
                    "zone_id": zone_id,
                    "volume": volume
                }
            )
            
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error setting volume: {str(e)}"
            )
    
    async def get_status(self, zone_id: str) -> AudioResponse:
        """Get playback status for the specified zone"""
        try:
            command_id = str(uuid.uuid4())
            zone = self.zones.get(zone_id)
            
            if not zone:
                return AudioResponse(
                    command_id=command_id,
                    success=False,
                    message=f"Zone {zone_id} not found"
                )
            
            # Get session for this zone
            session = self._get_session_for_zone(zone_id)
            
            status_data = {
                "zone_id": zone_id,
                "playback_state": zone.playback_state,
                "current_track": zone.current_track.dict() if zone.current_track else None,
                "position": zone.position,
                "volume": zone.volume,
                "is_muted": zone.is_muted,
                "session": session.dict() if session else None
            }
            
            return AudioResponse(
                command_id=command_id,
                success=True,
                message="Status retrieved",
                data=status_data
            )
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return AudioResponse(
                command_id=str(uuid.uuid4()),
                success=False,
                message=f"Error getting status: {str(e)}"
            )
    
    async def _get_or_create_zone(self, zone_id: str) -> Optional[AudioZone]:
        """Get or create audio zone"""
        if zone_id not in self.zones:
            zone = AudioZone(id=zone_id, name=f"Zone {zone_id}")
            self.zones[zone_id] = zone
        return self.zones[zone_id]
    
    async def _get_session_for_zone(self, zone_id: str) -> Optional[AudioSession]:
        """Get session for zone"""
        for session in self.sessions.values():
            if session.zone_id == zone_id:
                return session
        return None
    
    async def _load_and_play_track(self, track: AudioTrack, zone_id: str) -> bool:
        """Load and play track"""
        try:
            if not self.mixer:
                # Basic player without PyGame
                logger.info(f"Would play track: {track.title}")
                return True
            
            # Load track file
            if track.file_path and os.path.exists(track.file_path):
                self.mixer.music.load(track.file_path)
                self.mixer.music.play()
                return True
            elif track.url:
                # For URL-based tracks, we would need to download or stream
                # This is a simplified implementation
                logger.info(f"Would stream track from URL: {track.url}")
                return True
            else:
                logger.error(f"No valid file path or URL for track: {track.title}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading track: {e}")
            return False
    
    async def _track_positions(self):
        """Background task to track playback positions"""
        while self.is_initialized:
            try:
                for zone_id, start_time in self.playback_start_times.items():
                    if zone_id in self.zones:
                        zone = self.zones[zone_id]
                        if zone.playback_state == PlaybackState.PLAYING:
                            current_time = time.time()
                            zone.position = current_time - start_time
                            self.playback_positions[zone_id] = zone.position
                            
                            # Check if track finished
                            if zone.current_track and zone.position >= zone.current_track.duration:
                                await self._handle_track_finished(zone_id)
                
                await asyncio.sleep(0.1)  # Update every 100ms
                
            except Exception as e:
                logger.error(f"Error tracking positions: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_playback(self):
        """Background task to monitor playback"""
        while self.is_initialized:
            try:
                for zone_id, zone in self.zones.items():
                    if zone.playback_state == PlaybackState.PLAYING:
                        # Check if PyGame mixer is still playing
                        if self.mixer and not self.mixer.music.get_busy():
                            # Track finished or error
                            await self._handle_track_finished(zone_id)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error monitoring playback: {e}")
                await asyncio.sleep(1)
    
    async def _handle_track_finished(self, zone_id: str):
        """Handle track finished event"""
        try:
            zone = self.zones.get(zone_id)
            if not zone:
                return
            
            # Notify callbacks
            await self._notify_callbacks(zone_id, "track_finished", zone.current_track)
            
            # Auto-play next track if enabled
            if self.config.auto_play:
                await self.next_track(zone_id)
            else:
                zone.playback_state = PlaybackState.STOPPED
                zone.position = 0.0
                
        except Exception as e:
            logger.error(f"Error handling track finished: {e}")
    
    async def _notify_callbacks(self, zone_id: str, event: str, track: Optional[AudioTrack]):
        """Notify registered callbacks"""
        try:
            callbacks = self.playback_callbacks.get(zone_id, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event, track, zone_id)
                    else:
                        callback(event, track, zone_id)
                except Exception as e:
                    logger.error(f"Error in playback callback: {e}")
        except Exception as e:
            logger.error(f"Error notifying callbacks: {e}")
    
    def add_playback_callback(self, zone_id: str, callback: Callable):
        """Add playback callback for zone"""
        if zone_id not in self.playback_callbacks:
            self.playback_callbacks[zone_id] = []
        self.playback_callbacks[zone_id].append(callback)
    
    def remove_playback_callback(self, zone_id: str, callback: Callable):
        """Remove playback callback for zone"""
        if zone_id in self.playback_callbacks:
            try:
                self.playback_callbacks[zone_id].remove(callback)
            except ValueError:
                pass
    
    async def create_session(self, user_id: str, zone_id: str, playlist: Optional[Any] = None) -> AudioSession:
        """Create audio session"""
        session = AudioSession(
            user_id=user_id,
            zone_id=zone_id,
            playlist=playlist
        )
        self.sessions[session.id] = session
        return session
    
    async def get_session(self, session_id: str) -> Optional[AudioSession]:
        """Get audio session"""
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete audio session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
