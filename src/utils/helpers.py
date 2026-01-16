"""
YT-DLP GUI - Helper Utilities
Common utility functions used throughout the application.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def format_duration(seconds: int) -> str:
    """Convert seconds to HH:MM:SS format."""
    if seconds < 0:
        return "00:00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse_duration(time_str: str) -> int:
    """Parse HH:MM:SS or MM:SS format to seconds."""
    parts = time_str.strip().split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:
            return int(parts[0])
    except ValueError:
        pass
    return 0


def format_size(bytes_size: int) -> str:
    """Convert bytes to human-readable format."""
    if bytes_size < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_size)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.2f} {units[unit_index]}"


def format_speed(bytes_per_second: float) -> str:
    """Convert download speed to human-readable format."""
    return f"{format_size(int(bytes_per_second))}/s"


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename."""
    # Replace invalid Windows filename characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized or 'untitled'


def is_valid_url(url: str) -> bool:
    """Check if the string is a valid URL."""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(url_pattern.match(url))


def get_app_directory() -> Path:
    """Get the application's root directory.
    
    When running as compiled EXE, returns the directory containing the EXE.
    When running from source, returns the project root directory.
    """
    import sys
    
    # Check if running as compiled executable (PyInstaller)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running from source
        return Path(os.path.dirname(os.path.abspath(__file__))).parent.parent


def get_exe_directory() -> Path:
    """Get the directory containing the running executable.
    
    This is specifically for finding files relative to the EXE location,
    not the temp extraction directory that PyInstaller uses.
    """
    import sys
    
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return get_app_directory()


def get_bin_directory() -> Path:
    """Get the bin directory containing executables."""
    return get_app_directory() / 'bin'


def get_ytdlp_path() -> Optional[Path]:
    """Get the path to yt-dlp executable."""
    import sys
    
    # If running as EXE, check next to the executable first
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        
        # Check next to EXE
        exe_path = exe_dir / 'yt-dlp.exe'
        if exe_path.exists():
            return exe_path
        
        # Check in bin subfolder next to EXE
        bin_path = exe_dir / 'bin' / 'yt-dlp.exe'
        if bin_path.exists():
            return bin_path
    
    # Check in bin directory (source mode)
    bin_path = get_bin_directory() / 'yt-dlp.exe'
    if bin_path.exists():
        return bin_path
    
    # Check in app root
    root_path = get_app_directory() / 'yt-dlp.exe'
    if root_path.exists():
        return root_path
    
    # Check in PATH
    try:
        result = subprocess.run(
            ['where', 'yt-dlp'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            return Path(result.stdout.strip().split('\n')[0])
    except Exception:
        pass
    
    return None


def get_ffmpeg_path() -> Optional[Path]:
    """Get the path to ffmpeg executable."""
    import sys
    
    # If running as EXE, check next to the executable first
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        
        # Check next to EXE
        exe_path = exe_dir / 'ffmpeg.exe'
        if exe_path.exists():
            return exe_path
        
        # Check in bin subfolder next to EXE
        bin_path = exe_dir / 'bin' / 'ffmpeg.exe'
        if bin_path.exists():
            return bin_path
    
    # Check in bin directory (source mode)
    bin_path = get_bin_directory() / 'ffmpeg.exe'
    if bin_path.exists():
        return bin_path
    
    # Check in PATH
    try:
        result = subprocess.run(
            ['where', 'ffmpeg'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            return Path(result.stdout.strip().split('\n')[0])
    except Exception:
        pass
    
    return None


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_thumbnail_url(video_id: str, quality: str = 'maxresdefault') -> str:
    """Get YouTube thumbnail URL from video ID."""
    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"


def open_folder(path: Path):
    """Open folder in file explorer."""
    if path.is_file():
        path = path.parent
    
    if path.exists():
        os.startfile(str(path))
