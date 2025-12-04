#!/usr/bin/env python3
"""
AudioControl API Client
Fetches now playing information from HiFiBerry AudioControl API
"""

import json
import urllib.request
import urllib.error
import time
import threading
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AudioControlClient:
    """Client for fetching now playing data from HiFiBerry AudioControl API"""
    
    def __init__(self, api_url="http://localhost:1080/api", update_interval=1.0):
        """
        Initialize AudioControl client
        
        Args:
            api_url: Base URL of the AudioControl API
            update_interval: How often to poll for updates (seconds)
        """
        self.api_url = api_url.rstrip('/')
        self.update_interval = update_interval
        self.current_data = {}
        self.running = False
        self.thread = None
        self.error = None
        self.previous_song = None
        self.previous_state = None
        self.favorites_supported = None  # None=unknown, True=supported, False=not supported
        self.favorites_cache = None
        self.favorites_cache_time = 0
        
    def fetch_now_playing(self) -> Dict[str, Any]:
        """Fetch the current now playing information from the AudioControl API"""
        try:
            url = f"{self.api_url}/now-playing"
            logger.debug(f"Fetching now playing from: {url}")
            
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'NowPlayingSDL/1.0'}
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                logger.debug(f"API response: {result}")
                
                # Also fetch player information
                try:
                    player_url = f"{self.api_url}/players"
                    player_request = urllib.request.Request(
                        player_url,
                        headers={'User-Agent': 'NowPlayingSDL/1.0'}
                    )
                    with urllib.request.urlopen(player_request, timeout=5) as player_response:
                        player_data = json.loads(player_response.read().decode('utf-8'))
                        result["player_info"] = player_data
                        logger.debug(f"Player info: {player_data}")
                except Exception as e:
                    logger.debug(f"Could not fetch player info: {e}")
                
                self.error = None
                return result
                
        except urllib.error.HTTPError as e:
            self.error = f"HTTP Error: {e.code} {e.reason}"
            logger.error(self.error)
            return {"error": self.error}
        except urllib.error.URLError as e:
            self.error = f"Connection Error: {e.reason}"
            logger.error(self.error)
            return {"error": self.error}
        except json.JSONDecodeError as e:
            self.error = f"Invalid JSON response"
            logger.error(f"{self.error}: {e}")
            return {"error": self.error}
        except Exception as e:
            self.error = f"Error: {str(e)}"
            logger.error(self.error)
            return {"error": self.error}
    
    def format_now_playing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format raw API data into a normalized structure"""
        if "error" in data:
            return {
                "artist": "",
                "title": "",
                "album": "",
                "cover_url": None,
                "state": "error",
                "position": None,
                "duration": None,
                "player_name": None,
                "error": data["error"]
            }
        
        song = data.get("song")
        if song is None:
            song = {}
        
        state = data.get("state", "unknown")
        player_name = None
        
        # Get active player name
        player_info = data.get("player_info", {})
        if player_info:
            for player in player_info.get("players", []):
                if player.get("state") in ["playing", "paused"]:
                    player_name = player.get("name")
                    break
        
        # Get cover art URL if available (try multiple field names)
        cover_url = song.get("coverart_url") or song.get("cover_art_url") or song.get("coverUrl") or song.get("artUrl")
        
        # Clear data if stopped or paused
        if state.lower() in ["stopped", "paused"]:
            artist = ""
            title = ""
            album = ""
            cover_url = None
        else:
            artist = song.get("artist", "")
            title = song.get("title", "")
            album = song.get("album", "")
        
        logger.debug(f"Formatted data - title: {title}, artist: {artist}, cover_url: {cover_url}")
        
        # Check if this track is in favorites
        is_fav = self.is_favorite(title, artist) if title and artist else False
        
        return {
            "artist": artist,
            "title": title,
            "album": album,
            "cover_url": cover_url,
            "state": state,
            "position": data.get("position"),
            "duration": song.get("duration"),
            "player_name": player_name,
            "is_favorite": is_fav
        }
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get the most recent now playing data"""
        return self.current_data
    
    def _update_loop(self):
        """Background thread that polls for updates"""
        while self.running:
            raw_data = self.fetch_now_playing()
            new_data = self.format_now_playing(raw_data)
            
            # Check for changes
            current_song = (new_data.get('title'), new_data.get('artist'))
            current_state = new_data.get('state')
            
            if current_song != self.previous_song and current_song != ('', ''):
                logger.info(f"Now playing: {new_data.get('artist')} - {new_data.get('title')}")
                self.previous_song = current_song
            
            if current_state != self.previous_state:
                logger.info(f"Playback state changed: {self.previous_state} -> {current_state}")
                self.previous_state = current_state
            
            self.current_data = new_data
            time.sleep(self.update_interval)
    
    def start(self):
        """Start background polling"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        
        # Do initial fetch synchronously
        raw_data = self.fetch_now_playing()
        self.current_data = self.format_now_playing(raw_data)
    
    def stop(self):
        """Stop background polling"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def is_connected(self) -> bool:
        """Check if connection is working"""
        return self.error is None
    
    def get_favorites(self) -> Optional[Dict[str, Any]]:
        """Get list of favorites from the API"""
        # If we know favorites aren't supported, don't try
        if self.favorites_supported is False:
            return None
        
        # Use cache if fresh (within 2 seconds)
        current_time = time.time()
        if self.favorites_cache and (current_time - self.favorites_cache_time) < 2.0:
            return self.favorites_cache
        
        try:
            url = f"{self.api_url}/favourites"
            logger.debug(f"Fetching favorites from: {url}")
            
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'NowPlayingSDL/1.0'}
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                logger.debug(f"Favorites response: {result}")
                
                # Mark as supported and cache result
                self.favorites_supported = True
                self.favorites_cache = result
                self.favorites_cache_time = current_time
                return result
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Favorites endpoint not available
                if self.favorites_supported is None:
                    logger.info("Favorites API not available (404) - feature disabled")
                self.favorites_supported = False
            else:
                logger.error(f"HTTP error fetching favorites: {e.code} {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Error fetching favorites: {e}")
            return None
    
    def is_favorite(self, title: str, artist: str) -> bool:
        """Check if the current track is in favorites
        
        Args:
            title: Song title
            artist: Song artist
        
        Returns:
            True if the track is in favorites, False otherwise
        """
        # Return False if API not supported
        if self.favorites_supported is False:
            return False
        
        if not title or not artist:
            return False
        
        favorites = self.get_favorites()
        if not favorites or "favourites" not in favorites:
            return False
        
        # Check if current track is in favorites list
        for fav in favorites["favourites"]:
            if fav.get("title") == title and fav.get("artist") == artist:
                return True
        
        return False
    
    def add_favorite(self, title: str, artist: str, album: str = None) -> bool:
        """Add current track to favorites
        
        Args:
            title: Song title
            artist: Song artist
            album: Song album (optional)
        
        Returns:
            True if successful, False otherwise
        """
        # Return False if API not supported
        if self.favorites_supported is False:
            return False
        
        if not title or not artist:
            logger.warning("Cannot add favorite: missing title or artist")
            return False
        
        try:
            url = f"{self.api_url}/favourites/add"
            logger.info(f"Adding to favorites: {artist} - {title}")
            
            # Prepare the data
            data = {
                "title": title,
                "artist": artist
            }
            if album:
                data["album"] = album
            
            json_data = json.dumps(data).encode('utf-8')
            
            request = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'User-Agent': 'NowPlayingSDL/1.0',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                logger.info(f"Added to favorites: {response.status}")
                # Invalidate cache
                self.favorites_cache = None
                self.favorites_supported = True
                return response.status == 200
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                if self.favorites_supported is None:
                    logger.info("Favorites API not available (404) - feature disabled")
                self.favorites_supported = False
            else:
                logger.error(f"HTTP error adding to favorites: {e.code} {e.reason}")
            return False
        except Exception as e:
            logger.error(f"Error adding to favorites: {e}")
            return False
    
    def remove_favorite(self, title: str, artist: str) -> bool:
        """Remove track from favorites
        
        Args:
            title: Song title
            artist: Song artist
        
        Returns:
            True if successful, False otherwise
        """
        # Return False if API not supported
        if self.favorites_supported is False:
            return False
        
        if not title or not artist:
            logger.warning("Cannot remove favorite: missing title or artist")
            return False
        
        try:
            url = f"{self.api_url}/favourites/remove"
            logger.info(f"Removing from favorites: {artist} - {title}")
            
            # Prepare the data
            data = {
                "title": title,
                "artist": artist
            }
            
            json_data = json.dumps(data).encode('utf-8')
            
            request = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'User-Agent': 'NowPlayingSDL/1.0',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                logger.info(f"Removed from favorites: {response.status}")
                # Invalidate cache
                self.favorites_cache = None
                self.favorites_supported = True
                return response.status == 200
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                if self.favorites_supported is None:
                    logger.info("Favorites API not available (404) - feature disabled")
                self.favorites_supported = False
            else:
                logger.error(f"HTTP error removing from favorites: {e.code} {e.reason}")
            return False
        except Exception as e:
            logger.error(f"Error removing from favorites: {e}")
            return False
    
    def toggle_favorite(self, title: str, artist: str, album: str = None) -> bool:
        """Toggle favorite status of current track
        
        Args:
            title: Song title
            artist: Song artist
            album: Song album (optional)
        
        Returns:
            True if now favorited, False if unfavorited or error
        """
        if self.is_favorite(title, artist):
            self.remove_favorite(title, artist)
            return False
        else:
            self.add_favorite(title, artist, album)
            return True
