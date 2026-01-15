"""
YT-DLP GUI - yt-dlp Wrapper
Command-line wrapper for yt-dlp with async execution and progress parsing.
"""

import json
import re
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal

from ..utils.helpers import get_ytdlp_path, get_ffmpeg_path
from ..utils.logger import get_logger


@dataclass
class VideoFormat:
    """Represents a video format option."""
    format_id: str
    ext: str
    resolution: str
    filesize: Optional[int] = None
    vcodec: str = ""
    acodec: str = ""
    fps: Optional[float] = None
    tbr: Optional[float] = None  # Total bitrate
    
    @property
    def is_video_only(self) -> bool:
        return self.acodec == "none" or not self.acodec
    
    @property
    def is_audio_only(self) -> bool:
        return self.vcodec == "none" or not self.vcodec
    
    @property
    def display_name(self) -> str:
        parts = [self.resolution or self.ext]
        if self.fps:
            parts.append(f"{int(self.fps)}fps")
        if self.vcodec and self.vcodec != "none":
            parts.append(self.vcodec)
        if self.filesize:
            from ..utils.helpers import format_size
            parts.append(f"~{format_size(self.filesize)}")
        return " | ".join(parts)


@dataclass
class VideoInfo:
    """Represents video metadata."""
    id: str
    title: str
    url: str
    thumbnail: str = ""
    duration: int = 0
    channel: str = ""
    upload_date: str = ""
    description: str = ""
    view_count: int = 0
    formats: List[VideoFormat] = field(default_factory=list)
    chapters: List[Dict] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VideoInfo':
        """Create VideoInfo from yt-dlp JSON output."""
        formats = []
        for fmt in data.get('formats', []):
            formats.append(VideoFormat(
                format_id=str(fmt.get('format_id', '')),
                ext=fmt.get('ext', ''),
                resolution=fmt.get('resolution', fmt.get('format_note', '')),
                filesize=fmt.get('filesize') or fmt.get('filesize_approx'),
                vcodec=fmt.get('vcodec', ''),
                acodec=fmt.get('acodec', ''),
                fps=fmt.get('fps'),
                tbr=fmt.get('tbr')
            ))
        
        return cls(
            id=data.get('id', ''),
            title=data.get('title', 'Unknown'),
            url=data.get('webpage_url', data.get('url', '')),
            thumbnail=data.get('thumbnail', ''),
            duration=int(data.get('duration', 0)),
            channel=data.get('channel', data.get('uploader', '')),
            upload_date=data.get('upload_date', ''),
            description=data.get('description', ''),
            view_count=int(data.get('view_count', 0)),
            formats=formats,
            chapters=data.get('chapters', [])
        )


@dataclass
class DownloadProgress:
    """Download progress information."""
    status: str = "waiting"  # waiting, downloading, processing, finished, error
    percent: float = 0.0
    speed: str = ""
    eta: str = ""
    downloaded: str = ""
    total: str = ""
    filename: str = ""
    error_message: str = ""


class YTDLPSignals(QObject):
    """Qt signals for yt-dlp operations."""
    progress = Signal(DownloadProgress)
    finished = Signal(bool, str)  # success, message/filepath
    info_ready = Signal(VideoInfo)
    error = Signal(str)


