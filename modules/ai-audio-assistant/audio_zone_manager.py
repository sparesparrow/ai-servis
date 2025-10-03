"""
Audio Zone Management System
Handles multi-room audio, zone configuration, and audio synchronization
"""
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid

from audio_models import AudioZone, AudioDevice, AudioTrack, AudioSession

logger = logging.getLogger(__name__)


class ZoneState(Enum):
    """Audio zone states"""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class SyncMode(Enum):
    """Audio synchronization modes"""
    NONE = "none"
    MASTER_SLAVE = "master_slave"
    PEER_TO_PEER = "peer_to_peer"
    TIME_BASED = "time_based"


class ContentFilter(Enum):
    """Content filtering types"""
    NONE = "none"
    EXPLICIT = "explicit"
    GENRE = "genre"
    LANGUAGE = "language"
    AGE_RATING = "age_rating"


@dataclass
class ZoneConfiguration:
    """Audio zone configuration"""
    id: str
    name: str
    description: Optional[str] = None
    devices: List[str] = []  # Device IDs
    volume: float = 1.0
    muted: bool = False
    sync_mode: SyncMode = SyncMode.NONE
    master_zone: Optional[str] = None
    content_filters: List[ContentFilter] = None
    allowed_genres: List[str] = None
    blocked_genres: List[str] = None
    max_volume: float = 1.0
    min_volume: float = 0.0
    fade_in_duration: float = 0.0
    fade_out_duration: float = 0.0
    crossfade_duration: float = 0.0
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.content_filters is None:
            self.content_filters = []
        if self.allowed_genres is None:
            self.allowed_genres = []
        if self.blocked_genres is None:
            self.blocked_genres = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class ZonePlaybackState:
    """Zone playback state"""
    zone_id: str
    current_track: Optional[AudioTrack] = None
    playlist: List[AudioTrack] = None
    current_index: int = 0
    position: float = 0.0
    duration: float = 0.0
    volume: float = 1.0
    muted: bool = False
    state: ZoneState = ZoneState.IDLE
    repeat_mode: str = "none"
    shuffle_mode: bool = False
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.playlist is None:
            self.playlist = []
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class SyncGroup:
    """Audio synchronization group"""
    id: str
    name: str
    zones: List[str]  # Zone IDs
    master_zone: str
    sync_mode: SyncMode
    sync_tolerance: float = 0.1  # seconds
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AudioZoneManager:
    """Manages audio zones and multi-room audio"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Zone management
        self.zones: Dict[str, ZoneConfiguration] = {}
        self.zone_states: Dict[str, ZonePlaybackState] = {}
        self.sync_groups: Dict[str, SyncGroup] = {}
        
        # Device management
        self.devices: Dict[str, AudioDevice] = {}
        self.device_zones: Dict[str, str] = {}  # device_id -> zone_id
        
        # Synchronization
        self.sync_enabled = True
        self.sync_tolerance = 0.1  # seconds
        self.sync_interval = 0.1  # seconds
        self.sync_task: Optional[asyncio.Task] = None
        
        # Content filtering
        self.content_filters_enabled = True
        self.global_filters: List[ContentFilter] = []
        
        # Callbacks
        self.zone_change_callbacks: List[Callable[[str, ZoneState], None]] = []
        self.sync_callbacks: List[Callable[[str, float], None]] = []
        self.volume_callbacks: List[Callable[[str, float], None]] = []
        
        # Performance tracking
        self.sync_delays: Dict[str, List[float]] = {}
        self.volume_changes: Dict[str, List[float]] = {}
        
        # Initialize
        self._initialize_default_zones()
    
    def _initialize_default_zones(self):
        """Initialize default audio zones"""
        try:
            # Create default zone
            default_zone = ZoneConfiguration(
                id="default",
                name="Default Zone",
                description="Default audio zone for all devices"
            )
            self.zones["default"] = default_zone
            self.zone_states["default"] = ZonePlaybackState(zone_id="default")
            
            logger.info("Default audio zones initialized")
            
        except Exception as e:
            logger.error(f"Error initializing default zones: {e}")
    
    async def create_zone(self, zone_id: str, name: str, description: str = "", 
                         devices: List[str] = None, **kwargs) -> bool:
        """Create a new audio zone"""
        try:
            if zone_id in self.zones:
                logger.warning(f"Zone {zone_id} already exists")
                return False
            
            # Create zone configuration
            zone_config = ZoneConfiguration(
                id=zone_id,
                name=name,
                description=description,
                devices=devices or [],
                **kwargs
            )
            
            # Create zone state
            zone_state = ZonePlaybackState(zone_id=zone_id)
            
            # Add to management
            self.zones[zone_id] = zone_config
            self.zone_states[zone_id] = zone_state
            
            # Assign devices to zone
            if devices:
                for device_id in devices:
                    await self.assign_device_to_zone(device_id, zone_id)
            
            logger.info(f"Created audio zone: {name} ({zone_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating zone {zone_id}: {e}")
            return False
    
    async def delete_zone(self, zone_id: str) -> bool:
        """Delete an audio zone"""
        try:
            if zone_id == "default":
                logger.warning("Cannot delete default zone")
                return False
            
            if zone_id not in self.zones:
                logger.warning(f"Zone {zone_id} not found")
                return False
            
            # Remove from sync groups
            for sync_group in self.sync_groups.values():
                if zone_id in sync_group.zones:
                    sync_group.zones.remove(zone_id)
                    if sync_group.master_zone == zone_id:
                        # Reassign master zone
                        if sync_group.zones:
                            sync_group.master_zone = sync_group.zones[0]
                        else:
                            # Delete empty sync group
                            del self.sync_groups[sync_group.id]
            
            # Unassign devices
            zone_config = self.zones[zone_id]
            for device_id in zone_config.devices:
                await self.unassign_device_from_zone(device_id)
            
            # Remove zone
            del self.zones[zone_id]
            del self.zone_states[zone_id]
            
            logger.info(f"Deleted audio zone: {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting zone {zone_id}: {e}")
            return False
    
    async def assign_device_to_zone(self, device_id: str, zone_id: str) -> bool:
        """Assign a device to a zone"""
        try:
            if zone_id not in self.zones:
                logger.error(f"Zone {zone_id} not found")
                return False
            
            # Remove device from current zone
            if device_id in self.device_zones:
                current_zone_id = self.device_zones[device_id]
                if current_zone_id in self.zones:
                    self.zones[current_zone_id].devices.remove(device_id)
            
            # Assign to new zone
            self.zones[zone_id].devices.append(device_id)
            self.device_zones[device_id] = zone_id
            
            logger.info(f"Assigned device {device_id} to zone {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning device {device_id} to zone {zone_id}: {e}")
            return False
    
    async def unassign_device_from_zone(self, device_id: str) -> bool:
        """Unassign a device from its current zone"""
        try:
            if device_id not in self.device_zones:
                return True  # Already unassigned
            
            zone_id = self.device_zones[device_id]
            if zone_id in self.zones:
                self.zones[zone_id].devices.remove(device_id)
            
            del self.device_zones[device_id]
            
            logger.info(f"Unassigned device {device_id} from zone {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unassigning device {device_id}: {e}")
            return False
    
    async def set_zone_volume(self, zone_id: str, volume: float) -> bool:
        """Set zone volume"""
        try:
            if zone_id not in self.zones:
                logger.error(f"Zone {zone_id} not found")
                return False
            
            # Clamp volume to zone limits
            zone_config = self.zones[zone_id]
            volume = max(zone_config.min_volume, min(zone_config.max_volume, volume))
            
            # Update zone configuration and state
            zone_config.volume = volume
            zone_config.updated_at = datetime.now()
            
            if zone_id in self.zone_states:
                self.zone_states[zone_id].volume = volume
                self.zone_states[zone_id].last_updated = datetime.now()
            
            # Track volume changes
            if zone_id not in self.volume_changes:
                self.volume_changes[zone_id] = []
            self.volume_changes[zone_id].append(volume)
            
            # Keep only recent volume changes
            if len(self.volume_changes[zone_id]) > 100:
                self.volume_changes[zone_id] = self.volume_changes[zone_id][-100:]
            
            # Notify callbacks
            await self._notify_volume_change(zone_id, volume)
            
            logger.info(f"Zone {zone_id} volume set to {volume:.1%}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting zone {zone_id} volume: {e}")
            return False
    
    async def mute_zone(self, zone_id: str, muted: bool = True) -> bool:
        """Mute/unmute a zone"""
        try:
            if zone_id not in self.zones:
                logger.error(f"Zone {zone_id} not found")
                return False
            
            # Update zone configuration and state
            self.zones[zone_id].muted = muted
            self.zones[zone_id].updated_at = datetime.now()
            
            if zone_id in self.zone_states:
                self.zone_states[zone_id].muted = muted
                self.zone_states[zone_id].last_updated = datetime.now()
            
            logger.info(f"Zone {zone_id} {'muted' if muted else 'unmuted'}")
            return True
            
        except Exception as e:
            logger.error(f"Error muting zone {zone_id}: {e}")
            return False
    
    async def create_sync_group(self, group_id: str, name: str, zones: List[str], 
                               master_zone: str, sync_mode: SyncMode = SyncMode.MASTER_SLAVE) -> bool:
        """Create an audio synchronization group"""
        try:
            if group_id in self.sync_groups:
                logger.warning(f"Sync group {group_id} already exists")
                return False
            
            # Validate zones
            for zone_id in zones:
                if zone_id not in self.zones:
                    logger.error(f"Zone {zone_id} not found")
                    return False
            
            if master_zone not in zones:
                logger.error(f"Master zone {master_zone} must be in the group")
                return False
            
            # Create sync group
            sync_group = SyncGroup(
                id=group_id,
                name=name,
                zones=zones.copy(),
                master_zone=master_zone,
                sync_mode=sync_mode
            )
            
            self.sync_groups[group_id] = sync_group
            
            # Update zone configurations
            for zone_id in zones:
                self.zones[zone_id].sync_mode = sync_mode
                self.zones[zone_id].master_zone = master_zone
                self.zones[zone_id].updated_at = datetime.now()
            
            # Start synchronization if enabled
            if self.sync_enabled and not self.sync_task:
                self.sync_task = asyncio.create_task(self._sync_loop())
            
            logger.info(f"Created sync group: {name} ({group_id}) with {len(zones)} zones")
            return True
            
        except Exception as e:
            logger.error(f"Error creating sync group {group_id}: {e}")
            return False
    
    async def delete_sync_group(self, group_id: str) -> bool:
        """Delete a synchronization group"""
        try:
            if group_id not in self.sync_groups:
                logger.warning(f"Sync group {group_id} not found")
                return False
            
            sync_group = self.sync_groups[group_id]
            
            # Reset zone sync configurations
            for zone_id in sync_group.zones:
                if zone_id in self.zones:
                    self.zones[zone_id].sync_mode = SyncMode.NONE
                    self.zones[zone_id].master_zone = None
                    self.zones[zone_id].updated_at = datetime.now()
            
            # Remove sync group
            del self.sync_groups[group_id]
            
            # Stop sync task if no more groups
            if not self.sync_groups and self.sync_task:
                self.sync_task.cancel()
                self.sync_task = None
            
            logger.info(f"Deleted sync group: {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting sync group {group_id}: {e}")
            return False
    
    async def _sync_loop(self):
        """Audio synchronization loop"""
        try:
            while self.sync_groups and self.sync_enabled:
                for sync_group in self.sync_groups.values():
                    await self._sync_group(sync_group)
                
                await asyncio.sleep(self.sync_interval)
                
        except asyncio.CancelledError:
            logger.info("Sync loop cancelled")
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
    
    async def _sync_group(self, sync_group: SyncGroup):
        """Synchronize a group of zones"""
        try:
            if sync_group.master_zone not in self.zone_states:
                return
            
            master_state = self.zone_states[sync_group.master_zone]
            
            for zone_id in sync_group.zones:
                if zone_id == sync_group.master_zone:
                    continue
                
                if zone_id not in self.zone_states:
                    continue
                
                slave_state = self.zone_states[zone_id]
                
                # Calculate sync delay
                sync_delay = await self._calculate_sync_delay(master_state, slave_state)
                
                if abs(sync_delay) > sync_group.sync_tolerance:
                    await self._apply_sync_correction(zone_id, sync_delay)
                    
                    # Track sync delays
                    if zone_id not in self.sync_delays:
                        self.sync_delays[zone_id] = []
                    self.sync_delays[zone_id].append(sync_delay)
                    
                    # Keep only recent sync delays
                    if len(self.sync_delays[zone_id]) > 100:
                        self.sync_delays[zone_id] = self.sync_delays[zone_id][-100:]
                    
                    # Notify sync callbacks
                    await self._notify_sync_change(zone_id, sync_delay)
                
        except Exception as e:
            logger.error(f"Error syncing group {sync_group.id}: {e}")
    
    async def _calculate_sync_delay(self, master_state: ZonePlaybackState, 
                                   slave_state: ZonePlaybackState) -> float:
        """Calculate synchronization delay between master and slave"""
        try:
            # Simple time-based sync calculation
            # In a real implementation, this would be more sophisticated
            
            if master_state.state != slave_state.state:
                return 0.0  # Different states, no sync needed
            
            if master_state.state not in [ZoneState.PLAYING, ZoneState.PAUSED]:
                return 0.0  # Not in playable state
            
            # Calculate position difference
            position_diff = master_state.position - slave_state.position
            
            # Account for network latency and processing delays
            # This is a simplified calculation
            return position_diff
            
        except Exception as e:
            logger.error(f"Error calculating sync delay: {e}")
            return 0.0
    
    async def _apply_sync_correction(self, zone_id: str, sync_delay: float):
        """Apply synchronization correction to a zone"""
        try:
            if zone_id not in self.zone_states:
                return
            
            zone_state = self.zone_states[zone_id]
            
            # Apply position correction
            if abs(sync_delay) > 0.1:  # Only correct significant delays
                new_position = zone_state.position + sync_delay
                zone_state.position = max(0.0, new_position)
                zone_state.last_updated = datetime.now()
                
                logger.debug(f"Applied sync correction to zone {zone_id}: {sync_delay:.3f}s")
            
        except Exception as e:
            logger.error(f"Error applying sync correction to zone {zone_id}: {e}")
    
    async def set_zone_content_filter(self, zone_id: str, filters: List[ContentFilter]) -> bool:
        """Set content filters for a zone"""
        try:
            if zone_id not in self.zones:
                logger.error(f"Zone {zone_id} not found")
                return False
            
            self.zones[zone_id].content_filters = filters.copy()
            self.zones[zone_id].updated_at = datetime.now()
            
            logger.info(f"Set content filters for zone {zone_id}: {[f.value for f in filters]}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting content filters for zone {zone_id}: {e}")
            return False
    
    async def set_zone_genre_filters(self, zone_id: str, allowed_genres: List[str] = None, 
                                   blocked_genres: List[str] = None) -> bool:
        """Set genre filters for a zone"""
        try:
            if zone_id not in self.zones:
                logger.error(f"Zone {zone_id} not found")
                return False
            
            if allowed_genres is not None:
                self.zones[zone_id].allowed_genres = allowed_genres.copy()
            
            if blocked_genres is not None:
                self.zones[zone_id].blocked_genres = blocked_genres.copy()
            
            self.zones[zone_id].updated_at = datetime.now()
            
            logger.info(f"Set genre filters for zone {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting genre filters for zone {zone_id}: {e}")
            return False
    
    async def filter_content_for_zone(self, zone_id: str, track: AudioTrack) -> bool:
        """Check if content is allowed for a zone"""
        try:
            if zone_id not in self.zones:
                return True  # Allow content if zone not found
            
            zone_config = self.zones[zone_id]
            
            # Check content filters
            for filter_type in zone_config.content_filters:
                if filter_type == ContentFilter.EXPLICIT and track.explicit:
                    logger.debug(f"Blocked explicit content in zone {zone_id}")
                    return False
                elif filter_type == ContentFilter.LANGUAGE and track.language:
                    # Language filtering would need language detection
                    pass
                elif filter_type == ContentFilter.AGE_RATING:
                    # Age rating filtering would need rating system
                    pass
            
            # Check genre filters
            if track.genre:
                if zone_config.allowed_genres and track.genre not in zone_config.allowed_genres:
                    logger.debug(f"Blocked genre {track.genre} in zone {zone_id}")
                    return False
                
                if zone_config.blocked_genres and track.genre in zone_config.blocked_genres:
                    logger.debug(f"Blocked genre {track.genre} in zone {zone_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error filtering content for zone {zone_id}: {e}")
            return True  # Allow content on error
    
    async def get_zone_status(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive zone status"""
        try:
            if zone_id not in self.zones:
                return None
            
            zone_config = self.zones[zone_id]
            zone_state = self.zone_states.get(zone_id)
            
            # Calculate sync statistics
            sync_delays = self.sync_delays.get(zone_id, [])
            avg_sync_delay = sum(sync_delays) / len(sync_delays) if sync_delays else 0.0
            
            # Calculate volume statistics
            volume_changes = self.volume_changes.get(zone_id, [])
            avg_volume = sum(volume_changes) / len(volume_changes) if volume_changes else zone_config.volume
            
            return {
                "zone_id": zone_id,
                "configuration": asdict(zone_config),
                "state": asdict(zone_state) if zone_state else None,
                "devices": zone_config.devices,
                "sync_statistics": {
                    "avg_delay": avg_sync_delay,
                    "delay_count": len(sync_delays)
                },
                "volume_statistics": {
                    "current": zone_config.volume,
                    "average": avg_volume,
                    "change_count": len(volume_changes)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting zone status for {zone_id}: {e}")
            return None
    
    async def get_all_zones_status(self) -> Dict[str, Any]:
        """Get status of all zones"""
        try:
            zones_status = {}
            for zone_id in self.zones:
                zones_status[zone_id] = await self.get_zone_status(zone_id)
            
            return {
                "zones": zones_status,
                "sync_groups": {group_id: asdict(group) for group_id, group in self.sync_groups.items()},
                "total_zones": len(self.zones),
                "total_sync_groups": len(self.sync_groups),
                "sync_enabled": self.sync_enabled
            }
            
        except Exception as e:
            logger.error(f"Error getting all zones status: {e}")
            return {}
    
    # Callback management
    def add_zone_change_callback(self, callback: Callable[[str, ZoneState], None]):
        """Add zone state change callback"""
        self.zone_change_callbacks.append(callback)
    
    def add_sync_callback(self, callback: Callable[[str, float], None]):
        """Add synchronization callback"""
        self.sync_callbacks.append(callback)
    
    def add_volume_callback(self, callback: Callable[[str, float], None]):
        """Add volume change callback"""
        self.volume_callbacks.append(callback)
    
    async def _notify_zone_change(self, zone_id: str, state: ZoneState):
        """Notify zone change callbacks"""
        for callback in self.zone_change_callbacks:
            try:
                callback(zone_id, state)
            except Exception as e:
                logger.error(f"Error in zone change callback: {e}")
    
    async def _notify_sync_change(self, zone_id: str, sync_delay: float):
        """Notify sync callbacks"""
        for callback in self.sync_callbacks:
            try:
                callback(zone_id, sync_delay)
            except Exception as e:
                logger.error(f"Error in sync callback: {e}")
    
    async def _notify_volume_change(self, zone_id: str, volume: float):
        """Notify volume callbacks"""
        for callback in self.volume_callbacks:
            try:
                callback(zone_id, volume)
            except Exception as e:
                logger.error(f"Error in volume callback: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Audio zone manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up zone manager: {e}")
