"""
Music Service Abstraction Layer
Provides unified interface for multiple music streaming services
"""
import asyncio
import logging
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)


class MusicServiceType(Enum):
    """Music service types"""
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    LOCAL_FILES = "local_files"
    YOUTUBE_MUSIC = "youtube_music"
    SOUNDCLOUD = "soundcloud"


class PlaybackState(Enum):
    """Playback states"""
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    BUFFERING = "buffering"
    ERROR = "error"


@dataclass
class Track:
    """Music track representation"""
    id: str
    title: str
    artist: str
    album: str
    duration: int  # seconds
    service: MusicServiceType
    external_url: Optional[str] = None
    preview_url: Optional[str] = None
    image_url: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    popularity: Optional[int] = None
    explicit: bool = False
    isrc: Optional[str] = None  # International Standard Recording Code


@dataclass
class Album:
    """Music album representation"""
    id: str
    title: str
    artist: str
    service: MusicServiceType
    release_date: Optional[str] = None
    total_tracks: Optional[int] = None
    image_url: Optional[str] = None
    external_url: Optional[str] = None
    genres: Optional[List[str]] = None
    popularity: Optional[int] = None


@dataclass
class Artist:
    """Music artist representation"""
    id: str
    name: str
    service: MusicServiceType
    genres: Optional[List[str]] = None
    popularity: Optional[int] = None
    image_url: Optional[str] = None
    external_url: Optional[str] = None
    followers: Optional[int] = None


@dataclass
class Playlist:
    """Music playlist representation"""
    id: str
    name: str
    description: Optional[str] = None
    service: MusicServiceType = None
    owner: Optional[str] = None
    public: bool = False
    collaborative: bool = False
    total_tracks: Optional[int] = None
    image_url: Optional[str] = None
    external_url: Optional[str] = None
    tracks: Optional[List[Track]] = None


@dataclass
class SearchResult:
    """Search result container"""
    tracks: List[Track]
    albums: List[Album]
    artists: List[Artist]
    playlists: List[Playlist]
    total_tracks: int
    total_albums: int
    total_artists: int
    total_playlists: int


class MusicService(ABC):
    """Abstract base class for music services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_type = self._get_service_type()
        self.is_authenticated = False
        self.session: Optional[aiohttp.ClientSession] = None
    
    @abstractmethod
    def _get_service_type(self) -> MusicServiceType:
        """Get the service type"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20, offset: int = 0) -> SearchResult:
        """Search for music content"""
        pass
    
    @abstractmethod
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get track details"""
        pass
    
    @abstractmethod
    async def get_album(self, album_id: str) -> Optional[Album]:
        """Get album details"""
        pass
    
    @abstractmethod
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get artist details"""
        pass
    
    @abstractmethod
    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get playlist details"""
        pass
    
    @abstractmethod
    async def get_user_playlists(self) -> List[Playlist]:
        """Get user's playlists"""
        pass
    
    @abstractmethod
    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> Optional[Playlist]:
        """Create a new playlist"""
        pass
    
    @abstractmethod
    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Add tracks to playlist"""
        pass
    
    @abstractmethod
    async def remove_tracks_from_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Remove tracks from playlist"""
        pass
    
    @abstractmethod
    async def get_track_audio_url(self, track_id: str) -> Optional[str]:
        """Get playable audio URL for track"""
        pass
    
    async def close(self):
        """Close the service session"""
        if self.session:
            await self.session.close()


