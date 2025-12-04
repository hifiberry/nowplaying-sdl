"""
UI drawing functions for Now Playing Display
"""

import os
import logging
import sdl2
import sdl2.sdlttf as sdlttf

from .renderer import (
    draw_circle,
    draw_rounded_rect,
    render_text_centered,
    truncate_text,
    wrap_text,
    render_wrapped_text_centered
)

logger = logging.getLogger(__name__)


def get_resource_path(filename):
    """Get the full path to a resource file"""
    from pathlib import Path
    
    # Try package data directory first
    module_dir = Path(__file__).parent
    resource = module_dir / filename
    if resource.exists():
        return str(resource)
    
    # Try system data directory
    system_data = Path('/usr/share/nowplaying-sdl') / filename
    if system_data.exists():
        return str(system_data)
    
    # Fallback to module directory
    return str(module_dir / filename)


def get_now_playing_data(demo, now_playing_data, cover_cache):
    """Get now playing data from demo or API
    
    Args:
        demo: If True, use demo data
        now_playing_data: Dict with artist, title, album, cover_url from AudioControl
        cover_cache: CoverArtCache instance for downloading cover art
    
    Returns:
        Tuple of (cover_file, title, artist)
    """
    if demo:
        cover_file = get_resource_path("demo_cover.jpg")
        title = "Never Gonna Give You Up"
        artist = "Rick Astley"
    elif now_playing_data:
        # Get cover art (download if needed)
        cover_url = now_playing_data.get('cover_url')
        cover_file = cover_cache.get_cover(cover_url) if cover_cache and cover_url else None
        title = now_playing_data.get('title', '')
        artist = now_playing_data.get('artist', '')
    else:
        cover_file = None
        title = ""
        artist = ""
    
    return cover_file, title, artist


def get_button_colors(bw_buttons):
    """Get button colors for UI layouts
    
    Args:
        bw_buttons: If True, use grayscale colors
    
    Returns:
        Tuple of (prev_color, play_color, next_color, like_color)
    """
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
    
    return prev_color, play_color, next_color, like_color


def get_button_icon_font(minimal_buttons, font_icons, size_multiplier=1.5):
    """Get the appropriate icon font for buttons
    
    Args:
        minimal_buttons: If True, load a larger icon font for minimal button style
        font_icons: The default icon font to use if not minimal
        size_multiplier: Size multiplier for minimal buttons (default 1.5 for fixed size, or button_size * 0.6 for scaled)
    
    Returns:
        Tuple of (font_icons_buttons, needs_cleanup) where needs_cleanup indicates if font should be closed later
    """
    if minimal_buttons:
        if isinstance(size_multiplier, float) and size_multiplier < 1.0:
            # This is actually a button_size ratio (e.g., button_size * 0.6)
            font_size = int(size_multiplier)
        else:
            # This is a fixed multiplier (e.g., 48 * 1.5)
            font_size = int(48 * size_multiplier)
        font_icons_buttons = sdlttf.TTF_OpenFont(get_resource_path("fonts/MaterialIcons-Regular.ttf").encode("utf-8"), font_size)
        return font_icons_buttons, True
    else:
        return font_icons, False


def wrap_and_truncate_text(font, text, max_width, max_lines):
    """Wrap text and truncate to max lines with ellipsis
    
    Args:
        font: TTF font to use for text measurement
        text: Text to wrap
        max_width: Maximum width in pixels
        max_lines: Maximum number of lines
    
    Returns:
        List of text lines (truncated with ellipsis if needed)
    """
    wrapped = wrap_text(font, text, max_width)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        if len(wrapped[-1]) > 3:
            wrapped[-1] = wrapped[-1][:-3] + "..."
        elif len(wrapped[-1]) > 0:
            wrapped[-1] = wrapped[-1] + "..."
    return wrapped


def setup_circle_layout(screen_width, screen_height, width, height):
    """Setup circle layout dimensions and draw outline
    
    Args:
        screen_width, screen_height: Physical screen dimensions
        width, height: Layout dimensions
    
    Returns:
        Tuple of (physical_diameter, physical_center_x, physical_center_y, diameter, circle_center_x, circle_center_y)
    """
    physical_diameter = min(screen_width, screen_height)
    physical_center_x = screen_width // 2
    physical_center_y = screen_height // 2
    
    diameter = min(width, height)
    circle_center_x = width // 2
    circle_center_y = height // 2
    
    return physical_diameter, physical_center_x, physical_center_y, diameter, circle_center_x, circle_center_y


