#!/usr/bin/env python3
"""
Now Playing Display - Shows currently playing media on SDL screen
"""

import sdl2
import sdl2.ext
import sdl2.sdlttf as sdlttf
import sys
import argparse


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
        '--rotate',
        type=int,
        choices=[0, 90, 180, 270],
        default=0,
        help='Rotate display by degrees (0, 90, 180, 270)'
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
    return parser.parse_args()


def get_display_info(display_index):
    """Get information about a specific display"""
    mode = sdl2.SDL_DisplayMode()
    
    if sdl2.SDL_GetDesktopDisplayMode(display_index, mode) != 0:
        print(f"Error getting display mode: {sdl2.SDL_GetError()}")
        return None
    
    return mode


def draw_rounded_rect(renderer, x, y, w, h, radius, r, g, b, a):
    """Draw a filled rounded rectangle"""
    sdl2.SDL_SetRenderDrawColor(renderer, r, g, b, a)
    
    # Draw filled rectangles to make up the rounded rect
    # Top
    rect = sdl2.SDL_Rect(x + radius, y, w - 2 * radius, radius)
    sdl2.SDL_RenderFillRect(renderer, rect)
    # Middle
    rect = sdl2.SDL_Rect(x, y + radius, w, h - 2 * radius)
    sdl2.SDL_RenderFillRect(renderer, rect)
    # Bottom
    rect = sdl2.SDL_Rect(x + radius, y + h - radius, w - 2 * radius, radius)
    sdl2.SDL_RenderFillRect(renderer, rect)
    
    # Draw circles at corners (simplified with filled rects for now)
    # Top-left
    rect = sdl2.SDL_Rect(x, y, radius, radius)
    sdl2.SDL_RenderFillRect(renderer, rect)
    # Top-right
    rect = sdl2.SDL_Rect(x + w - radius, y, radius, radius)
    sdl2.SDL_RenderFillRect(renderer, rect)
    # Bottom-left
    rect = sdl2.SDL_Rect(x, y + h - radius, radius, radius)
    sdl2.SDL_RenderFillRect(renderer, rect)
    # Bottom-right
    rect = sdl2.SDL_Rect(x + w - radius, y + h - radius, radius, radius)
    sdl2.SDL_RenderFillRect(renderer, rect)


def render_text(renderer, font, text, x, y, r, g, b):
    """Render text at the given position"""
    color = sdl2.SDL_Color(r, g, b, 255)
    surface = sdlttf.TTF_RenderText_Blended(font, text.encode('utf-8'), color)
    if not surface:
        return
    
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    if texture:
        rect = sdl2.SDL_Rect(x, y, surface.contents.w, surface.contents.h)
        sdl2.SDL_RenderCopy(renderer, texture, None, rect)
        sdl2.SDL_DestroyTexture(texture)
    
    sdl2.SDL_FreeSurface(surface)


def render_text_centered(renderer, font, text, center_x, center_y, r, g, b):
    """Render text centered at the given position"""
    color = sdl2.SDL_Color(r, g, b, 255)
    surface = sdlttf.TTF_RenderText_Blended(font, text.encode('utf-8'), color)
    if not surface:
        return
    
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    if texture:
        # Center the text
        x = center_x - surface.contents.w // 2
        y = center_y - surface.contents.h // 2
        rect = sdl2.SDL_Rect(x, y, surface.contents.w, surface.contents.h)
        sdl2.SDL_RenderCopy(renderer, texture, None, rect)
        sdl2.SDL_DestroyTexture(texture)
    
    sdl2.SDL_FreeSurface(surface)