class YTDLPWrapper:
    """Wrapper for yt-dlp command-line operations."""
    
    def __init__(self):
        self.logger = get_logger()
        self.ytdlp_path = get_ytdlp_path()
        self.ffmpeg_path = get_ffmpeg_path()
        self.signals = YTDLPSignals()
        self._active_processes: Dict[str, subprocess.Popen] = {}
        self._cancelled: Dict[str, bool] = {}
    
    def _get_base_args(self) -> List[str]:
        """Get base command arguments."""
        args = [str(self.ytdlp_path)]
        
        # Check FFmpeg path dynamically (might be installed after app start)
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            args.extend(['--ffmpeg-location', str(ffmpeg_path.parent)])
        
        args.extend([
            '--no-playlist',
            '--encoding', 'utf-8',
        ])
        
        return args
    
    def check_available(self) -> bool:
        """Check if yt-dlp is available."""
        return self.ytdlp_path is not None and self.ytdlp_path.exists()
    
    def get_version(self) -> Optional[str]:
        """Get yt-dlp version."""
        if not self.check_available():
            return None
        
        try:
            result = subprocess.run(
                [str(self.ytdlp_path), '--version'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error getting yt-dlp version: {e}")
            return None
    
    def extract_info(self, url: str, callback: Optional[Callable] = None) -> Optional[VideoInfo]:
        """Extract video information from URL."""
        if not self.check_available():
            self.signals.error.emit("yt-dlp not found")
            return None
        
        def _extract():
            try:
                args = self._get_base_args() + [
                    '--dump-json',
                    '--no-download',
                    url
                ]
                
                self.logger.info(f"Extracting info from: {url}")
                
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or "Unknown error"
                    self.logger.error(f"Extract info failed: {error_msg}")
                    self.signals.error.emit(error_msg)
                    return
                
                data = json.loads(result.stdout)
                info = VideoInfo.from_dict(data)
                self.logger.info(f"Extracted info: {info.title}")
                self.signals.info_ready.emit(info)
                
                if callback:
                    callback(info)
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parse error: {e}")
                self.signals.error.emit(f"Failed to parse video info: {e}")
            except Exception as e:
                self.logger.error(f"Extract info error: {e}")
                self.signals.error.emit(str(e))
        
        thread = threading.Thread(target=_extract, daemon=True)
        thread.start()
        return None
    
    def download(
        self,
        url: str,
        output_path: str,
        format_spec: str = "best",
        options: Optional[Dict] = None,
        task_id: Optional[str] = None
    ):
        """Start download with progress tracking."""
        if not self.check_available():
            self.signals.error.emit("yt-dlp not found")
            return
        
        options = options or {}
        task_id = task_id or url
        self._cancelled[task_id] = False
        
        def _download():
            try:
                output_template = str(Path(output_path) / "%(title)s.%(ext)s")
                
                args = self._get_base_args() + [
                    '-f', format_spec,
                    '-o', output_template,
                    '--newline',
                    '--progress',
                ]
                
                # Add optional arguments
                if options.get('embed_thumbnail'):
                    args.append('--embed-thumbnail')
                
                if options.get('embed_metadata'):
                    args.append('--embed-metadata')
                
                if options.get('embed_subtitles'):
                    args.extend(['--embed-subs', '--sub-langs', ','.join(options.get('subtitle_langs', ['en']))])
                
                if options.get('clip_start') or options.get('clip_end'):
                    # Build download section string: *start-end
                    start = options.get('clip_start', '0:00')
                    end = options.get('clip_end', '')
                    
                    # Format: "*start-end" or "*start-" if no end
                    if end:
                        section = f"*{start}-{end}"
                    else:
                        section = f"*{start}-"
                    
                    args.extend(['--download-sections', section])
                    # Force keyframes for accurate cuts
                    args.append('--force-keyframes-at-cuts')
                
                if options.get('rate_limit'):
                    args.extend(['-r', options['rate_limit']])
                
                if options.get('proxy'):
                    args.extend(['--proxy', options['proxy']])
                
                if options.get('cookies_file'):
                    args.extend(['--cookies', options['cookies_file']])
                
                # Add extra arguments (like --extract-audio for audio formats)
                if options.get('extra_args'):
                    args.extend(options['extra_args'])
                
                # Force container format (MP4, MKV, etc.)
                if options.get('merge_output_format'):
                    args.extend(['--merge-output-format', options['merge_output_format']])
                
                args.append(url)
                
                self.logger.info(f"Starting download: {url}")
                self.logger.debug(f"Command: {' '.join(args)}")
                
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                self._active_processes[task_id] = process
                progress = DownloadProgress(status="downloading")
                error_lines = []  # Collect error messages
                
                for line in process.stdout:
                    if self._cancelled.get(task_id):
                        process.terminate()
                        self.signals.finished.emit(False, "Cancelled")
                        return
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Capture error lines
                    if 'ERROR:' in line or 'error:' in line.lower():
                        error_lines.append(line)
                        self.logger.error(line)
                    
                    # Parse download progress
                    progress = self._parse_progress_line(line, progress)
                    self.signals.progress.emit(progress)
                
                process.wait()
                
                if process.returncode == 0:
                    self.logger.info("Download completed successfully")
                    progress.status = "finished"
                    progress.percent = 100.0
                    self.signals.progress.emit(progress)
                    self.signals.finished.emit(True, output_path)
                else:
                    # Include actual error messages if captured
                    if error_lines:
                        error_msg = "\n".join(error_lines[-3:])  # Last 3 errors
                    else:
                        error_msg = f"Download failed with exit code {process.returncode}"
                    self.logger.error(f"Download failed: {error_msg}")
                    self.signals.finished.emit(False, error_msg)
                
            except Exception as e:
                self.logger.error(f"Download error: {e}")
                self.signals.error.emit(str(e))
                self.signals.finished.emit(False, str(e))
            finally:
                self._active_processes.pop(task_id, None)
                self._cancelled.pop(task_id, None)
        
        thread = threading.Thread(target=_download, daemon=True)
        thread.start()
    
    def _parse_progress_line(self, line: str, progress: DownloadProgress) -> DownloadProgress:
        """Parse a progress line from yt-dlp output."""
        # [download] 45.5% of 125.32MiB at 2.35MiB/s ETA 00:25
        download_match = re.search(
            r'\[download\]\s+(\d+\.?\d*)%\s+of\s+~?(\S+)\s+at\s+(\S+)\s+ETA\s+(\S+)',
            line
        )
        if download_match:
            progress.percent = float(download_match.group(1))
            progress.total = download_match.group(2)
            progress.speed = download_match.group(3)
            progress.eta = download_match.group(4)
            progress.status = "downloading"
            return progress
        
        # [download] Destination: filename.mp4
        dest_match = re.search(r'\[download\]\s+Destination:\s+(.+)', line)
        if dest_match:
            progress.filename = dest_match.group(1)
            return progress
        
        # [download] 100% of 125.32MiB in 00:53
        complete_match = re.search(r'\[download\]\s+100%\s+of\s+(\S+)', line)
        if complete_match:
            progress.percent = 100.0
            progress.total = complete_match.group(1)
            progress.status = "processing"
            return progress
        
        # [Merger] Merging formats...
        if '[Merger]' in line or '[ExtractAudio]' in line:
            progress.status = "processing"
            return progress
        
        # Error handling
        if 'ERROR:' in line:
            progress.status = "error"
            progress.error_message = line.replace('ERROR:', '').strip()
            return progress
        
        return progress
    
    def cancel(self, task_id: str):
        """Cancel a download task."""
        self._cancelled[task_id] = True
        if task_id in self._active_processes:
            try:
                self._active_processes[task_id].terminate()
            except Exception:
                pass
    
    def cancel_all(self):
        """Cancel all active downloads."""
        for task_id in list(self._active_processes.keys()):
            self.cancel(task_id)
