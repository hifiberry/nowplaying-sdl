#!/usr/bin/env python3
"""
Simple Python program to display screen size using SDL (PySDL2)
"""

import sdl2
import sys


def get_screen_size():
    """Initialize SDL and get the screen size"""
    # Initialize SDL
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(f"Error initializing SDL: {sdl2.SDL_GetError()}")
        return None
    
    try:
        # Get the number of video displays
        num_displays = sdl2.SDL_GetNumVideoDisplays()
        
        if num_displays < 1:
            print(f"Error getting display count: {sdl2.SDL_GetError()}")
            return None
        
        print(f"Number of displays: {num_displays}\n")
        
        # Get information for each display
        for i in range(num_displays):
            mode = sdl2.SDL_DisplayMode()
            
            # Get the desktop display mode
            if sdl2.SDL_GetDesktopDisplayMode(i, mode) != 0:
                print(f"Error getting display mode for display {i}: {sdl2.SDL_GetError()}")
                continue
            
            print(f"Display {i}:")
            print(f"  Resolution: {mode.w} x {mode.h}")
            print(f"  Refresh rate: {mode.refresh_rate} Hz")
            print(f"  Format: {sdl2.SDL_GetPixelFormatName(mode.format).decode('utf-8')}")
            
            # Get display bounds
            rect = sdl2.SDL_Rect()
            if sdl2.SDL_GetDisplayBounds(i, rect) == 0:
                print(f"  Position: ({rect.x}, {rect.y})")
            
            print()
        
        return True
        
    finally:
        # Clean up SDL
        sdl2.SDL_Quit()


def main():
    """Main function"""
    print("SDL Screen Size Detection")
    print("=" * 40)
    print()
    
    result = get_screen_size()
    
    if result is None:
        sys.exit(1)
    
    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
