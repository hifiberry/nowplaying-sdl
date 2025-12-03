"""
SDL2 Rendering utilities with rotation support
"""

import sdl2
import sdl2.sdlttf as sdlttf


def transform_coordinates(x, y, width, height, screen_width, screen_height, rotation):
    """Transform coordinates based on rotation angle
    
    Args:
        x, y: Original coordinates
        width, height: Width and height of the element being drawn
        screen_width, screen_height: Screen dimensions
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        
    Returns:
        Transformed (x, y) coordinates
    """
    if rotation == 0:
        result = (x, y)
    elif rotation == 90:
        # Rotate 90° clockwise: origin moves to top-right
        # Point (x,y) in landscape becomes (screen_height - y - height, x) in portrait
        result = (screen_height - y - height, x)
    elif rotation == 180:
        # Rotate 180°: origin moves to bottom-right
        result = (screen_width - x - width, screen_height - y - height)
    elif rotation == 270:
        # Rotate 270° clockwise (90° counter-clockwise): origin moves to bottom-left  
        # Point (x,y) in landscape becomes (y, screen_width - x - width) in portrait
        result = (y, screen_width - x - width)
    else:
        result = (x, y)
    
    return result


def draw_circle(renderer, center_x, center_y, radius, r, g, b, a, thickness=1):
    """Draw a circle outline using Bresenham's circle algorithm
    
    Args:
        renderer: SDL2 renderer
        center_x, center_y: Center position
        radius: Circle radius
        r, g, b, a: Color components
        thickness: Line thickness (1 for thin line)
    """
    sdl2.SDL_SetRenderDrawColor(renderer, r, g, b, a)
    
    # Draw circle using midpoint circle algorithm
    for t in range(thickness):
        r_current = radius + t
        x = r_current
        y = 0
        decision = 1 - x
        
        while x >= y:
            # Draw 8 octants
            sdl2.SDL_RenderDrawPoint(renderer, center_x + x, center_y + y)
            sdl2.SDL_RenderDrawPoint(renderer, center_x + y, center_y + x)
            sdl2.SDL_RenderDrawPoint(renderer, center_x - y, center_y + x)
            sdl2.SDL_RenderDrawPoint(renderer, center_x - x, center_y + y)
            sdl2.SDL_RenderDrawPoint(renderer, center_x - x, center_y - y)
            sdl2.SDL_RenderDrawPoint(renderer, center_x - y, center_y - x)
            sdl2.SDL_RenderDrawPoint(renderer, center_x + y, center_y - x)
            sdl2.SDL_RenderDrawPoint(renderer, center_x + x, center_y - y)
            
            y += 1
            if decision <= 0:
                decision += 2 * y + 1
            else:
                x -= 1
                decision += 2 * (y - x) + 1


def draw_rounded_rect(renderer, x, y, w, h, radius, r, g, b, a, rotation=0, screen_width=0, screen_height=0):
    """Draw a filled rounded rectangle with optional rotation
    
    Args:
        renderer: SDL2 renderer
        x, y: Position
        w, h: Width and height
        radius: Corner radius
        r, g, b, a: Color components
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        screen_width, screen_height: Physical screen dimensions (required for rotation)
    """
    # Transform coordinates based on rotation
    if rotation in (90, 270):
        # For 90° and 270° rotations, dimensions are swapped
        # Need to use swapped screen dimensions for the transform
        tx, ty = transform_coordinates(x, y, h, w, screen_height, screen_width, rotation)
        x, y, w, h = tx, ty, h, w
    elif rotation == 180:
        # For 180° rotation, transform coordinates
        tx, ty = transform_coordinates(x, y, w, h, screen_width, screen_height, rotation)
        x, y = tx, ty
    
    # Direct rendering after coordinate transformation
    
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