class SpotifyService(MusicService):
    """Spotify Web API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get("spotify_client_id")
        self.client_secret = config.get("spotify_client_secret")
        self.redirect_uri = config.get("spotify_redirect_uri", "http://localhost:8080/callback")
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.base_url = "https://api.spotify.com/v1"
    
    def _get_service_type(self) -> MusicServiceType:
        return MusicServiceType.SPOTIFY
    
    async def authenticate(self) -> bool:
        """Authenticate with Spotify using Client Credentials flow"""
        try:
            if not self.client_id or not self.client_secret:
                logger.error("Spotify client credentials not configured")
                return False
            
            # Create session
            self.session = aiohttp.ClientSession()
            
            # Get access token
            auth_url = "https://accounts.spotify.com/api/token"
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            async with self.session.post(auth_url, data=auth_data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now().timestamp() + expires_in
                    self.is_authenticated = True
                    logger.info("Spotify authentication successful")
                    return True
                else:
                    logger.error(f"Spotify authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Spotify: {e}")
            return False
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.is_authenticated or not self.access_token:
            await self.authenticate()
        elif self.token_expires_at and datetime.now().timestamp() >= self.token_expires_at:
            await self.authenticate()
    
    async def search(self, query: str, limit: int = 20, offset: int = 0) -> SearchResult:
        """Search Spotify for music content"""
        try:
            await self._ensure_authenticated()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "q": query,
                "type": "track,album,artist,playlist",
                "limit": limit,
                "offset": offset
            }
            
            async with self.session.get(f"{self.base_url}/search", headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_search_results(data)
                else:
                    logger.error(f"Spotify search failed: {response.status}")
                    return SearchResult([], [], [], [], 0, 0, 0, 0)
                    
        except Exception as e:
            logger.error(f"Error searching Spotify: {e}")
            return SearchResult([], [], [], [], 0, 0, 0, 0)
    
    def _parse_search_results(self, data: Dict[str, Any]) -> SearchResult:
        """Parse Spotify search results"""
        tracks = []
        albums = []
        artists = []
        playlists = []
        
        # Parse tracks
        if "tracks" in data:
            for item in data["tracks"].get("items", []):
                track = self._parse_track(item)
                if track:
                    tracks.append(track)
        
        # Parse albums
        if "albums" in data:
            for item in data["albums"].get("items", []):
                album = self._parse_album(item)
                if album:
                    albums.append(album)
        
        # Parse artists
        if "artists" in data:
            for item in data["artists"].get("items", []):
                artist = self._parse_artist(item)
                if artist:
                    artists.append(artist)
        
        # Parse playlists
        if "playlists" in data:
            for item in data["playlists"].get("items", []):
                playlist = self._parse_playlist(item)
                if playlist:
                    playlists.append(playlist)
        
        return SearchResult(
            tracks=tracks,
            albums=albums,
            artists=artists,
            playlists=playlists,
            total_tracks=data.get("tracks", {}).get("total", 0),
            total_albums=data.get("albums", {}).get("total", 0),
            total_artists=data.get("artists", {}).get("total", 0),
            total_playlists=data.get("playlists", {}).get("total", 0)
        )
    
    def _parse_track(self, data: Dict[str, Any]) -> Optional[Track]:
        """Parse Spotify track data"""
        try:
            return Track(
                id=data["id"],
                title=data["name"],
                artist=", ".join([artist["name"] for artist in data["artists"]]),
                album=data["album"]["name"],
                duration=data["duration_ms"] // 1000,
                service=MusicServiceType.SPOTIFY,
                external_url=data.get("external_urls", {}).get("spotify"),
                preview_url=data.get("preview_url"),
                image_url=data["album"].get("images", [{}])[0].get("url") if data["album"].get("images") else None,
                explicit=data.get("explicit", False),
                track_number=data.get("track_number"),
                disc_number=data.get("disc_number"),
                popularity=data.get("popularity"),
                isrc=data.get("external_ids", {}).get("isrc")
            )
        except Exception as e:
            logger.error(f"Error parsing Spotify track: {e}")
            return None
    
    def _parse_album(self, data: Dict[str, Any]) -> Optional[Album]:
        """Parse Spotify album data"""
        try:
            return Album(
                id=data["id"],
                title=data["name"],
                artist=", ".join([artist["name"] for artist in data["artists"]]),
                service=MusicServiceType.SPOTIFY,
                release_date=data.get("release_date"),
                total_tracks=data.get("total_tracks"),
                image_url=data.get("images", [{}])[0].get("url") if data.get("images") else None,
                external_url=data.get("external_urls", {}).get("spotify"),
                genres=data.get("genres"),
                popularity=data.get("popularity")
            )
        except Exception as e:
            logger.error(f"Error parsing Spotify album: {e}")
            return None
    
    def _parse_artist(self, data: Dict[str, Any]) -> Optional[Artist]:
        """Parse Spotify artist data"""
        try:
            return Artist(
                id=data["id"],
                name=data["name"],
                service=MusicServiceType.SPOTIFY,
                genres=data.get("genres"),
                popularity=data.get("popularity"),
                image_url=data.get("images", [{}])[0].get("url") if data.get("images") else None,
                external_url=data.get("external_urls", {}).get("spotify"),
                followers=data.get("followers", {}).get("total")
            )
        except Exception as e:
            logger.error(f"Error parsing Spotify artist: {e}")
            return None
    
    def _parse_playlist(self, data: Dict[str, Any]) -> Optional[Playlist]:
        """Parse Spotify playlist data"""
        try:
            return Playlist(
                id=data["id"],
                name=data["name"],
                description=data.get("description"),
                service=MusicServiceType.SPOTIFY,
                owner=data.get("owner", {}).get("display_name"),
                public=data.get("public", False),
                collaborative=data.get("collaborative", False),
                total_tracks=data.get("tracks", {}).get("total"),
                image_url=data.get("images", [{}])[0].get("url") if data.get("images") else None,
                external_url=data.get("external_urls", {}).get("spotify")
            )
        except Exception as e:
            logger.error(f"Error parsing Spotify playlist: {e}")
            return None
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get Spotify track details"""
        try:
            await self._ensure_authenticated()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(f"{self.base_url}/tracks/{track_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_track(data)
                else:
                    logger.error(f"Failed to get Spotify track: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Spotify track: {e}")
            return None
    
    async def get_album(self, album_id: str) -> Optional[Album]:
        """Get Spotify album details"""
        try:
            await self._ensure_authenticated()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(f"{self.base_url}/albums/{album_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_album(data)
                else:
                    logger.error(f"Failed to get Spotify album: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Spotify album: {e}")
            return None
    
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get Spotify artist details"""
        try:
            await self._ensure_authenticated()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(f"{self.base_url}/artists/{artist_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_artist(data)
                else:
                    logger.error(f"Failed to get Spotify artist: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Spotify artist: {e}")
            return None
    
    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get Spotify playlist details"""
        try:
            await self._ensure_authenticated()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(f"{self.base_url}/playlists/{playlist_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    playlist = self._parse_playlist(data)
                    
                    # Get tracks
                    if playlist and "tracks" in data:
                        tracks = []
                        for item in data["tracks"].get("items", []):
                            if "track" in item and item["track"]:
                                track = self._parse_track(item["track"])
                                if track:
                                    tracks.append(track)
                        playlist.tracks = tracks
                    
                    return playlist
                else:
                    logger.error(f"Failed to get Spotify playlist: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Spotify playlist: {e}")
            return None
    
    async def get_user_playlists(self) -> List[Playlist]:
        """Get user's Spotify playlists (requires user authentication)"""
        # This would require user authentication flow
        logger.warning("get_user_playlists requires user authentication - not implemented")
        return []
    
    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> Optional[Playlist]:
        """Create Spotify playlist (requires user authentication)"""
        # This would require user authentication flow
        logger.warning("create_playlist requires user authentication - not implemented")
        return None
    
    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Add tracks to Spotify playlist (requires user authentication)"""
        # This would require user authentication flow
        logger.warning("add_tracks_to_playlist requires user authentication - not implemented")
        return False
    
    async def remove_tracks_from_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Remove tracks from Spotify playlist (requires user authentication)"""
        # This would require user authentication flow
        logger.warning("remove_tracks_from_playlist requires user authentication - not implemented")
        return False
    
    async def get_track_audio_url(self, track_id: str) -> Optional[str]:
        """Get playable audio URL for Spotify track"""
        # Spotify doesn't provide direct audio URLs for playback
        # This would require Spotify Web Playback SDK or similar
        logger.warning("get_track_audio_url not available for Spotify - requires Web Playback SDK")
        return None


class LocalFileService(MusicService):
    """Local file music service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.music_directories = config.get("music_directories", ["~/Music", "~/Downloads"])
        self.supported_formats = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"}
        self.track_cache: Dict[str, Track] = {}
        self.scan_completed = False
    
    def _get_service_type(self) -> MusicServiceType:
        return MusicServiceType.LOCAL_FILES
    
    async def authenticate(self) -> bool:
        """Local files don't require authentication"""
        self.is_authenticated = True
        await self._scan_music_files()
        return True
    
    async def _scan_music_files(self):
        """Scan local directories for music files"""
        try:
            logger.info("Scanning local music files...")
            self.track_cache.clear()
            
            for directory in self.music_directories:
                expanded_dir = os.path.expanduser(directory)
                if os.path.exists(expanded_dir):
                    await self._scan_directory(expanded_dir)
            
            self.scan_completed = True
            logger.info(f"Found {len(self.track_cache)} local music files")
            
        except Exception as e:
            logger.error(f"Error scanning music files: {e}")
    
    async def _scan_directory(self, directory: str):
        """Recursively scan directory for music files"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(fmt) for fmt in self.supported_formats):
                        file_path = os.path.join(root, file)
                        track = await self._create_track_from_file(file_path)
                        if track:
                            self.track_cache[track.id] = track
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    async def _create_track_from_file(self, file_path: str) -> Optional[Track]:
        """Create Track object from local file"""
        try:
            # Get file info
            stat = os.stat(file_path)
            file_size = stat.st_size
            modified_time = stat.st_mtime
            
            # Try to get metadata
            title, artist, album = self._extract_metadata(file_path)
            
            # Create track ID from file path
            track_id = f"local_{hash(file_path)}"
            
            return Track(
                id=track_id,
                title=title or os.path.splitext(os.path.basename(file_path))[0],
                artist=artist or "Unknown Artist",
                album=album or "Unknown Album",
                duration=0,  # Would need to extract from file
                service=MusicServiceType.LOCAL_FILES,
                external_url=file_path
            )
            
        except Exception as e:
            logger.error(f"Error creating track from file {file_path}: {e}")
            return None
    
    def _extract_metadata(self, file_path: str) -> tuple:
        """Extract metadata from music file"""
        try:
            # Try to use mutagen for metadata extraction
            from mutagen import File
            
            audio_file = File(file_path)
            if audio_file is not None:
                title = audio_file.get("title", [None])[0]
                artist = audio_file.get("artist", [None])[0]
                album = audio_file.get("album", [None])[0]
                return title, artist, album
        except ImportError:
            logger.debug("mutagen not available for metadata extraction")
        except Exception as e:
            logger.debug(f"Error extracting metadata: {e}")
        
        return None, None, None
    
    async def search(self, query: str, limit: int = 20, offset: int = 0) -> SearchResult:
        """Search local music files"""
        try:
            if not self.scan_completed:
                await self._scan_music_files()
            
            query_lower = query.lower()
            matching_tracks = []
            
            for track in self.track_cache.values():
                if (query_lower in track.title.lower() or 
                    query_lower in track.artist.lower() or 
                    query_lower in track.album.lower()):
                    matching_tracks.append(track)
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            paginated_tracks = matching_tracks[start_idx:end_idx]
            
            return SearchResult(
                tracks=paginated_tracks,
                albums=[],  # Would need to group tracks by album
                artists=[],  # Would need to group tracks by artist
                playlists=[],  # Local playlists not implemented
                total_tracks=len(matching_tracks),
                total_albums=0,
                total_artists=0,
                total_playlists=0
            )
            
        except Exception as e:
            logger.error(f"Error searching local files: {e}")
            return SearchResult([], [], [], [], 0, 0, 0, 0)
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get local track details"""
        return self.track_cache.get(track_id)
    
    async def get_album(self, album_id: str) -> Optional[Album]:
        """Get local album details (not implemented)"""
        return None
    
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get local artist details (not implemented)"""
        return None
    
    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get local playlist details (not implemented)"""
        return None
    
    async def get_user_playlists(self) -> List[Playlist]:
        """Get local playlists (not implemented)"""
        return []
    
    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> Optional[Playlist]:
        """Create local playlist (not implemented)"""
        return None
    
    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Add tracks to local playlist (not implemented)"""
        return False
    
    async def remove_tracks_from_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Remove tracks from local playlist (not implemented)"""
        return False
    
    async def get_track_audio_url(self, track_id: str) -> Optional[str]:
        """Get local file path for track"""
        track = self.track_cache.get(track_id)
        return track.external_url if track else None


class MusicServiceManager:
    """Manages multiple music services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services: Dict[MusicServiceType, MusicService] = {}
        self.default_service = MusicServiceType.SPOTIFY
        
        # Initialize services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize available music services"""
        try:
            # Initialize Spotify
            if self.config.get("spotify_client_id") and self.config.get("spotify_client_secret"):
                self.services[MusicServiceType.SPOTIFY] = SpotifyService(self.config)
                logger.info("Spotify service initialized")
            
            # Initialize Local Files
            self.services[MusicServiceType.LOCAL_FILES] = LocalFileService(self.config)
            logger.info("Local files service initialized")
            
            # TODO: Initialize Apple Music, YouTube Music, etc.
            
        except Exception as e:
            logger.error(f"Error initializing music services: {e}")
    
    async def authenticate_all(self) -> Dict[MusicServiceType, bool]:
        """Authenticate with all services"""
        results = {}
        for service_type, service in self.services.items():
            try:
                results[service_type] = await service.authenticate()
            except Exception as e:
                logger.error(f"Error authenticating {service_type.value}: {e}")
                results[service_type] = False
        return results
    
    async def search_all(self, query: str, limit: int = 20) -> SearchResult:
        """Search across all services"""
        all_tracks = []
        all_albums = []
        all_artists = []
        all_playlists = []
        
        total_tracks = 0
        total_albums = 0
        total_artists = 0
        total_playlists = 0
        
        for service_type, service in self.services.items():
            if service.is_authenticated:
                try:
                    result = await service.search(query, limit)
                    all_tracks.extend(result.tracks)
                    all_albums.extend(result.albums)
                    all_artists.extend(result.artists)
                    all_playlists.extend(result.playlists)
                    
                    total_tracks += result.total_tracks
                    total_albums += result.total_albums
                    total_artists += result.total_artists
                    total_playlists += result.total_playlists
                    
                except Exception as e:
                    logger.error(f"Error searching {service_type.value}: {e}")
        
        return SearchResult(
            tracks=all_tracks,
            albums=all_albums,
            artists=all_artists,
            playlists=all_playlists,
            total_tracks=total_tracks,
            total_albums=total_albums,
            total_artists=total_artists,
            total_playlists=total_playlists
        )
    
    async def get_track(self, track_id: str, service_type: Optional[MusicServiceType] = None) -> Optional[Track]:
        """Get track from specific service or search all"""
        if service_type and service_type in self.services:
            return await self.services[service_type].get_track(track_id)
        
        # Search all services
        for service in self.services.values():
            if service.is_authenticated:
                track = await service.get_track(track_id)
                if track:
                    return track
        
        return None
    
    async def get_playable_url(self, track_id: str, service_type: Optional[MusicServiceType] = None) -> Optional[str]:
        """Get playable URL for track"""
        if service_type and service_type in self.services:
            return await self.services[service_type].get_track_audio_url(track_id)
        
        # Search all services
        for service in self.services.values():
            if service.is_authenticated:
                url = await service.get_track_audio_url(track_id)
                if url:
                    return url
        
        return None
    
    async def close_all(self):
        """Close all services"""
        for service in self.services.values():
            await service.close()
