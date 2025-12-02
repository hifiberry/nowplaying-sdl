#!/usr/bin/env python3
"""
Now Playing Display - Shows currently playing media on SDL screen
"""

import sdl2
import sdl2.ext
import sdl2.sdlttf as sdlttf
import sdl2.sdlimage as sdlimage
import sys
import argparse
import os
from renderer import (
    draw_rounded_rect,
    render_text,
    render_text_centered,
    wrap_text,
    truncate_text,
    render_wrapped_text_centered
)


def render_coverart(renderer, x, y, size, imagefile, font_icons, rotation=0, screen_width=0, screen_height=0):
    """Render album cover art or placeholder
    
    Args:
        renderer: SDL2 renderer
        x, y: Top-left position
        size: Width and height of the cover square
        imagefile: Path to cover image file, or None for placeholder
        font_icons: Material Icons font for placeholder icon
        rotation: Rotation angle in degrees
        screen_width, screen_height: Physical screen dimensions
    """
    # Draw background square
    draw_rounded_rect(renderer, x, y, size, size, 20, 100, 100, 100, 255, rotation, screen_width, screen_height)
    
    if imagefile and os.path.exists(imagefile):
        # Load and render the image
        surface = sdlimage.IMG_Load(imagefile.encode('utf-8'))
        if surface:
            texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
            if texture:
                # Transform coordinates for rotation if needed
                if rotation in [90, 270]:
                    # Transform layout coordinates to screen coordinates
                    if rotation == 90:
                        screen_x = screen_width - (y + size)
                        screen_y = x
                    else:  # 270
                        screen_x = y
                        screen_y = screen_height - (x + size)
                    
                    # Create rect in screen coordinates
                    rect = sdl2.SDL_Rect(screen_x, screen_y, size, size)
                    center = sdl2.SDL_Point(size // 2, size // 2)
                    sdl2.SDL_RenderCopyEx(renderer, texture, None, rect, rotation, center, sdl2.SDL_FLIP_NONE)
                else:
                    rect = sdl2.SDL_Rect(x, y, size, size)
                    if rotation == 180:
                        center = sdl2.SDL_Point(size // 2, size // 2)
                        sdl2.SDL_RenderCopyEx(renderer, texture, None, rect, rotation, center, sdl2.SDL_FLIP_NONE)
                    else:
                        sdl2.SDL_RenderCopy(renderer, texture, None, rect)
                
                sdl2.SDL_DestroyTexture(texture)
            sdl2.SDL_FreeSurface(surface)
    else:
        # Draw placeholder icon (larger size)
        album_icon = "album"
        # Use a larger font size for the icon - scale with cover size
        icon_size = int(size * 0.4)  # 40% of cover size
        font_icons_large = sdlttf.TTF_OpenFont(b"/home/matuschd/nowplaying-sdl/MaterialIcons-Regular.ttf", icon_size)
        if font_icons_large:
            render_text_centered(renderer, font_icons_large, album_icon, 
                               x + size // 2, y + size // 2, 200, 200, 200, rotation, screen_width, screen_height)
            sdlttf.TTF_CloseFont(font_icons_large)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Now Playing Display - Shows currently playing media'
    )
    parser.add_argument(
        '--display',
        type=int,
        default=0,
        help='Display number to use (default: 0)'
    )
    orientation_group = parser.add_mutually_exclusive_group()
    orientation_group.add_argument(
        '--portrait',
        action='store_true',
        help='Force portrait orientation'
    )
    orientation_group.add_argument(
        '--landscape',
        action='store_true',
        help='Force landscape orientation'
    )
    parser.add_argument(
        '--bw-buttons',
        action='store_true',
        help='Use black and white buttons instead of colored'
    )
    parser.add_argument(
        '--no-control',
        action='store_true',
        help='Hide play/pause/next/prev buttons, only show like button'
    )
    parser.add_argument(
        '--minimal-buttons',
        action='store_true',
        help='Render buttons without background rectangles and increase icon size by 20%%'
    )
    parser.add_argument(
        '--liked',
        action='store_true',
        help='Show filled heart icon (default: unfilled border)'
    )
    parser.add_argument(
        '--rotation',
        type=int,
        choices=[0, 90, 180, 270],
        default=0,
        help='Rotation angle in degrees (0, 90, 180, or 270)'
    )
    return parser.parse_args()


def get_display_info(display_index):
    """Get information about a specific display"""
    mode = sdl2.SDL_DisplayMode()
    
    if sdl2.SDL_GetDesktopDisplayMode(display_index, mode) != 0:
        print(f"Error getting display mode: {sdl2.SDL_GetError()}")
        return None
    
    return mode


def draw_now_playing_ui_landscape(renderer, width, height, font_large, font_medium, font_icons, bw_buttons=False, no_control=False, minimal_buttons=False, liked=False, rotation=0, screen_width=0, screen_height=0):
    """Draw the Now Playing UI in landscape orientation
    
    Args:
        width, height: Layout dimensions (may be swapped for rotation)
        screen_width, screen_height: Physical screen dimensions
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    # Layout customization constants
    TEXT_VERTICAL_OFFSET_PERCENT = 0.10  # Move text down by 10% of height
    BUTTON_VERTICAL_OFFSET_PERCENT = -0.10  # Move buttons up by 10% of height (negative = up)
    
    # Clear screen to light gray background
    sdl2.SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255)
    sdl2.SDL_RenderClear(renderer)
    
    # Calculate layout
    padding = 40
    cover_size = min(width // 2 - padding * 2, height - padding * 2)
    cover_x = padding
    cover_y = (height - cover_size) // 2
    
    button_rects = {}
    
    # Render album cover (with demo image)
    render_coverart(renderer, cover_x, cover_y, cover_size, "demo_cover.jpg", font_icons, rotation, screen_width, screen_height)
    
    # Right side content area
    content_x = cover_x + cover_size + padding * 2
    content_y = padding * 2
    content_width = width - content_x - padding
    content_center_x = content_x + content_width // 2
    
    # Song title (centered) - wrap to max 40% display width
    title = "Never Gonna Give You Up"
    max_text_width = int(width * 0.4)
    wrapped_title = wrap_text(font_large, title, max_text_width)
    if len(wrapped_title) > 2:
        # Truncate to 2 lines with ellipsis
        wrapped_title = wrapped_title[:2]
        if len(wrapped_title[1]) > 0:
            wrapped_title[1] = wrapped_title[1][:-3] + "..." if len(wrapped_title[1]) > 3 else wrapped_title[1] + "..."
    
    title_y = content_y + 28 + int(height * TEXT_VERTICAL_OFFSET_PERCENT)
    for i, line in enumerate(wrapped_title):
        render_text_centered(renderer, font_large, line, content_center_x, title_y + i * 60, 30, 30, 30, rotation, screen_width, screen_height)
    
    # Artist name (centered) - wrap to max 40% display width
    artist = "Rick Astley"
    wrapped_artist = wrap_text(font_medium, artist, max_text_width)
    if len(wrapped_artist) > 2:
        wrapped_artist = wrapped_artist[:2]
        if len(wrapped_artist[1]) > 0:
            wrapped_artist[1] = wrapped_artist[1][:-3] + "..." if len(wrapped_artist[1]) > 3 else wrapped_artist[1] + "..."
    
    artist_y = content_y + 105 + (len(wrapped_title) - 1) * 60 + int(height * TEXT_VERTICAL_OFFSET_PERCENT)
    for i, line in enumerate(wrapped_artist):
        render_text_centered(renderer, font_medium, line, content_center_x, artist_y + i * 50, 100, 100, 100, rotation, screen_width, screen_height)
    
    # Control buttons area - align bottom of buttons with bottom of cover
    button_size = 100
    button_spacing = 25
    button_y = cover_y + cover_size - button_size + int(height * BUTTON_VERTICAL_OFFSET_PERCENT)
    
    # Determine button colors
    if bw_buttons:
        prev_color = (80, 80, 80)
        play_color = (80, 80, 80)
        next_color = (80, 80, 80)
        like_color = (80, 80, 80)
    else:
        prev_color = (60, 60, 60)
        play_color = (30, 150, 30)
        next_color = (60, 60, 60)
        like_color = (200, 50, 50)
    
    # Load larger icon font if minimal buttons (use regular MaterialIcons for thinner lines)
    if minimal_buttons:
        font_icons_buttons = sdlttf.TTF_OpenFont(b"/home/matuschd/nowplaying-sdl/MaterialIcons-Regular.ttf", int(48 * 1.5))
    else:
        font_icons_buttons = font_icons
    
    if no_control:
        # Only show like button, centered (filled if liked, border if not)
        like_icon = "favorite" if liked else "favorite_border"
        like_x = content_x + (content_width - button_size) // 2
        if not minimal_buttons:
            draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 40, *like_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, *like_color, rotation, screen_width, screen_height)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    else:
        # Calculate button positions to center them
        total_buttons_width = button_size * 4 + button_spacing * 3
        buttons_start_x = content_x + (content_width - total_buttons_width) // 2
        
        # Previous button (skip_previous icon)
        prev_x = buttons_start_x
        if not minimal_buttons:
            draw_rounded_rect(renderer, prev_x, button_y, button_size, button_size, 40, *prev_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "skip_previous", prev_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "skip_previous", prev_x + button_size // 2, button_y + button_size // 2, *prev_color, rotation, screen_width, screen_height)
        button_rects['prev'] = (prev_x, button_y, button_size, button_size)
        
        # Play/Pause button (play_arrow icon)
        play_x = prev_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, play_x, button_y, button_size, button_size, 40, *play_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "play_arrow", play_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "play_arrow", play_x + button_size // 2, button_y + button_size // 2, *play_color, rotation, screen_width, screen_height)
        button_rects['play'] = (play_x, button_y, button_size, button_size)
        
        # Next button (skip_next icon)
        next_x = play_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, next_x, button_y, button_size, button_size, 40, *next_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "skip_next", next_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "skip_next", next_x + button_size // 2, button_y + button_size // 2, *next_color, rotation, screen_width, screen_height)
        button_rects['next'] = (next_x, button_y, button_size, button_size)
        
        # Like button (favorite icon - filled if liked, border if not)
        like_icon = "favorite" if liked else "favorite_border"
        like_x = next_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 40, *like_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, *like_color, rotation, screen_width, screen_height)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    
    if minimal_buttons and font_icons_buttons != font_icons:
        sdlttf.TTF_CloseFont(font_icons_buttons)
    
    return button_rects


def draw_now_playing_ui_portrait(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons=False, no_control=False, minimal_buttons=False, liked=False, rotation=0, screen_width=0, screen_height=0):
    """Draw the Now Playing UI in portrait orientation
    
    Args:
        width, height: Layout dimensions (may be swapped for rotation)
        screen_width, screen_height: Physical screen dimensions
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    
    # Clear screen to light gray background
    sdl2.SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255)
    sdl2.SDL_RenderClear(renderer)
    
    # Calculate layout with 5% vertical offset
    vertical_offset = int(height * 0.05)
    padding = 30
    cover_size = min(width - padding * 2, (height - padding * 4) // 2)
    cover_x = (width - cover_size) // 2
    cover_y = padding + vertical_offset
    
    button_rects = {}
    
    # Render album cover (with demo image)
    render_coverart(renderer, cover_x, cover_y, cover_size, "demo_cover.jpg", font_icons, rotation, screen_width, screen_height)
    
    # Content area below cover
    content_y = cover_y + cover_size + padding + int(height * 0.05)  # Move 5% down
    content_x = padding
    max_text_width = int(width * 0.90)  # 90% of width
    center_x = width // 2
    
    # Song title (centered, wrapped to max 2 lines)
    title = "Never Gonna Give You Up"
    title_height = render_wrapped_text_centered(renderer, font_large, title, center_x, content_y, max_text_width, 30, 30, 30, max_lines=2, rotation=rotation, width=screen_width, height=screen_height)
    
    # Artist name (centered, single line with truncation)
    artist = "Rick Astley"
    artist_text = truncate_text(font_medium, artist, max_text_width)
    render_text_centered(renderer, font_medium, artist_text, center_x, content_y + title_height + 20, 100, 100, 100, rotation, screen_width, screen_height)
    
    # Control buttons area
    button_y = content_y + title_height + 150
    button_size = 90
    button_spacing = 20
    
    # Determine button colors
    if bw_buttons:
        prev_color = (80, 80, 80)
        play_color = (80, 80, 80)
        next_color = (80, 80, 80)
        like_color = (80, 80, 80)
    else:
        prev_color = (60, 60, 60)
        play_color = (30, 150, 30)
        next_color = (60, 60, 60)
        like_color = (200, 50, 50)
    
    # Load larger icon font if minimal buttons (use regular MaterialIcons for thinner lines)
    if minimal_buttons:
        font_icons_buttons = sdlttf.TTF_OpenFont(b"/home/matuschd/nowplaying-sdl/MaterialIcons-Regular.ttf", int(48 * 1.5))
    else:
        font_icons_buttons = font_icons
    
    if no_control:
        # Only show like button, centered (filled if liked, border if not)
        like_icon = "favorite" if liked else "favorite_border"
        like_x = (width - button_size) // 2
        if not minimal_buttons:
            draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 35, *like_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, *like_color, rotation, screen_width, screen_height)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    else:
        # Calculate button positions to center them
        total_buttons_width = button_size * 4 + button_spacing * 3
        buttons_start_x = (width - total_buttons_width) // 2
        
        # Previous button (skip_previous icon)
        prev_x = buttons_start_x
        if not minimal_buttons:
            draw_rounded_rect(renderer, prev_x, button_y, button_size, button_size, 35, *prev_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "skip_previous", prev_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "skip_previous", prev_x + button_size // 2, button_y + button_size // 2, *prev_color, rotation, screen_width, screen_height)
        button_rects['prev'] = (prev_x, button_y, button_size, button_size)
        
        # Play/Pause button (play_arrow icon)
        play_x = prev_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, play_x, button_y, button_size, button_size, 35, *play_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "play_arrow", play_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "play_arrow", play_x + button_size // 2, button_y + button_size // 2, *play_color, rotation, screen_width, screen_height)
        button_rects['play'] = (play_x, button_y, button_size, button_size)
        
        # Next button (skip_next icon)
        next_x = play_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, next_x, button_y, button_size, button_size, 35, *next_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "skip_next", next_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "skip_next", next_x + button_size // 2, button_y + button_size // 2, *next_color, rotation, screen_width, screen_height)
        button_rects['next'] = (next_x, button_y, button_size, button_size)
        
        # Like button (favorite icon - filled if liked, border if not)
        like_icon = "favorite" if liked else "favorite_border"
        like_x = next_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 35, *like_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, like_icon, like_x + button_size // 2, button_y + button_size // 2, *like_color, rotation, screen_width, screen_height)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    
    if minimal_buttons and font_icons_buttons != font_icons:
        sdlttf.TTF_CloseFont(font_icons_buttons)
    
    return button_rects


def draw_now_playing_ui(renderer, width, height, font_large, font_medium, font_small, font_icons, is_portrait, bw_buttons=False, no_control=False, minimal_buttons=False, liked=False, rotation=0, screen_width=0, screen_height=0):
    """Draw the Now Playing UI based on orientation
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    if is_portrait:
        return draw_now_playing_ui_portrait(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons, no_control, minimal_buttons, liked, rotation, screen_width, screen_height)
    else:
        return draw_now_playing_ui_landscape(renderer, width, height, font_large, font_medium, font_icons, bw_buttons, no_control, minimal_buttons, liked, rotation, screen_width, screen_height)


def main():
    """Main application entry point"""
    args = parse_arguments()
    
    # Initialize SDL
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(f"Error initializing SDL: {sdl2.SDL_GetError()}")
        return 1
    
    # Initialize SDL_ttf
    if sdlttf.TTF_Init() != 0:
        print(f"Error initializing SDL_ttf: {sdlttf.TTF_GetError()}")
        sdl2.SDL_Quit()
        return 1
    
    # Initialize SDL_image
    img_flags = sdlimage.IMG_INIT_JPG | sdlimage.IMG_INIT_PNG
    if sdlimage.IMG_Init(img_flags) != img_flags:
        print(f"Error initializing SDL_image: {sdlimage.IMG_GetError()}")
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()
        return 1
    
    try:
        # Get number of displays
        num_displays = sdl2.SDL_GetNumVideoDisplays()
        
        if num_displays < 1:
            print(f"Error: No displays found: {sdl2.SDL_GetError()}")
            return 1
        
        # Validate display index
        if args.display < 0 or args.display >= num_displays:
            print(f"Error: Display {args.display} not found. Available displays: 0-{num_displays-1}")
            return 1
        
        # Get display information
        display_mode = get_display_info(args.display)
        if display_mode is None:
            return 1
        
        # Determine orientation
        screen_is_portrait = display_mode.h > display_mode.w
        
        # Determine base orientation (before rotation)
        if args.portrait:
            base_is_portrait = True
            orientation_str = "portrait (forced)"
        elif args.landscape:
            base_is_portrait = False
            orientation_str = "landscape (forced)"
        else:
            # Auto-detect based on display resolution
            base_is_portrait = screen_is_portrait
            orientation_str = "portrait (auto)" if base_is_portrait else "landscape (auto)"
        
        # Validate base orientation matches screen (before rotation)
        if base_is_portrait != screen_is_portrait:
            screen_orientation = "portrait" if screen_is_portrait else "landscape"
            desired_orientation = "portrait" if base_is_portrait else "landscape"
            print(f"Error: Screen is {screen_orientation} ({display_mode.w}x{display_mode.h}) but {desired_orientation} mode was requested.")
            print(f"Please use --{'portrait' if screen_is_portrait else 'landscape'} or allow auto-detection.")
            return 1
        
        # Apply rotation: 90° and 270° flip the orientation for rendering
        is_portrait = base_is_portrait
        if args.rotation in (90, 270):
            is_portrait = not is_portrait
            orientation_str += f" + rotated {args.rotation}°"
        
        print(f"Using display {args.display}: {display_mode.w}x{display_mode.h} @ {display_mode.refresh_rate}Hz ({orientation_str})")
        
        # Get display bounds to position window on correct display
        bounds = sdl2.SDL_Rect()
        if sdl2.SDL_GetDisplayBounds(args.display, bounds) != 0:
            print(f"Error getting display bounds: {sdl2.SDL_GetError()}")
            return 1
        
        # Create window on the specified display
        window = sdl2.SDL_CreateWindow(
            b"Now Playing",
            bounds.x,  # Position on the specified display
            bounds.y,
            display_mode.w,
            display_mode.h,
            sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP
        )
        
        if not window:
            print(f"Error creating window: {sdl2.SDL_GetError()}")
            return 1
        
        # Create renderer
        renderer = sdl2.SDL_CreateRenderer(
            window,
            -1,
            sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
        )
        
        if not renderer:
            print(f"Error creating renderer: {sdl2.SDL_GetError()}")
            sdl2.SDL_DestroyWindow(window)
            return 1
        
        # Load fonts
        font_large = sdlttf.TTF_OpenFont(b"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = sdlttf.TTF_OpenFont(b"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        font_small = sdlttf.TTF_OpenFont(b"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_icons = sdlttf.TTF_OpenFont(b"/home/matuschd/nowplaying-sdl/MaterialSymbolsRounded.ttf", 48)
        
        if not font_large or not font_medium or not font_small or not font_icons:
            print(f"Error loading fonts: {sdlttf.TTF_GetError()}")
        # Main loop
        running = True
        event = sdl2.SDL_Event()
        
        # Draw initial frame to get button positions (use list to make it mutable in closure)
        # Track liked state (mutable so it can be toggled)
        liked_state = [args.liked]
        sdl2.SDL_RenderClear(renderer)
        
        # For rotation 90/270, swap width and height for layout calculation
        # The layout function calculates positions for a landscape layout (e.g., 1280x720)
        # Then the renderer functions transform those to physical screen coords (e.g., 720x1280)
        layout_width = display_mode.h if args.rotation in (90, 270) else display_mode.w
        layout_height = display_mode.w if args.rotation in (90, 270) else display_mode.h
        
        button_rects = [draw_now_playing_ui(renderer, layout_width, layout_height, 
                          font_large, font_medium, font_small, font_icons, is_portrait, 
                          args.bw_buttons, args.no_control, args.minimal_buttons, liked_state[0], 
                          args.rotation, display_mode.w, display_mode.h)]
        sdl2.SDL_RenderPresent(renderer)
        
        def check_button_hit(x, y):
            """Check if coordinates hit any button, return button name or None"""
            rects = button_rects[0]
            if not rects:
                return None
            for button_name, (bx, by, bw, bh) in rects.items():
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    return button_name
            return None
        
        while running:
            # Handle events
            while sdl2.SDL_PollEvent(event) != 0:
                if event.type == sdl2.SDL_QUIT:
                    running = False
                elif event.type == sdl2.SDL_KEYDOWN:
                    # Exit on ESC or Q key
                    if event.key.keysym.sym in (sdl2.SDLK_ESCAPE, sdl2.SDLK_q):
                        running = False
                elif event.type == sdl2.SDL_FINGERDOWN:
                    # Touch coordinates are normalized (0.0-1.0)
                    touch_x = int(event.tfinger.x * display_mode.w)
                    touch_y = int(event.tfinger.y * display_mode.h)
                    button = check_button_hit(touch_x, touch_y)
                    if button:
                        print(f"Button pressed: {button}")
                        # Toggle liked state when like button is pressed
                        if button == 'like':
                            liked_state[0] = not liked_state[0]
                            print(f"Liked: {liked_state[0]}")
                elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                    # Mouse coordinates are in pixels
                    button = check_button_hit(event.button.x, event.button.y)
                    if button:
                        print(f"Button pressed: {button}")
                        # Toggle liked state when like button is pressed
                        if button == 'like':
                            liked_state[0] = not liked_state[0]
                            print(f"Liked: {liked_state[0]}")
            
            # Clear renderer
            sdl2.SDL_RenderClear(renderer)
            
            # Draw the Now Playing UI and get button positions
            button_rects[0] = draw_now_playing_ui(renderer, layout_width, layout_height, 
                              font_large, font_medium, font_small, font_icons, is_portrait, 
                              args.bw_buttons, args.no_control, args.minimal_buttons, liked_state[0], 
                              args.rotation, display_mode.w, display_mode.h)
            
            # Present the rendered frame
            sdl2.SDL_RenderPresent(renderer)
            
            # Small delay to prevent busy loop
            sdl2.SDL_Delay(10)
        
        # Cleanup
        if font_large:
            sdlttf.TTF_CloseFont(font_large)
        if font_medium:
            sdlttf.TTF_CloseFont(font_medium)
        if font_small:
            sdlttf.TTF_CloseFont(font_small)
        if font_icons:
            sdlttf.TTF_CloseFont(font_icons)
        sdl2.SDL_DestroyRenderer(renderer)
        sdl2.SDL_DestroyWindow(window)
        
    finally:
        sdlimage.IMG_Quit()
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
