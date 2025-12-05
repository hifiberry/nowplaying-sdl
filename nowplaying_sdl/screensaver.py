"""
Screensaver functionality with backlight control
"""

import logging
import time
import glob

logger = logging.getLogger(__name__)


class Screensaver:
    """Manages screen backlight dimming and power saving"""
    
    def __init__(self, brightness_off=0, brightness_dimmed=5, brightness_on=16,
                 dimming_timeout=60, off_timeout=600):
        """Initialize screensaver
        
        Args:
            brightness_off: Brightness level when off (default: 0)
            brightness_dimmed: Brightness level when dimmed (default: 5)
            brightness_on: Brightness level when fully on (default: 16)
            dimming_timeout: Seconds of inactivity before dimming (default: 60)
            off_timeout: Seconds of inactivity before turning off when stopped (default: 600)
        """
        self.brightness_off = brightness_off
        self.brightness_dimmed = brightness_dimmed
        self.brightness_on = brightness_on
        self.dimming_timeout = max(5, dimming_timeout)  # Minimum 5 seconds
        self.off_timeout = max(self.dimming_timeout + 5, off_timeout)  # Must be at least 5s after dimming
        
        self.backlight_device = self._find_backlight_device()
        self.current_brightness = None
        self.last_activity_time = time.time()
        
        if self.backlight_device:
            logger.info(f"Backlight device found: {self.backlight_device}")
            logger.info(f"Screensaver config: brightness_on={self.brightness_on}, brightness_dimmed={self.brightness_dimmed}, brightness_off={self.brightness_off}")
            logger.info(f"Screensaver timings: dimming_timeout={self.dimming_timeout}s, off_timeout={self.off_timeout}s")
            self.set_brightness(self.brightness_on)
        else:
            logger.warning("No backlight device found - screensaver will not work")
    
    def _find_backlight_device(self):
        """Find the backlight device file
        
        Returns:
            Path to backlight device file, or None if not found
        """
        backlight_files = glob.glob('/sys/class/backlight/*/brightness')
        if backlight_files:
            return backlight_files[0]
        return None
    
    def set_brightness(self, brightness):
        """Set backlight brightness
        
        Args:
            brightness: Brightness value to set
        
        Returns:
            True if successful, False otherwise
        """
        if self.backlight_device is None:
            return False
        
        if brightness == self.current_brightness:
            return True
        
        try:
            with open(self.backlight_device, 'w') as f:
                f.write(f"{brightness}\n")
            self.current_brightness = brightness
            logger.debug(f"Set backlight to {brightness} via {self.backlight_device}")
            return True
        except (PermissionError, IOError) as e:
            logger.warning(f"Failed to set backlight: {e}")
            return False
    
    def reset_activity(self):
        """Reset the inactivity timer (call on user interaction)"""
        logger.info("User activity detected, resetting screensaver timer")
        old_time = self.last_activity_time
        self.last_activity_time = time.time()
        logger.info(f"Activity timer reset (was {time.time() - old_time:.1f}s ago)")
        # Always restore full brightness on activity
        if self.current_brightness != self.brightness_on:
            logger.info(f"Restoring brightness to {self.brightness_on}")
        self.set_brightness(self.brightness_on)
    
    def update(self, is_playing=False):
        """Update screensaver state based on inactivity and playback status
        
        Args:
            is_playing: True if media is currently playing
        
        Returns:
            Current brightness level
        """
        if self.backlight_device is None:
            return self.brightness_on
        
        # Reset activity timer if playing
        if is_playing:
            self.last_activity_time = time.time()
        
        current_time = time.time()
        idle_time = current_time - self.last_activity_time
        target_brightness = self.brightness_on
        
        # Only apply screensaver rules if we've been idle for more than 1 second
        # This prevents immediate dimming on startup
        if idle_time > 1:
            # Dim after dimming timeout
            if idle_time >= self.dimming_timeout:
                target_brightness = self.brightness_dimmed
                
                # Turn off after off timeout, but only if not playing
                if idle_time >= self.off_timeout and not is_playing:
                    target_brightness = self.brightness_off
        
        # Update backlight if changed
        if target_brightness != self.current_brightness:
            if target_brightness == self.brightness_dimmed:
                logger.info(f"Dimming display to {target_brightness} after {idle_time:.0f}s of inactivity")
            elif target_brightness == self.brightness_off:
                logger.info(f"Turning off display (brightness={target_brightness}) after {idle_time:.0f}s of inactivity (playback stopped)")
            else:
                logger.info(f"Backlight changed to {target_brightness} (idle: {idle_time:.0f}s, playing: {is_playing})")
            self.set_brightness(target_brightness)
        
        return self.current_brightness
    
    def is_enabled(self):
        """Check if screensaver is enabled (backlight device available)
        
        Returns:
            True if screensaver can control backlight, False otherwise
        """
        return self.backlight_device is not None
