#!/usr/bin/env python3
"""Setup script for nowplaying-sdl package"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README if it exists
this_directory = Path(__file__).parent
long_description = """
Now Playing Display - SDL2-based music player display

A simple SDL2-based display for showing currently playing music information
with support for rotation and touch controls.
"""

setup(
    name='nowplaying-sdl',
    version='0.1.0',
    description='SDL2-based now playing display for music players',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='HiFiBerry',
    author_email='info@hifiberry.com',
    url='https://github.com/hifiberry/nowplaying-sdl',
    packages=find_packages(),
    package_data={
        'nowplaying_sdl': [
            'fonts/*.ttf',
            '*.jpg',
        ],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'nowplaying-sdl=nowplaying_sdl:main',
        ],
    },
    python_requires='>=3.7',
    install_requires=[
        'PySDL2>=0.9.7',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