def render_text(renderer, font, text, x, y, r, g, b, rotation=0, screen_width=0, screen_height=0):
    """Render text at the given position with optional rotation
    
    Args:
        renderer: SDL2 renderer
        font: TTF font
        text: Text to render
        x, y: Position
        r, g, b: Color components
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        screen_width, screen_height: Screen dimensions (required for rotation)
    """
    color = sdl2.SDL_Color(r, g, b, 255)
    surface = sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
    if not surface:
        return
    
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    if texture:
        if rotation != 0:
            # Input x,y are in layout coordinates, need to map to physical screen
            # For 90/270: layout width->screen height, layout height->screen width
            if rotation in (90, 270):
                # Transform layout position to physical screen position
                layout_center_x = x + surface.contents.w // 2
                layout_center_y = y + surface.contents.h // 2
                
                # Map from layout coords to screen coords
                # Layout is 1280x720, screen is 720x1280
                # For 90° clockwise: layout (x,y) -> screen (screen_width-y, x)
                # layout_x in [0, 1280] -> screen_y in [0, 1280]
                # layout_y in [0, 720] -> screen_x in [720, 0] (inverted)
                if rotation == 90:
                    center_x = screen_width - layout_center_y
                    center_y = layout_center_x
                else:  # 270
                    center_x = layout_center_y
                    center_y = screen_height - layout_center_x
            elif rotation == 180:
                # For 180°: flip both x and y
                layout_center_x = x + surface.contents.w // 2
                layout_center_y = y + surface.contents.h // 2
                center_x = screen_width - layout_center_x
                center_y = screen_height - layout_center_y
            else:
                center_x = x + surface.contents.w // 2
                center_y = y + surface.contents.h // 2
            
            # Place rect so its center is at computed center position
            rect = sdl2.SDL_Rect(center_x - surface.contents.w // 2, center_y - surface.contents.h // 2, 
                                surface.contents.w, surface.contents.h)
            
            print(f"render_text: text='{text[:20]}' layout pos=({x},{y}) screen center=({center_x},{center_y}) size={surface.contents.w}x{surface.contents.h} rect=({rect.x},{rect.y}) rotation={rotation}")
            
            center = sdl2.SDL_Point(surface.contents.w // 2, surface.contents.h // 2)
            sdl2.SDL_RenderCopyEx(renderer, texture, None, rect, rotation, center, sdl2.SDL_FLIP_NONE)
        else:
            rect = sdl2.SDL_Rect(x, y, surface.contents.w, surface.contents.h)
            sdl2.SDL_RenderCopy(renderer, texture, None, rect)
        
        sdl2.SDL_DestroyTexture(texture)
    
    sdl2.SDL_FreeSurface(surface)


def render_text_centered(renderer, font, text, center_x, center_y, r, g, b, rotation=0, screen_width=0, screen_height=0):
    """Render text centered at the given position with optional rotation
    
    Args:
        renderer: SDL2 renderer
        font: TTF font
        text: Text to render
        center_x, center_y: Center position
        r, g, b: Color components
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        screen_width, screen_height: Screen dimensions (required for rotation)
    """
    color = sdl2.SDL_Color(r, g, b, 255)
    surface = sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
    if not surface:
        return
    
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    if texture:
        if rotation != 0:
            # Input center_x, center_y are in layout coordinates
            # Map from layout coords to screen coords
            if rotation in (90, 270):
                # Layout is 1280x720, screen is 720x1280
                # For 90° clockwise: layout (x,y) -> screen (screen_width-y, x)
                # layout_x in [0, 1280] -> screen_y in [0, 1280]
                # layout_y in [0, 720] -> screen_x in [720, 0] (inverted)
                if rotation == 90:
                    screen_center_x = screen_width - center_y
                    screen_center_y = center_x
                else:  # 270
                    screen_center_x = center_y
                    screen_center_y = screen_height - center_x
            elif rotation == 180:
                # For 180°: flip both x and y
                screen_center_x = screen_width - center_x
                screen_center_y = screen_height - center_y
            else:
                screen_center_x = center_x
                screen_center_y = center_y
            
            # Place rect so its center is at screen center position
            rect = sdl2.SDL_Rect(screen_center_x - surface.contents.w // 2, screen_center_y - surface.contents.h // 2,
                                surface.contents.w, surface.contents.h)
            
            center = sdl2.SDL_Point(surface.contents.w // 2, surface.contents.h // 2)
            sdl2.SDL_RenderCopyEx(renderer, texture, None, rect, rotation, center, sdl2.SDL_FLIP_NONE)
        else:
            # Center the text (no rotation)
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


def render_wrapped_text_centered(renderer, font, text, center_x, y, max_width, r, g, b, max_lines=2, rotation=0, width=0, height=0):
    """Render wrapped text centered horizontally with optional rotation
    
    Args:
        renderer: SDL2 renderer
        font: TTF font
        text: Text to render
        center_x: Horizontal center position
        y: Vertical position
        max_width: Maximum width for text
        r, g, b: Color components
        max_lines: Maximum number of lines
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        width, height: Screen dimensions (required for rotation)
        
    Returns:
        Total height of rendered text
    """
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
        render_text_centered(renderer, font, line, center_x, y + i * line_height, r, g, b, rotation, width, height)
    
    return len(lines) * line_height
