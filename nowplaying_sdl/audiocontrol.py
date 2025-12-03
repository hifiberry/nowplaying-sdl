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
        
        song = data.get("song", {})
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
        cover_url = song.get("cover_art_url") or song.get("coverUrl") or song.get("artUrl")
        
        logger.debug(f"Formatted data - title: {song.get('title', '')}, artist: {song.get('artist', '')}, cover_url: {cover_url}")
        
        return {
            "artist": song.get("artist", ""),
            "title": song.get("title", ""),
            "album": song.get("album", ""),
            "cover_url": cover_url,
            "state": state,
            "position": data.get("position"),
            "duration": song.get("duration"),
            "player_name": player_name
        }
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get the most recent now playing data"""
        return self.current_data
    
    def _update_loop(self):
        """Background thread that polls for updates"""
        while self.running:
            raw_data = self.fetch_now_playing()
            self.current_data = self.format_now_playing(raw_data)
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
