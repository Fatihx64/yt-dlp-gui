"""
YT-DLP GUI - FFmpeg Downloader
Auto-download FFmpeg if not present.
"""

import os
import zipfile
import shutil
import threading
from pathlib import Path
from typing import Optional, Callable
import urllib.request

from PySide6.QtCore import QObject, Signal

from .logger import get_logger


class FFmpegDownloaderSignals(QObject):
    """Signals for FFmpeg download progress."""
    progress = Signal(int)  # percentage
    finished = Signal(bool, str)  # success, message
    status = Signal(str)  # status message


class FFmpegDownloader:
    """Download and install FFmpeg automatically."""
    
    # FFmpeg download URL (Windows builds)
    FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    def __init__(self):
        self.logger = get_logger()
        self.signals = FFmpegDownloaderSignals()
        self._is_downloading = False
    
    def get_ffmpeg_dir(self) -> Path:
        """Get the directory where FFmpeg should be installed."""
        # Use bin folder next to the application
        import sys
        if getattr(sys, 'frozen', False):
            # Running as compiled
            app_dir = Path(sys.executable).parent
        else:
            # Running as script
            app_dir = Path(__file__).parent.parent.parent
        
        return app_dir / "bin"
    
    def get_ffmpeg_path(self) -> Optional[Path]:
        """Get path to ffmpeg.exe if it exists."""
        bin_dir = self.get_ffmpeg_dir()
        ffmpeg = bin_dir / "ffmpeg.exe"
        
        if ffmpeg.exists():
            return ffmpeg
        
        # Check if ffmpeg is in PATH
        import shutil as sh
        ffmpeg_in_path = sh.which("ffmpeg")
        if ffmpeg_in_path:
            return Path(ffmpeg_in_path)
        
        return None
    
    def is_installed(self) -> bool:
        """Check if FFmpeg is installed."""
        return self.get_ffmpeg_path() is not None
    
    def download(self, callback: Optional[Callable] = None):
        """Download FFmpeg in background thread."""
        if self._is_downloading:
            return
        
        self._is_downloading = True
        
        def _download():
            try:
                bin_dir = self.get_ffmpeg_dir()
                bin_dir.mkdir(parents=True, exist_ok=True)
                
                zip_path = bin_dir / "ffmpeg.zip"
                
                self.signals.status.emit("Downloading FFmpeg...")
                self.logger.info("Downloading FFmpeg...")
                
                # Download with progress
                def report_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = min(int(block_num * block_size * 100 / total_size), 100)
                        self.signals.progress.emit(percent)
                
                urllib.request.urlretrieve(self.FFMPEG_URL, zip_path, report_progress)
                
                self.signals.status.emit("Extracting FFmpeg...")
                self.logger.info("Extracting FFmpeg...")
                
                # Extract
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    # Find the bin folder inside the zip
                    for name in zf.namelist():
                        if name.endswith('ffmpeg.exe'):
                            # Extract just ffmpeg.exe
                            with zf.open(name) as src, open(bin_dir / "ffmpeg.exe", 'wb') as dst:
                                dst.write(src.read())
                        elif name.endswith('ffprobe.exe'):
                            with zf.open(name) as src, open(bin_dir / "ffprobe.exe", 'wb') as dst:
                                dst.write(src.read())
                
                # Clean up zip file
                zip_path.unlink()
                
                self.logger.info("FFmpeg installed successfully")
                self.signals.status.emit("FFmpeg installed!")
                self.signals.finished.emit(True, "FFmpeg installed successfully")
                
                if callback:
                    callback(True)
                    
            except Exception as e:
                self.logger.error(f"FFmpeg download failed: {e}")
                self.signals.status.emit(f"Failed: {e}")
                self.signals.finished.emit(False, str(e))
                
                if callback:
                    callback(False)
            finally:
                self._is_downloading = False
        
        thread = threading.Thread(target=_download, daemon=True)
        thread.start()


# Singleton instance
_downloader_instance: Optional[FFmpegDownloader] = None


def get_ffmpeg_downloader() -> FFmpegDownloader:
    """Get the FFmpeg downloader singleton."""
    global _downloader_instance
    if _downloader_instance is None:
        _downloader_instance = FFmpegDownloader()
    return _downloader_instance
