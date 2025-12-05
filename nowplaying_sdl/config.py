#!/usr/bin/env python3
"""
Configuration file handler for nowplaying-sdl
"""

import os
import configparser
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Config:
    """Handle configuration from file and command-line arguments"""
    
    # Default config file locations
    SYSTEM_CONFIG = "/etc/nowplaying_sdl.conf"
    USER_CONFIG = "~/.config/nowplaying_sdl.conf"
    
    # Default values
    DEFAULTS = {
        'api_url': 'http://localhost:1080/api',
        'poll_interval': '2.0',
        'demo': 'false'
    }
    
    DISPLAY_DEFAULTS = {
        'display': '0',
        'rotation': '0'
    }
    
    UI_DEFAULTS = {
        'portrait': 'false',
        'landscape': 'false',
        'circle': 'false',
        'circle2': 'false',
        'bw_buttons': 'false',
        'no_control': 'false',
        'minimal_buttons': 'false',
        'round_controls': 'false',
        'volume_slider': 'false',
        'left_button': 'none',
        'liked': 'false'
    }
    
    SCREENSAVER_DEFAULTS = {
        'brightness_off': '0',
        'brightness_dimmed': '5',
        'brightness_on': '16',
        'dimming': '60',
        'off': '600'
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to config file, or None to auto-detect
        """
        self.config_file = self._find_config_file(config_file)
        self.config = self._load_config()
    
    def _find_config_file(self, config_file: Optional[str]) -> Optional[str]:
        """Find config file in order of preference"""
        if config_file:
            # Explicit config file specified
            if os.path.exists(config_file):
                return config_file
            else:
                logger.warning(f"Config file {config_file} not found")
                return None
        
        # Check if running as root
        if os.geteuid() == 0:
            if os.path.exists(self.SYSTEM_CONFIG):
                return self.SYSTEM_CONFIG
        
        # Check user config
        user_config = os.path.expanduser(self.USER_CONFIG)
        if os.path.exists(user_config):
            return user_config
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config = configparser.ConfigParser()
        
        # Set defaults
        config['DEFAULT'] = self.DEFAULTS
        
        # Create display section with defaults
        config['display'] = self.DISPLAY_DEFAULTS.copy()
        
        # Create ui section with defaults
        config['ui'] = self.UI_DEFAULTS.copy()
        
        # Create screensaver section with defaults
        config['screensaver'] = self.SCREENSAVER_DEFAULTS.copy()
        
        if self.config_file:
            try:
                config.read(self.config_file)
                logger.info(f"Loaded config from: {self.config_file}")
            except Exception as e:
                logger.error(f"Error reading config file {self.config_file}: {e}")
        
        return configception as e:
                logger.error(f"Error reading config file {self.config_file}: {e}")
        
        return configception as e:
                logger.error(f"Error reading config file {self.config_file}: {e}")
        
        return config
    
    def get(self, key: str, section: str = 'nowplaying') -> Any:
        """Get configuration value"""
        try:
            if section in self.config and key in self.config[section]:
                return self.config[section][key]
            elif key in self.config['DEFAULT']:
                return self.config['DEFAULT'][key]
        except Exception:
            pass
        return self.DEFAULTS.get(key, '')
    
    def get_int(self, key: str, section: str = 'nowplaying') -> int:
        """Get integer configuration value"""
        try:
            return int(self.get(key, section))
        except (ValueError, TypeError):
            return int(self.DEFAULTS.get(key, 0))
    
    def get_bool(self, key: str, section: str = 'nowplaying') -> bool:
        """Get boolean configuration value"""
        value = self.get(key, section).lower()
        return value in ('true', 'yes', '1', 'on')
    
    def get_float(self, key: str, section: str = 'nowplaying') -> float:
        """Get float configuration value"""
        try:
            return float(self.get(key, section))
        except (ValueError, TypeError):
            return float(self.DEFAULTS.get(key, 0.0))
    
    def merge_args(self, args) -> None:
        """Merge command-line arguments into config (args take precedence)"""
        # Command-line args override config file
        if hasattr(args, 'display') and args.display != int(self.DEFAULTS['display']):
            self.config['nowplaying']['display'] = str(args.display)
        if hasattr(args, 'rotation') and args.rotation != int(self.DEFAULTS['rotation']):
            self.config['nowplaying']['rotation'] = str(args.rotation)
        if hasattr(args, 'api_url') and args.api_url != self.DEFAULTS['api_url']:
            self.config['nowplaying']['api_url'] = args.api_url
        if hasattr(args, 'portrait') and args.portrait:
            self.config['nowplaying']['portrait'] = 'true'
        if hasattr(args, 'landscape') and args.landscape:
            self.config['nowplaying']['landscape'] = 'true'
        if hasattr(args, 'bw_buttons') and args.bw_buttons:
            self.config['nowplaying']['bw_buttons'] = 'true'
        if hasattr(args, 'no_control') and args.no_control:
            self.config['nowplaying']['no_control'] = 'true'
        if hasattr(args, 'minimal_buttons') and args.minimal_buttons:
            self.config['nowplaying']['minimal_buttons'] = 'true'
        if hasattr(args, 'liked') and args.liked:
            self.config['nowplaying']['liked'] = 'true'
        if hasattr(args, 'demo') and args.demo:
            self.config['nowplaying']['demo'] = 'true'