def wrap_text(font, text, max_width):
    """Wrap text to fit within max_width, returning list of lines"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Get text width
        w = sdl2.c_int()
        h = sdl2.c_int()
        sdlttf.TTF_SizeText(font, test_line.encode('utf-8'), w, h)
        
        if w.value <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Single word is too long
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def truncate_text(font, text, max_width):
    """Truncate text to fit within max_width with ellipsis"""
    # Check if text fits
    w = sdl2.c_int()
    h = sdl2.c_int()
    sdlttf.TTF_SizeText(font, text.encode('utf-8'), w, h)
    
    if w.value <= max_width:
        return text
    
    # Binary search for the right length
    ellipsis = "..."
    left, right = 0, len(text)
    best = ""
    
    while left <= right:
        mid = (left + right) // 2
        test_text = text[:mid] + ellipsis
        sdlttf.TTF_SizeText(font, test_text.encode('utf-8'), w, h)
        
        if w.value <= max_width:
            best = test_text
            left = mid + 1
        else:
            right = mid - 1
    
    return best if best else ellipsis


def render_wrapped_text_centered(renderer, font, text, center_x, y, max_width, r, g, b, max_lines=2):
    """Render wrapped text centered horizontally"""
    lines = wrap_text(font, text, max_width)
    
    # Limit to max_lines
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Truncate last line with ellipsis
        lines[-1] = truncate_text(font, lines[-1], max_width)
    
    # Get line height
    line_height = sdlttf.TTF_FontLineSkip(font)
    
    # Render each line
    for i, line in enumerate(lines):
        render_text_centered(renderer, font, line, center_x, y + i * line_height, r, g, b)
    
    return len(lines) * line_height


def draw_now_playing_ui_landscape(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons=False, no_control=False):
    """Draw the Now Playing UI in landscape orientation
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    # Clear screen to light gray background
    sdl2.SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255)
    sdl2.SDL_RenderClear(renderer)
    
    # Calculate layout
    padding = 40
    cover_size = min(width // 2 - padding * 2, height - padding * 2)
    cover_x = padding
    cover_y = (height - cover_size) // 2
    
    button_rects = {}
    
    # Draw album cover placeholder (dark gray square)
    draw_rounded_rect(renderer, cover_x, cover_y, cover_size, cover_size, 20, 100, 100, 100, 255)
    
    # Draw music note symbol in center of cover
    note_text = "♪"
    render_text(renderer, font_large, note_text, 
                cover_x + cover_size // 2 - 30, cover_y + cover_size // 2 - 40, 200, 200, 200)
    
    # Right side content area
    content_x = cover_x + cover_size + padding * 2
    content_y = padding * 2
    content_width = width - content_x - padding
    
    # Song title
    title = "Never Gonna Give You Up"
    render_text(renderer, font_large, title, content_x, content_y, 30, 30, 30)
    
    # Artist name
    artist = "Rick Astley"
    render_text(renderer, font_medium, artist, content_x, content_y + 80, 100, 100, 100)
    
    # Album name
    album = "Whenever You Need Somebody"
    render_text(renderer, font_small, album, content_x, content_y + 130, 150, 150, 150)
    
    # Control buttons area
    button_y = content_y + 280
    button_size = 100
    button_spacing = 25
    
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
    
    if no_control:
        # Only show like button, centered
        like_x = content_x + (content_width - button_size) // 2
        draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 40, *like_color, 255)
        render_text_centered(renderer, font_icons, "favorite", like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    else:
        # Calculate button positions to center them
        total_buttons_width = button_size * 4 + button_spacing * 3
        buttons_start_x = content_x + (content_width - total_buttons_width) // 2
        
        # Previous button (skip_previous icon)
        prev_x = buttons_start_x
        draw_rounded_rect(renderer, prev_x, button_y, button_size, button_size, 40, *prev_color, 255)
        render_text_centered(renderer, font_icons, "skip_previous", prev_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['prev'] = (prev_x, button_y, button_size, button_size)
        
        # Play/Pause button (play_arrow icon)
        play_x = prev_x + button_size + button_spacing
        draw_rounded_rect(renderer, play_x, button_y, button_size, button_size, 40, *play_color, 255)
        render_text_centered(renderer, font_icons, "play_arrow", play_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['play'] = (play_x, button_y, button_size, button_size)
        
        # Next button (skip_next icon)
        next_x = play_x + button_size + button_spacing
        draw_rounded_rect(renderer, next_x, button_y, button_size, button_size, 40, *next_color, 255)
        render_text_centered(renderer, font_icons, "skip_next", next_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['next'] = (next_x, button_y, button_size, button_size)
        
        # Like button (favorite icon)
        like_x = next_x + button_size + button_spacing
        draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 40, *like_color, 255)
        render_text_centered(renderer, font_icons, "favorite", like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    
    return button_rects


def draw_now_playing_ui_portrait(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons=False, no_control=False):
    """Draw the Now Playing UI in portrait orientation
    
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
    
    # Calculate layout with 5% vertical offset
    vertical_offset = int(height * 0.05)
    padding = 30
    cover_size = min(width - padding * 2, (height - padding * 4) // 2)
    cover_x = (width - cover_size) // 2
    cover_y = padding + vertical_offset
    
    # Draw album cover placeholder (dark gray square)
    draw_rounded_rect(renderer, cover_x, cover_y, cover_size, cover_size, 20, 100, 100, 100, 255)
    
    # Draw music note symbol in center of cover
    note_text = "♪"
    render_text(renderer, font_large, note_text, 
                cover_x + cover_size // 2 - 30, cover_y + cover_size // 2 - 40, 200, 200, 200)
    
    # Content area below cover
    content_y = cover_y + cover_size + padding + int(height * 0.05)  # Move 5% down
    content_x = padding
    max_text_width = int(width * 0.90)  # 90% of width
    center_x = width // 2
    
    # Song title (centered, wrapped to max 2 lines)
    title = "Never Gonna Give You Up"
    title_height = render_wrapped_text_centered(renderer, font_large, title, center_x, content_y, max_text_width, 30, 30, 30, max_lines=2)
    
    # Artist name (centered, single line with truncation)
    artist = "Rick Astley"
    artist_text = truncate_text(font_medium, artist, max_text_width)
    render_text_centered(renderer, font_medium, artist_text, center_x, content_y + title_height + 20, 100, 100, 100)
    
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
    
    if no_control:
        # Only show like button, centered
        like_x = (width - button_size) // 2
        draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 35, *like_color, 255)
        render_text_centered(renderer, font_icons, "favorite", like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    else:
        # Calculate button positions to center them
        total_buttons_width = button_size * 4 + button_spacing * 3
        buttons_start_x = (width - total_buttons_width) // 2
        
        # Previous button (skip_previous icon)
        prev_x = buttons_start_x
        draw_rounded_rect(renderer, prev_x, button_y, button_size, button_size, 35, *prev_color, 255)
        render_text_centered(renderer, font_icons, "skip_previous", prev_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['prev'] = (prev_x, button_y, button_size, button_size)
        
        # Play/Pause button (play_arrow icon)
        play_x = prev_x + button_size + button_spacing
        draw_rounded_rect(renderer, play_x, button_y, button_size, button_size, 35, *play_color, 255)
        render_text_centered(renderer, font_icons, "play_arrow", play_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['play'] = (play_x, button_y, button_size, button_size)
        
        # Next button (skip_next icon)
        next_x = play_x + button_size + button_spacing
        draw_rounded_rect(renderer, next_x, button_y, button_size, button_size, 35, *next_color, 255)
        render_text_centered(renderer, font_icons, "skip_next", next_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['next'] = (next_x, button_y, button_size, button_size)
        
        # Like button (favorite icon)
        like_x = next_x + button_size + button_spacing
        draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, 35, *like_color, 255)
        render_text_centered(renderer, font_icons, "favorite", like_x + button_size // 2, button_y + button_size // 2, 255, 255, 255)
        button_rects['like'] = (like_x, button_y, button_size, button_size)
    
    return button_rects


def draw_now_playing_ui(renderer, width, height, font_large, font_medium, font_small, font_icons, is_portrait, bw_buttons=False, no_control=False):
    """Draw the Now Playing UI based on orientation
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    if is_portrait:
        return draw_now_playing_ui_portrait(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons, no_control)
    else:
        return draw_now_playing_ui_landscape(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons, no_control)

def draw_now_playing_ui(renderer, width, height, font_large, font_medium, font_small, font_icons, is_portrait, bw_buttons=False, no_control=False):
    """Draw the Now Playing UI based on orientation
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    if is_portrait:
        return draw_now_playing_ui_portrait(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons, no_control)
    else:
        return draw_now_playing_ui_landscape(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons, no_control)


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
        if args.portrait:
            is_portrait = True
            orientation_str = "portrait (forced)"
        elif args.landscape:
            is_portrait = False
            orientation_str = "landscape (forced)"
        else:
            # Auto-detect based on display resolution
            is_portrait = display_mode.h > display_mode.w
            orientation_str = "portrait (auto)" if is_portrait else "landscape (auto)"
        
        print(f"Using display {args.display}: {display_mode.w}x{display_mode.h} @ {display_mode.refresh_rate}Hz ({orientation_str})")
        
        # Get display bounds to position window on correct display
        bounds = sdl2.SDL_Rect()
        if sdl2.SDL_GetDisplayBounds(args.display, bounds) != 0:
            print(f"Error getting display bounds: {sdl2.SDL_GetError()}")
            return 1
        
        # Adjust dimensions based on rotation
        if args.rotate in [90, 270]:
            window_w = display_mode.h
            window_h = display_mode.w
        else:
            window_w = display_mode.w
            window_h = display_mode.h
        
        # Create window on the specified display
        window = sdl2.SDL_CreateWindow(
            b"Now Playing",
            bounds.x,  # Position on the specified display
            bounds.y,
            window_w,
            window_h,
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
        sdl2.SDL_RenderClear(renderer)
        button_rects = [draw_now_playing_ui(renderer, display_mode.w, display_mode.h, 
                          font_large, font_medium, font_small, font_icons, is_portrait, 
                          args.bw_buttons, args.no_control)]
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
                elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                    # Mouse coordinates are in pixels
                    button = check_button_hit(event.button.x, event.button.y)
                    if button:
                        print(f"Button pressed: {button}")
            
            # Clear and apply rotation
            sdl2.SDL_RenderClear(renderer)
            
            # Save current render state
            if args.rotate != 0:
                # Get the center point for rotation
                if args.rotate in [90, 270]:
                    center_x = display_mode.h // 2
                    center_y = display_mode.w // 2
                else:
                    center_x = display_mode.w // 2
                    center_y = display_mode.h // 2
                
                # Apply rotation by rendering to a texture (simplified approach)
                # For now, just adjust the logical dimensions
                pass
            
            # Draw the Now Playing UI and get button positions
            button_rects[0] = draw_now_playing_ui(renderer, display_mode.w, display_mode.h, 
                              font_large, font_medium, font_small, font_icons, is_portrait, 
                              args.bw_buttons, args.no_control)
            
            # Present the rendered frame
            sdl2.SDL_RenderPresent(renderer)
        
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
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
