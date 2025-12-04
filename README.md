# Now Playing SDL

SDL2-based now playing display for music players.

## Features

- SDL2-based display with hardware acceleration
- Screen rotation support (0°, 90°, 180°, 270°)
- Touch-friendly button controls
- Album cover art display
- Material Design icons
- Multiple display modes (portrait/landscape/circle)
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

## Configuration

The application can be configured via a configuration file or command-line arguments. Command-line arguments take precedence over config file settings.

### Config File Locations

The application looks for configuration files in this order:
1. Path specified with `--config` option
2. `/etc/nowplaying_sdl.conf` (if running as root)
3. `~/.config/nowplaying_sdl.conf` (user config)
4. `/etc/nowplaying_sdl.conf` (fallback)

A default configuration file is installed to `/usr/share/nowplaying-sdl/nowplaying_sdl.conf` which can be copied to one of the above locations and customized.

### Example Configuration

```ini
[nowplaying]
display = 0
rotation = 90
api_url = http://localhost:1080/api
# Orientation/Layout mode (use one or neither for auto-detect)
# portrait = false
# landscape = false
# circle = false
bw_buttons = false
no_control = false
minimal_buttons = false
liked = false
demo = false
```

### Display Configuration Examples

To configure the displayy add to `/boot/firmware/config.txt`:

**For 7-inch Touch Display 2:**
```ini
dtoverlay=vc4-kms-dsi-ili9881-7inch
```

**For 5-inch Touch Display 2:**
```ini
dtoverlay=vc4-kms-dsi-ili9881-5inch
```

** Waveshare Round LCD (720x720)
For Waveshare 1.28" or similar round displays in circle mode:

```ini
dtoverlay=vc4-kms-dsi-waveshare-panel-v2,4_0_inch_c
```

### Systemd Service

A systemd user service is provided for automatic startup:

```bash
# Enable and start the service
systemctl --user enable nowplaying-sdl
systemctl --user start nowplaying-sdl

# Check status
systemctl --user status nowplaying-sdl
```

## Usage

```bash
# Basic usage (uses config file)
nowplaying-sdl

# Use specific config file
nowplaying-sdl --config /path/to/config.conf

# Override config with command-line options
nowplaying-sdl --rotation 90

# Portrait mode
nowplaying-sdl --portrait

# Landscape mode
nowplaying-sdl --landscape

# Circle mode (circular layout for round displays)
nowplaying-sdl --circle

# Minimal buttons (no background)
nowplaying-sdl --minimal-buttons

# Volume slider (portrait/landscape only)
nowplaying-sdl --volume-slider

# No control buttons
nowplaying-sdl --no-control

# Black and white buttons
nowplaying-sdl --bw-buttons

# Specific display
nowplaying-sdl --display 1

# Demo mode (sample data)
nowplaying-sdl --demo

# Custom API URL
nowplaying-sdl --api-url http://192.168.1.100:1080/api
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
