#!/usr/bin/env python3
"""
Cover art cache and downloader for nowplaying-sdl
"""

import os
import urllib.request
import hashlib
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CoverArtCache:
    """Download and cache cover art images"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cover art cache
        
        Args:
            cache_dir: Directory to store cached images, or None for temp directory
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(tempfile.gettempdir()) / "nowplaying_sdl_cache"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL"""
        # Use hash of URL as filename to avoid filesystem issues
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        # Try to preserve file extension
        ext = ""
        if url.lower().endswith('.jpg') or url.lower().endswith('.jpeg'):
            ext = ".jpg"
        elif url.lower().endswith('.png'):
            ext = ".png"
        return self.cache_dir / f"{url_hash}{ext}"
    
    def get_cover(self, url: Optional[str]) -> Optional[str]:
        """
        Get cover art, downloading if necessary
        
        Args:
            url: URL of cover art image, or None
            
        Returns:
            Path to local file, or None if unavailable
        """
        if not url:
            logger.debug("No cover URL provided")
            return None
        
        logger.debug(f"Getting cover art for URL: {url}")
        
        # Check if already cached
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            logger.info(f"Cover art found in cache: {cache_path}")
            return str(cache_path)
        
        # Download the image
        logger.info(f"Downloading cover art from: {url}")
        try:
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'NowPlayingSDL/1.0'}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = response.read()
                logger.debug(f"Downloaded {len(data)} bytes")
                
                # Save to cache
                with open(cache_path, 'wb') as f:
                    f.write(data)
                
                logger.info(f"Cover art cached to: {cache_path}")
                return str(cache_path)
                
        except Exception as e:
            logger.error(f"Error downloading cover art from {url}: {e}")
            return None
    
    def clear_cache(self):
        """Remove all cached images"""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cover art cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
