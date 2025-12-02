# Now Playing SDL

SDL2-based now playing display for music players.

## Features

- SDL2-based display with hardware acceleration
- Screen rotation support (0°, 90°, 180°, 270°)
- Touch-friendly button controls
- Album cover art display
- Material Design icons
- Multiple display modes (portrait/landscape)
- Customizable button layouts

## Installation

### From Debian Package

```bash
sudo dpkg -i nowplaying-sdl_0.1.0-1_all.deb
sudo apt-get install -f  # Install dependencies
```

### From Source

```bash
pip3 install .
```

## Usage

```bash
# Basic usage
nowplaying-sdl

# With rotation
nowplaying-sdl --rotation 90

# Portrait mode
nowplaying-sdl --portrait

# Landscape mode
nowplaying-sdl --landscape

# Minimal buttons (no background)
nowplaying-sdl --minimal-buttons

# No control buttons
nowplaying-sdl --no-control

# Black and white buttons
nowplaying-sdl --bw-buttons

# Specific display
nowplaying-sdl --display 1
```

## Dependencies

- Python 3.7+
- PySDL2
- libsdl2-2.0-0
- libsdl2-ttf-2.0-0
- libsdl2-image-2.0-0
- fonts-dejavu-core

## Building Debian Package

```bash
# Install build dependencies
sudo apt-get install debhelper dh-python python3-all python3-setuptools

# Build the package
dpkg-buildpackage -us -uc -b

# The package will be created in the parent directory
```

## License

MIT License - see debian/copyright for details

Material Icons fonts are licensed under Apache License 2.0 by Google Inc.