def draw_circle_outline(renderer, physical_center_x, physical_center_y, physical_diameter):
    """Draw circle outline on physical screen
    
    Args:
        renderer: SDL2 renderer
        physical_center_x, physical_center_y: Center coordinates on physical screen
        physical_diameter: Diameter of the circle
    """
    circle_radius = physical_diameter // 2 + 1
    draw_circle(renderer, physical_center_x, physical_center_y, circle_radius, 0, 0, 0, 255, thickness=2)


def render_control_buttons(renderer, button_y, button_size, button_spacing, center_x, total_width,
                          prev_color, play_color, next_color, like_color,
                          font_icons_buttons, minimal_buttons, liked, no_control,
                          rotation, screen_width, screen_height, border_radius=35, hide_like_button=False):
    """Render control buttons (prev, play, next, like)
    
    Args:
        renderer: SDL2 renderer
        button_y: Y position for buttons
        button_size: Size of each button
        button_spacing: Spacing between buttons
        center_x: Center X position for button group
        total_width: Total width available (used for centering)
        prev_color, play_color, next_color, like_color: Button colors
        font_icons_buttons: Icon font to use
        minimal_buttons: If True, render minimal style (no background)
        liked: If True, show filled heart icon
        no_control: If True, only show like button
        rotation: Screen rotation angle
        screen_width, screen_height: Physical screen dimensions
        border_radius: Border radius for button backgrounds (default 35)
        hide_like_button: If True, don't render the like button
    
    Returns:
        Dict of button rectangles: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    button_rects = {}
    
    if no_control:
        # Only show like button, centered (if not hidden)
        if not hide_like_button:
            like_icon = "favorite" if liked else "favorite_border"
            like_x = center_x - button_size // 2
            if not minimal_buttons:
                draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, border_radius, 
                                *like_color, 255, rotation, screen_width, screen_height)
                render_text_centered(renderer, font_icons_buttons, like_icon, 
                                   like_x + button_size // 2, button_y + button_size // 2, 
                                   255, 255, 255, rotation, screen_width, screen_height)
            else:
                render_text_centered(renderer, font_icons_buttons, like_icon, 
                                   like_x + button_size // 2, button_y + button_size // 2, 
                                   *like_color, rotation, screen_width, screen_height)
            button_rects['like'] = (like_x, button_y, button_size, button_size)
    else:
        # Calculate button positions to center them
        num_buttons = 3 if hide_like_button else 4
        total_buttons_width = button_size * num_buttons + button_spacing * (num_buttons - 1)
        buttons_start_x = center_x - total_buttons_width // 2
        
        # Previous button
        prev_x = buttons_start_x
        if not minimal_buttons:
            draw_rounded_rect(renderer, prev_x, button_y, button_size, button_size, border_radius, 
                            *prev_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "skip_previous", 
                               prev_x + button_size // 2, button_y + button_size // 2, 
                               255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "skip_previous", 
                               prev_x + button_size // 2, button_y + button_size // 2, 
                               *prev_color, rotation, screen_width, screen_height)
        button_rects['prev'] = (prev_x, button_y, button_size, button_size)
        
        # Play/Pause button
        play_x = prev_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, play_x, button_y, button_size, button_size, border_radius, 
                            *play_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "play_arrow", 
                               play_x + button_size // 2, button_y + button_size // 2, 
                               255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "play_arrow", 
                               play_x + button_size // 2, button_y + button_size // 2, 
                               *play_color, rotation, screen_width, screen_height)
        button_rects['play'] = (play_x, button_y, button_size, button_size)
        
        # Next button
        next_x = play_x + button_size + button_spacing
        if not minimal_buttons:
            draw_rounded_rect(renderer, next_x, button_y, button_size, button_size, border_radius, 
                            *next_color, 255, rotation, screen_width, screen_height)
            render_text_centered(renderer, font_icons_buttons, "skip_next", 
                               next_x + button_size // 2, button_y + button_size // 2, 
                               255, 255, 255, rotation, screen_width, screen_height)
        else:
            render_text_centered(renderer, font_icons_buttons, "skip_next", 
                               next_x + button_size // 2, button_y + button_size // 2, 
                               *next_color, rotation, screen_width, screen_height)
        button_rects['next'] = (next_x, button_y, button_size, button_size)
        
        # Like button (if not hidden)
        if not hide_like_button:
            like_icon = "favorite" if liked else "favorite_border"
            like_x = next_x + button_size + button_spacing
            if not minimal_buttons:
                draw_rounded_rect(renderer, like_x, button_y, button_size, button_size, border_radius, 
                                *like_color, 255, rotation, screen_width, screen_height)
                render_text_centered(renderer, font_icons_buttons, like_icon, 
                                   like_x + button_size // 2, button_y + button_size // 2, 
                                   255, 255, 255, rotation, screen_width, screen_height)
            else:
                render_text_centered(renderer, font_icons_buttons, like_icon, 
                                   like_x + button_size // 2, button_y + button_size // 2, 
                                   *like_color, rotation, screen_width, screen_height)
            button_rects['like'] = (like_x, button_y, button_size, button_size)
    
    return button_rects


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
    import sdl2.sdlimage as sdlimage
    
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
                    # For 0° and 180° rotations
                    if rotation == 180:
                        # Transform coordinates for 180° rotation
                        screen_x = screen_width - (x + size)
                        screen_y = screen_height - (y + size)
                        rect = sdl2.SDL_Rect(screen_x, screen_y, size, size)
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
        font_path = get_resource_path('fonts/MaterialIcons-Regular.ttf')
        font_icons_large = sdlttf.TTF_OpenFont(font_path.encode('utf-8'), icon_size)
        if font_icons_large:
            render_text_centered(renderer, font_icons_large, album_icon, 
                               x + size // 2, y + size // 2, 200, 200, 200, rotation, screen_width, screen_height)
            sdlttf.TTF_CloseFont(font_icons_large)


def draw_now_playing_ui_portrait(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons=False, no_control=False, minimal_buttons=False, liked=False, rotation=0, screen_width=0, screen_height=0, demo=False, now_playing_data=None, cover_cache=None, hide_like_button=False):
    """Draw the Now Playing UI in portrait orientation
    
    Args:
        width, height: Layout dimensions (may be swapped for rotation)
        screen_width, screen_height: Physical screen dimensions
        demo: If True, use demo data; if False, use now_playing_data
        now_playing_data: Dict with artist, title, album, cover_url from AudioControl
        cover_cache: CoverArtCache instance for downloading cover art
        hide_like_button: If True, don't render the like button
    
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
    
    # Get now playing data
    cover_file, title, artist = get_now_playing_data(demo, now_playing_data, cover_cache)
    
    # Render album cover
    render_coverart(renderer, cover_x, cover_y, cover_size, cover_file, font_icons, rotation, screen_width, screen_height)
    
    # Content area below cover
    content_y = cover_y + cover_size + padding + int(height * 0.05)  # Move 5% down
    content_x = padding
    max_text_width = int(width * 0.90)  # 90% of width
    center_x = width // 2
    
    # Song title (centered, wrapped to max 2 lines)
    title_height = render_wrapped_text_centered(renderer, font_large, title, center_x, content_y, max_text_width, 30, 30, 30, max_lines=2, rotation=rotation, width=screen_width, height=screen_height)
    
    # Artist name (centered, single line with truncation)
    artist_text = truncate_text(font_medium, artist, max_text_width)
    render_text_centered(renderer, font_medium, artist_text, center_x, content_y + title_height + 20, 100, 100, 100, rotation, screen_width, screen_height)
    
    # Control buttons area
    button_y = content_y + title_height + 150
    button_size = 90
    button_spacing = 20
    
    # Get button colors
    prev_color, play_color, next_color, like_color = get_button_colors(bw_buttons)
    
    # Load icon font for buttons
    font_icons_buttons, needs_font_cleanup = get_button_icon_font(minimal_buttons, font_icons, 1.5)
    
    # Render control buttons
    button_rects = render_control_buttons(
        renderer, button_y, button_size, button_spacing, center_x, width,
        prev_color, play_color, next_color, like_color,
        font_icons_buttons, minimal_buttons, liked, no_control,
        rotation, screen_width, screen_height, border_radius=35, hide_like_button=hide_like_button
    )
    
    if needs_font_cleanup:
        sdlttf.TTF_CloseFont(font_icons_buttons)
    
    return button_rects


