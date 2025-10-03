"""
Apple Music API Integration
Provides access to Apple Music catalog and user library
"""
import asyncio
import logging
import json
import base64
from typing import Dict, List, Optional, Any
import aiohttp
from datetime import datetime, timedelta

from music_service_abstraction import (
    MusicService, MusicServiceType, Track, Album, Artist, Playlist, SearchResult
)

logger = logging.getLogger(__name__)


class AppleMusicService(MusicService):
    """Apple Music API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.team_id = config.get("apple_music_team_id")
        self.key_id = config.get("apple_music_key_id")
        self.private_key = config.get("apple_music_private_key")
        self.storefront = config.get("apple_music_storefront", "us")
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://api.music.apple.com/v1"
        self.auth_url = "https://appleid.apple.com/auth/oauth2/token"
    
    def _get_service_type(self) -> MusicServiceType:
        return MusicServiceType.APPLE_MUSIC
    
    async def authenticate(self) -> bool:
        """Authenticate with Apple Music using JWT"""
        try:
            if not all([self.team_id, self.key_id, self.private_key]):
                logger.error("Apple Music credentials not configured")
                return False
            
            # Create session
            self.session = aiohttp.ClientSession()
            
            # Generate JWT token
            jwt_token = self._generate_jwt_token()
            
            # Exchange JWT for access token
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.team_id,
                "client_secret": jwt_token
            }
            
            async with self.session.post(self.auth_url, data=auth_data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    self.is_authenticated = True
                    logger.info("Apple Music authentication successful")
                    return True
                else:
                    logger.error(f"Apple Music authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Apple Music: {e}")
            return False
    
    def _generate_jwt_token(self) -> str:
        """Generate JWT token for Apple Music authentication"""
        try:
            import jwt
            
            # JWT header
            header = {
                "alg": "ES256",
                "kid": self.key_id
            }
            
            # JWT payload
            now = datetime.now()
            payload = {
                "iss": self.team_id,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(hours=1)).timestamp())
            }
            
            # Sign JWT
            token = jwt.encode(payload, self.private_key, algorithm="ES256", headers=header)
            return token
            
        except ImportError:
            logger.error("PyJWT not available for Apple Music authentication")
            return ""
        except Exception as e:
            logger.error(f"Error generating JWT token: {e}")
            return ""
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.is_authenticated or not self.access_token:
            await self.authenticate()
        elif self.token_expires_at and datetime.now() >= self.token_expires_at:
            await self.authenticate()
    
    async def search(self, query: str, limit: int = 20, offset: int = 0) -> SearchResult:
        """Search Apple Music catalog"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Music-User-Token": ""  # Would need user token for personal library
            }
            
            params = {
                "term": query,
                "limit": limit,
                "offset": offset,
                "types": "songs,albums,artists,playlists"
            }
            
            url = f"{self.base_url}/catalog/{self.storefront}/search"
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_search_results(data)
                else:
                    logger.error(f"Apple Music search failed: {response.status}")
                    return SearchResult([], [], [], [], 0, 0, 0, 0)
                    
        except Exception as e:
            logger.error(f"Error searching Apple Music: {e}")
            return SearchResult([], [], [], [], 0, 0, 0, 0)
    
    def _parse_search_results(self, data: Dict[str, Any]) -> SearchResult:
        """Parse Apple Music search results"""
        tracks = []
        albums = []
        artists = []
        playlists = []
        
        results = data.get("results", {})
        
        # Parse songs (tracks)
        if "songs" in results:
            for item in results["songs"].get("data", []):
                track = self._parse_track(item)
                if track:
                    tracks.append(track)
        
        # Parse albums
        if "albums" in results:
            for item in results["albums"].get("data", []):
                album = self._parse_album(item)
                if album:
                    albums.append(album)
        
        # Parse artists
        if "artists" in results:
            for item in results["artists"].get("data", []):
                artist = self._parse_artist(item)
                if artist:
                    artists.append(artist)
        
        # Parse playlists
        if "playlists" in results:
            for item in results["playlists"].get("data", []):
                playlist = self._parse_playlist(item)
                if playlist:
                    playlists.append(playlist)
        
        return SearchResult(
            tracks=tracks,
            albums=albums,
            artists=artists,
            playlists=playlists,
            total_tracks=results.get("songs", {}).get("meta", {}).get("total", 0),
            total_albums=results.get("albums", {}).get("meta", {}).get("total", 0),
            total_artists=results.get("artists", {}).get("meta", {}).get("total", 0),
            total_playlists=results.get("playlists", {}).get("meta", {}).get("total", 0)
        )
    
    def _parse_track(self, data: Dict[str, Any]) -> Optional[Track]:
        """Parse Apple Music track data"""
        try:
            attributes = data.get("attributes", {})
            
            return Track(
                id=data["id"],
                title=attributes.get("name", ""),
                artist=attributes.get("artistName", ""),
                album=attributes.get("albumName", ""),
                duration=int(attributes.get("durationInMillis", 0)) // 1000,
                service=MusicServiceType.APPLE_MUSIC,
                external_url=attributes.get("url"),
                preview_url=attributes.get("previews", [{}])[0].get("url") if attributes.get("previews") else None,
                image_url=self._get_image_url(attributes.get("artwork", {})),
                genre=attributes.get("genreNames", [None])[0] if attributes.get("genreNames") else None,
                year=int(attributes.get("releaseDate", "0")[:4]) if attributes.get("releaseDate") else None,
                track_number=attributes.get("trackNumber"),
                disc_number=attributes.get("discNumber"),
                popularity=attributes.get("popularity"),
                explicit=attributes.get("contentRating") == "explicit",
                isrc=attributes.get("isrc")
            )
        except Exception as e:
            logger.error(f"Error parsing Apple Music track: {e}")
            return None
    
    def _parse_album(self, data: Dict[str, Any]) -> Optional[Album]:
        """Parse Apple Music album data"""
        try:
            attributes = data.get("attributes", {})
            
            return Album(
                id=data["id"],
                title=attributes.get("name", ""),
                artist=attributes.get("artistName", ""),
                service=MusicServiceType.APPLE_MUSIC,
                release_date=attributes.get("releaseDate"),
                total_tracks=attributes.get("trackCount"),
                image_url=self._get_image_url(attributes.get("artwork", {})),
                external_url=attributes.get("url"),
                genres=attributes.get("genreNames"),
                popularity=attributes.get("popularity")
            )
        except Exception as e:
            logger.error(f"Error parsing Apple Music album: {e}")
            return None
    
    def _parse_artist(self, data: Dict[str, Any]) -> Optional[Artist]:
        """Parse Apple Music artist data"""
        try:
            attributes = data.get("attributes", {})
            
            return Artist(
                id=data["id"],
                name=attributes.get("name", ""),
                service=MusicServiceType.APPLE_MUSIC,
                genres=attributes.get("genreNames"),
                popularity=attributes.get("popularity"),
                image_url=self._get_image_url(attributes.get("artwork", {})),
                external_url=attributes.get("url")
            )
        except Exception as e:
            logger.error(f"Error parsing Apple Music artist: {e}")
            return None
    
    def _parse_playlist(self, data: Dict[str, Any]) -> Optional[Playlist]:
        """Parse Apple Music playlist data"""
        try:
            attributes = data.get("attributes", {})
            
            return Playlist(
                id=data["id"],
                name=attributes.get("name", ""),
                description=attributes.get("description", {}).get("standard") if attributes.get("description") else None,
                service=MusicServiceType.APPLE_MUSIC,
                owner=attributes.get("curatorName"),
                public=attributes.get("playParams", {}).get("isPublic", False),
                total_tracks=attributes.get("trackCount"),
                image_url=self._get_image_url(attributes.get("artwork", {})),
                external_url=attributes.get("url")
            )
        except Exception as e:
            logger.error(f"Error parsing Apple Music playlist: {e}")
            return None
    
    def _get_image_url(self, artwork: Dict[str, Any]) -> Optional[str]:
        """Get image URL from Apple Music artwork data"""
        try:
            if not artwork:
                return None
            
            # Apple Music provides artwork in different sizes
            # We'll use the largest available size
            width = artwork.get("width", 0)
            height = artwork.get("height", 0)
            
            if width and height:
                # Construct URL with size
                base_url = artwork.get("url", "")
                if base_url:
                    # Replace {w} and {h} placeholders
                    url = base_url.replace("{w}", str(width)).replace("{h}", str(height))
                    return url
            
            return artwork.get("url")
            
        except Exception as e:
            logger.error(f"Error getting image URL: {e}")
            return None
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get Apple Music track details"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Music-User-Token": ""
            }
            
            url = f"{self.base_url}/catalog/{self.storefront}/songs/{track_id}"
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and data["data"]:
                        return self._parse_track(data["data"][0])
                    return None
                else:
                    logger.error(f"Failed to get Apple Music track: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Apple Music track: {e}")
            return None
    
    async def get_album(self, album_id: str) -> Optional[Album]:
        """Get Apple Music album details"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Music-User-Token": ""
            }
            
            url = f"{self.base_url}/catalog/{self.storefront}/albums/{album_id}"
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and data["data"]:
                        return self._parse_album(data["data"][0])
                    return None
                else:
                    logger.error(f"Failed to get Apple Music album: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Apple Music album: {e}")
            return None
    
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get Apple Music artist details"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Music-User-Token": ""
            }
            
            url = f"{self.base_url}/catalog/{self.storefront}/artists/{artist_id}"
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and data["data"]:
                        return self._parse_artist(data["data"][0])
                    return None
                else:
                    logger.error(f"Failed to get Apple Music artist: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Apple Music artist: {e}")
            return None
    
    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get Apple Music playlist details"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Music-User-Token": ""
            }
            
            url = f"{self.base_url}/catalog/{self.storefront}/playlists/{playlist_id}"
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and data["data"]:
                        playlist = self._parse_playlist(data["data"][0])
                        
                        # Get tracks if available
                        if playlist and "relationships" in data["data"][0]:
                            tracks = []
                            tracks_data = data["data"][0]["relationships"].get("tracks", {}).get("data", [])
                            for track_data in tracks_data:
                                track = self._parse_track(track_data)
                                if track:
                                    tracks.append(track)
                            playlist.tracks = tracks
                        
                        return playlist
                    return None
                else:
                    logger.error(f"Failed to get Apple Music playlist: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Apple Music playlist: {e}")
            return None
    
    async def get_user_playlists(self) -> List[Playlist]:
        """Get user's Apple Music playlists (requires user authentication)"""
        # This would require user authentication with Music-User-Token
        logger.warning("get_user_playlists requires user authentication - not implemented")
        return []
    
    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> Optional[Playlist]:
        """Create Apple Music playlist (requires user authentication)"""
        # This would require user authentication with Music-User-Token
        logger.warning("create_playlist requires user authentication - not implemented")
        return None
    
    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Add tracks to Apple Music playlist (requires user authentication)"""
        # This would require user authentication with Music-User-Token
        logger.warning("add_tracks_to_playlist requires user authentication - not implemented")
        return False
    
    async def remove_tracks_from_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Remove tracks from Apple Music playlist (requires user authentication)"""
        # This would require user authentication with Music-User-Token
        logger.warning("remove_tracks_from_playlist requires user authentication - not implemented")
        return False
    
    async def get_track_audio_url(self, track_id: str) -> Optional[str]:
        """Get playable audio URL for Apple Music track"""
        # Apple Music doesn't provide direct audio URLs for playback
        # This would require Apple Music Web Playback SDK or similar
        logger.warning("get_track_audio_url not available for Apple Music - requires Web Playback SDK")
        return None
