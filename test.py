#!/usr/bin/env python3
"""Simple test to debug text rotation"""

import sys
import argparse
import sdl2
import sdl2.ext
import sdl2.sdlttf as sdlttf


def main():
    parser = argparse.ArgumentParser(description='Test text rotation')
    parser.add_argument(
        '--rotation',
        type=int,
        choices=[0, 90, 180, 270],
        default=0,
        help='Rotation angle in degrees (0, 90, 180, or 270)'
    )
    args = parser.parse_args()
    
    # Initialize SDL
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(f"SDL_Init Error: {sdl2.SDL_GetError()}")
        return 1
    
    # Initialize SDL_ttf
    if sdlttf.TTF_Init() != 0:
        print(f"TTF_Init Error: {sdl2.SDL_GetError()}")
        sdl2.SDL_Quit()
        return 1
    
    # Get display mode
    display_mode = sdl2.SDL_DisplayMode()
    if sdl2.SDL_GetDesktopDisplayMode(0, display_mode) != 0:
        print(f"Error getting display mode: {sdl2.SDL_GetError()}")
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()
        return 1
    
    screen_width = display_mode.w
    screen_height = display_mode.h
    
    # For 90/270 rotation, swap layout dimensions
    if args.rotation in (90, 270):
        layout_width = screen_height
        layout_height = screen_width
    else:
        layout_width = screen_width
        layout_height = screen_height
    
    print(f"Screen: {screen_width}x{screen_height}, Layout: {layout_width}x{layout_height}, Rotation: {args.rotation}°")
    
    # Create window
    window = sdl2.SDL_CreateWindow(
        b"Text Rotation Test",
        sdl2.SDL_WINDOWPOS_UNDEFINED,
        sdl2.SDL_WINDOWPOS_UNDEFINED,
        screen_width,
        screen_height,
        sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_FULLSCREEN
    )
    
    if not window:
        print(f"Window creation error: {sdl2.SDL_GetError()}")
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()
        return 1
    
    # Create renderer
    renderer = sdl2.SDL_CreateRenderer(
        window, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
    )
    
    if not renderer:
        print(f"Renderer creation error: {sdl2.SDL_GetError()}")
        sdl2.SDL_DestroyWindow(window)
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()
        return 1
    
    # Load font
    font = sdlttf.TTF_OpenFont(b"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    if not font:
        print(f"Font loading error: {sdl2.SDL_GetError()}")
        sdl2.SDL_DestroyRenderer(renderer)
        sdl2.SDL_DestroyWindow(window)
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()
        return 1
    
    # Main loop
    running = True
    event = sdl2.SDL_Event()
    
    while running:
        while sdl2.SDL_PollEvent(event) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE or event.key.keysym.sym == sdl2.SDLK_q:
                    running = False
        
        # Clear screen to white
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
        sdl2.SDL_RenderClear(renderer)
        
        # Render text
        text = "this is a test"
        color = sdl2.SDL_Color(0, 0, 0, 255)
        surface = sdlttf.TTF_RenderText_Blended(font, text.encode('utf-8'), color)
        
        if surface:
            texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
            if texture:
                text_width = surface.contents.w
                text_height = surface.contents.h
                
                # Calculate center position in layout coordinates
                center_x = layout_width // 2
                center_y = layout_height // 2
                
                # Position text (top-left corner)
                x = center_x - text_width // 2
                y = center_y - text_height // 2
                
                print(f"Text: {text_width}x{text_height}, Center: ({center_x},{center_y}), Pos: ({x},{y})")
                
                # Draw a big red box in the center to visualize
                center_box = sdl2.SDL_Rect(screen_width // 2 - 50, screen_height // 2 - 50, 100, 100)
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255)
                sdl2.SDL_RenderFillRect(renderer, center_box)
                
                # Transform coordinates if rotated
                if args.rotation != 0:
                    if args.rotation == 90:
                        # We want the final rotated text centered at screen center (360, 640)
                        # After rotation, dimensions become: height=84, width=505
                        desired_center_x = screen_width // 2   # 360
                        desired_center_y = screen_height // 2  # 640
                        
                        # With center pivot, the center of the rect becomes the rotation center
                        # Place rect so its center is where we want the rotated center
                        # The rect center is at (x + w/2, y + h/2)
                        # We want this at (desired_center_x, desired_center_y)
                        
                        # For 90° rotation with center pivot:
                        # The center point stays fixed, dimensions swap visually
                        # So place rect center at desired center
                        tx = desired_center_x - text_width // 2
                        ty = desired_center_y - text_height // 2
                        
                        pivot = sdl2.SDL_Point(text_width // 2, text_height // 2)
                        
                    elif args.rotation == 180:
                        tx = (screen_width - text_width) // 2
                        ty = (screen_height - text_height) // 2
                        pivot = sdl2.SDL_Point(text_width // 2, text_height // 2)
                    elif args.rotation == 270:
                        desired_center_x = screen_width // 2
                        desired_center_y = screen_height // 2
                        tx = desired_center_x - text_width // 2
                        ty = desired_center_y - text_height // 2
                        pivot = sdl2.SDL_Point(text_width // 2, text_height // 2)
                    
                    print(f"Rect at: ({tx},{ty}) size {text_width}x{text_height}, pivot at center, rotation={args.rotation}")
                    rect = sdl2.SDL_Rect(tx, ty, text_width, text_height)
                    
                    # Draw the actual rect position (pre-rotation) - BLUE
                    sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 255, 180)
                    sdl2.SDL_RenderFillRect(renderer, rect)
                    
                    # Draw where we EXPECT the text to be after rotation - GREEN
                    if args.rotation == 90:
                        expected_x = (screen_width - text_height) // 2
                        expected_y = (screen_height - text_width) // 2
                        expected_rect = sdl2.SDL_Rect(expected_x, expected_y, text_height, text_width)
                    else:
                        expected_rect = sdl2.SDL_Rect((screen_width - text_width) // 2, (screen_height - text_height) // 2, text_width, text_height)
                    
                    sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 0, 255)
                    sdl2.SDL_RenderDrawRect(renderer, expected_rect)
                    
                    # Rotate with center pivot
                    sdl2.SDL_RenderCopyEx(renderer, texture, None, rect, args.rotation, pivot, sdl2.SDL_FLIP_NONE)
                else:
                    rect = sdl2.SDL_Rect(x, y, text_width, text_height)
                    
                    # Draw bounding box for debugging
                    sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255)
                    sdl2.SDL_RenderDrawRect(renderer, rect)
                    
                    sdl2.SDL_RenderCopy(renderer, texture, None, rect)
                
                sdl2.SDL_DestroyTexture(texture)
            
            sdl2.SDL_FreeSurface(surface)
        
        sdl2.SDL_RenderPresent(renderer)
        sdl2.SDL_Delay(16)
    
    # Cleanup
    sdlttf.TTF_CloseFont(font)
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdlttf.TTF_Quit()
    sdl2.SDL_Quit()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