def draw_now_playing_ui_landscape(renderer, width, height, font_large, font_medium, font_icons, bw_buttons=False, no_control=False, minimal_buttons=False, liked=False, rotation=0, screen_width=0, screen_height=0, demo=False, now_playing_data=None, cover_cache=None, hide_like_button=False):
    """Draw the Now Playing UI in landscape orientation
    
    Args:
        width, height: Layout dimensions (may be swapped for rotation)
        screen_width, screen_height: Physical screen dimensions
        demo: If True, use demo data; if False, use now_playing_data
        now_playing_data: Dict with artist, title, album, cover_url from AudioControl
        cover_cache: CoverArtCache instance for downloading cover art
    
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
    
    # Get now playing data
    cover_file, title, artist = get_now_playing_data(demo, now_playing_data, cover_cache)
    
    # Render album cover
    render_coverart(renderer, cover_x, cover_y, cover_size, cover_file, font_icons, rotation, screen_width, screen_height)
    
    # Right side content area
    content_x = cover_x + cover_size + padding * 2
    content_y = padding * 2
    content_width = width - content_x - padding
    content_center_x = content_x + content_width // 2
    
    # Song title (centered) - wrap to max 40% display width
    max_text_width = int(width * 0.4)
    wrapped_title = wrap_and_truncate_text(font_large, title, max_text_width, 2)
    
    title_y = content_y + 28 + int(height * TEXT_VERTICAL_OFFSET_PERCENT)
    for i, line in enumerate(wrapped_title):
        render_text_centered(renderer, font_large, line, content_center_x, title_y + i * 60, 30, 30, 30, rotation, screen_width, screen_height)
    
    # Artist name (centered) - wrap to max 40% display width
    wrapped_artist = wrap_and_truncate_text(font_medium, artist, max_text_width, 2)
    
    artist_y = content_y + 105 + (len(wrapped_title) - 1) * 60 + int(height * TEXT_VERTICAL_OFFSET_PERCENT)
    for i, line in enumerate(wrapped_artist):
        render_text_centered(renderer, font_medium, line, content_center_x, artist_y + i * 50, 100, 100, 100, rotation, screen_width, screen_height)
    
    # Control buttons area - align bottom of buttons with bottom of cover
    button_size = 100
    button_spacing = 25
    button_y = cover_y + cover_size - button_size + int(height * BUTTON_VERTICAL_OFFSET_PERCENT)
    
    # Get button colors
    prev_color, play_color, next_color, like_color = get_button_colors(bw_buttons)
    
    # Load icon font for buttons
    font_icons_buttons, needs_font_cleanup = get_button_icon_font(minimal_buttons, font_icons, 1.5)
    
    # Render control buttons
    button_rects = render_control_buttons(
        renderer, button_y, button_size, button_spacing, content_center_x, content_width,
        prev_color, play_color, next_color, like_color,
        font_icons_buttons, minimal_buttons, liked, no_control,
        rotation, screen_width, screen_height, border_radius=40, hide_like_button=hide_like_button
    )
    
    if needs_font_cleanup:
        sdlttf.TTF_CloseFont(font_icons_buttons)
    
    return button_rects


def draw_now_playing_ui_circle(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons=False, no_control=False, minimal_buttons=False, liked=False, rotation=0, screen_width=0, screen_height=0, demo=False, now_playing_data=None, cover_cache=None, hide_like_button=False):
    """Draw the Now Playing UI in circular layout mode
    
    Args:
        width, height: Layout dimensions (may be swapped for rotation)
        screen_width, screen_height: Physical screen dimensions
        demo: If True, use demo data; if False, use now_playing_data
        now_playing_data: Dict with artist, title, album, cover_url from AudioControl
        cover_cache: CoverArtCache instance for downloading cover art
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    
    # Clear screen to light gray background
    sdl2.SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255)
    sdl2.SDL_RenderClear(renderer)
    
    # Setup circle layout
    physical_diameter, physical_center_x, physical_center_y, diameter, circle_center_x, circle_center_y = \
        setup_circle_layout(screen_width, screen_height, width, height)
    
    # Draw circle outline
    draw_circle_outline(renderer, physical_center_x, physical_center_y, physical_diameter)
    
    # Calculate layout elements within the circle
    padding = int(diameter * 0.05)  # 5% of diameter
    cover_size = int(diameter * 0.4)  # 40% of diameter for cover
    cover_x = circle_center_x - cover_size // 2
    cover_y = circle_center_y - int(diameter * 0.37)  # Move cover 2% up (was 0.35, now 0.37)
    
    button_rects = {}
    
    # Get now playing data
    cover_file, title, artist = get_now_playing_data(demo, now_playing_data, cover_cache)
    
    # Render album cover at the top
    render_coverart(renderer, cover_x, cover_y, cover_size, cover_file, font_icons, rotation, screen_width, screen_height)
    
    # Song title below the cover - wrap to 70% of diameter
    max_text_width = int(diameter * 0.7)
    wrapped_title = wrap_and_truncate_text(font_large, title, max_text_width, 2)
    
    # Move text 5% down
    text_offset = int(diameter * 0.05)
    title_y = cover_y + cover_size + 20 + text_offset  # Below the cover + 5% offset
    for i, line in enumerate(wrapped_title):
        render_text_centered(renderer, font_large, line, circle_center_x, title_y + i * 60, 30, 30, 30, rotation, screen_width, screen_height)
    
    # Artist name below title
    wrapped_artist = wrap_and_truncate_text(font_medium, artist, max_text_width, 1)
    
    artist_y = title_y + 65 + (len(wrapped_title) - 1) * 60  # Below title
    for i, line in enumerate(wrapped_artist):
        render_text_centered(renderer, font_medium, line, circle_center_x, artist_y + i * 50, 100, 100, 100, rotation, screen_width, screen_height)
    
    # Control buttons at the bottom of the circle
    button_size = int(diameter * 0.12)  # 12% of diameter
    button_spacing = int(diameter * 0.03)  # 3% of diameter
    button_y = circle_center_y + int(diameter * 0.32)  # Move buttons 3% up (was 0.35, now 0.32)
    
    # Get button colors
    prev_color, play_color, next_color, like_color = get_button_colors(bw_buttons)
    
    # Load icon font for buttons
    font_icons_buttons, needs_font_cleanup = get_button_icon_font(minimal_buttons, font_icons, button_size * 0.6)
    
    # Render control buttons
    button_rects = render_control_buttons(
        renderer, button_y, button_size, button_spacing, circle_center_x, diameter,
        prev_color, play_color, next_color, like_color,
        font_icons_buttons, minimal_buttons, liked, no_control,
        rotation, screen_width, screen_height, border_radius=int(button_size * 0.35), hide_like_button=hide_like_button
    )
    
    if needs_font_cleanup:
        sdlttf.TTF_CloseFont(font_icons_buttons)
    
    return button_rects


def draw_now_playing_ui_circle2(renderer, width, height, font_large, font_medium, font_small, font_icons, bw_buttons=False, no_control=False, minimal_buttons=False, liked=False, rotation=0, screen_width=0, screen_height=0, demo=False, now_playing_data=None, cover_cache=None, hide_like_button=False):
    """Draw the Now Playing UI in circular layout mode with larger cover and smaller fonts
    
    Args:
        width, height: Layout dimensions (may be swapped for rotation)
        screen_width, screen_height: Physical screen dimensions
        demo: If True, use demo data; if False, use now_playing_data
        now_playing_data: Dict with artist, title, album, cover_url from AudioControl
        cover_cache: CoverArtCache instance for downloading cover art
    
    Returns button positions as dict: {'prev': (x,y,w,h), 'play': (x,y,w,h), ...}
    """
    
    # Clear screen to light gray background
    sdl2.SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255)
    sdl2.SDL_RenderClear(renderer)
    
    # Setup circle layout
    physical_diameter, physical_center_x, physical_center_y, diameter, circle_center_x, circle_center_y = \
        setup_circle_layout(screen_width, screen_height, width, height)
    
    # Draw circle outline
    draw_circle_outline(renderer, physical_center_x, physical_center_y, physical_diameter)
    
    # Calculate layout elements within the circle
    padding = int(diameter * 0.05)  # 5% of diameter
    cover_size = int(diameter * 0.52)  # 52% of diameter for cover (30% larger than 40%)
    cover_x = circle_center_x - cover_size // 2
    cover_y = circle_center_y - int(diameter * 0.37)  # Move cover 2% up
    
    button_rects = {}
    
    # Get now playing data
    cover_file, title, artist = get_now_playing_data(demo, now_playing_data, cover_cache)
    
    # Render album cover at the top
    render_coverart(renderer, cover_x, cover_y, cover_size, cover_file, font_icons, rotation, screen_width, screen_height)
    
    # Load smaller fonts (20% smaller: 48->38, 42->34) - using Noto Sans for better Unicode support
    # Try multiple font paths for better compatibility
    font_paths_bold = [
        b"/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        b"/usr/share/fonts/truetype/noto/NotoSans_Condensed-Bold.ttf",
        b"/usr/share/fonts/noto/NotoSans-Bold.ttf",
        b"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    font_paths_regular = [
        b"/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        b"/usr/share/fonts/truetype/noto/NotoSans_Condensed-Regular.ttf",
        b"/usr/share/fonts/noto/NotoSans-Regular.ttf",
        b"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    
    font_large_small = None
    for path in font_paths_bold:
        try:
            font_large_small = sdlttf.TTF_OpenFont(path, 38)
            if font_large_small:
                break
        except:
            continue
    
    font_medium_small = None
    for path in font_paths_regular:
        try:
            font_medium_small = sdlttf.TTF_OpenFont(path, 34)
            if font_medium_small:
                break
        except:
            continue
    
    # Song title below the cover - wrap to 70% of diameter
    max_text_width = int(diameter * 0.7)
    wrapped_title = wrap_and_truncate_text(font_large_small, title, max_text_width, 1)
    
    # Move text down to account for larger cover
    text_offset = int(diameter * 0.05)  # 5% down (reduced to shift text up)
    title_y = cover_y + cover_size + 20 + text_offset  # Below the cover + offset
    for i, line in enumerate(wrapped_title):
        render_text_centered(renderer, font_large_small, line, circle_center_x, title_y + i * 48, 30, 30, 30, rotation, screen_width, screen_height)
    
    # Artist name below title
    wrapped_artist = wrap_and_truncate_text(font_medium_small, artist, max_text_width, 1)
    
    artist_y = title_y + 52 + (len(wrapped_title) - 1) * 48  # Below title
    for i, line in enumerate(wrapped_artist):
        render_text_centered(renderer, font_medium_small, line, circle_center_x, artist_y + i * 40, 100, 100, 100, rotation, screen_width, screen_height)
    
    # Clean up smaller fonts
    if font_large_small:
        sdlttf.TTF_CloseFont(font_large_small)
    if font_medium_small:
        sdlttf.TTF_CloseFont(font_medium_small)
    
    # Control buttons at the bottom of the circle
    button_size = int(diameter * 0.12)  # 12% of diameter
    button_spacing = int(diameter * 0.03)  # 3% of diameter
    button_y = circle_center_y + int(diameter * 0.32)  # Move buttons 3% up
    
    # Get button colors
    prev_color, play_color, next_color, like_color = get_button_colors(bw_buttons)
    
    # Load icon font for buttons
    font_icons_buttons, needs_font_cleanup = get_button_icon_font(minimal_buttons, font_icons, button_size * 0.6)
    
    # Render control buttons
    button_rects = render_control_buttons(
        renderer, button_y, button_size, button_spacing, circle_center_x, diameter,
        prev_color, play_color, next_color, like_color,
        font_icons_buttons, minimal_buttons, liked, no_control,
        rotation, screen_width, screen_height, border_radius=int(button_size * 0.35), hide_like_button=hide_like_button
    )
    
    if needs_font_cleanup:
        sdlttf.TTF_CloseFont(font_icons_buttons)
    
    return button_rects
