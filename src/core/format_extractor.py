"""
YT-DLP GUI - Format Extractor
Handle video format extraction and quality selection.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .ytdlp_wrapper import VideoFormat, VideoInfo


@dataclass
class QualityOption:
    """Represents a quality selection option for the UI."""
    label: str
    format_spec: str
    description: str = ""
    extra_args: List[str] = field(default_factory=list)


class FormatExtractor:
    """Handles format extraction and quality selection logic."""
    
    # Standard quality presets
    QUALITY_PRESETS = {
        "best": QualityOption("Best Quality", "bestvideo+bestaudio/best", "Highest available quality"),
        "4k": QualityOption("4K (2160p)", "bestvideo[height<=2160]+bestaudio/best[height<=2160]", "Ultra HD"),
        "1080": QualityOption("1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]", "Full HD"),
        "720": QualityOption("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]", "HD"),
        "480": QualityOption("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]", "SD"),
        "360": QualityOption("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]", "Low"),
        "worst": QualityOption("Worst Quality", "worstvideo+worstaudio/worst", "Smallest file size"),
    }
    
    # Format type presets - separated format_spec and extra_args
    FORMAT_PRESETS = {
        "video_audio": QualityOption(
            "Video + Audio", 
            "bestvideo+bestaudio/best", 
            "Complete video with audio"
        ),
        "video_only": QualityOption(
            "Video Only", 
            "bestvideo", 
            "Video without audio"
        ),
        "audio_mp3": QualityOption(
            "Audio (MP3)", 
            "bestaudio", 
            "Audio converted to MP3",
            ["--extract-audio", "--audio-format", "mp3"]
        ),
        "audio_m4a": QualityOption(
            "Audio (M4A)", 
            "bestaudio[ext=m4a]/bestaudio", 
            "Audio in M4A format",
            ["--extract-audio", "--audio-format", "m4a"]
        ),
        "audio_opus": QualityOption(
            "Audio (Opus)", 
            "bestaudio", 
            "Audio in Opus format",
            ["--extract-audio", "--audio-format", "opus"]
        ),
        "audio_best": QualityOption(
            "Audio (Best)", 
            "bestaudio", 
            "Best available audio",
            ["--extract-audio"]
        ),
    }
    
    @classmethod
    def get_quality_options(cls) -> List[QualityOption]:
        """Get all quality preset options."""
        return list(cls.QUALITY_PRESETS.values())
    
    @classmethod
    def get_format_options(cls) -> List[QualityOption]:
        """Get all format preset options."""
        return list(cls.FORMAT_PRESETS.values())
    
    @classmethod
    def get_quality_by_key(cls, key: str) -> Optional[QualityOption]:
        """Get quality option by key."""
        return cls.QUALITY_PRESETS.get(key)
    
    @classmethod
    def get_format_by_key(cls, key: str) -> Optional[QualityOption]:
        """Get format option by key."""
        return cls.FORMAT_PRESETS.get(key)
    
    @classmethod
    def build_format_spec(cls, format_type: str, quality: str) -> str:
        """Build format specification string (only the -f argument)."""
        # Handle audio-only formats
        if format_type.startswith("audio_"):
            format_opt = cls.FORMAT_PRESETS.get(format_type)
            if format_opt:
                return format_opt.format_spec
            return "bestaudio"
        
        # Handle video formats with quality
        quality_opt = cls.QUALITY_PRESETS.get(quality)
        if quality_opt:
            return quality_opt.format_spec
        
        return "bestvideo+bestaudio/best"
    
    @classmethod
    def get_extra_args(cls, format_type: str) -> List[str]:
        """Get extra arguments for a format type (like --extract-audio)."""
        format_opt = cls.FORMAT_PRESETS.get(format_type)
        if format_opt and format_opt.extra_args:
            return format_opt.extra_args
        return []
    
    @classmethod
    def filter_formats_by_type(cls, formats: List[VideoFormat], format_type: str) -> List[VideoFormat]:
        """Filter formats by type (video, audio, or both)."""
        if format_type == "video_only":
            return [f for f in formats if f.is_video_only]
        elif format_type.startswith("audio_"):
            return [f for f in formats if f.is_audio_only]
        else:
            return formats
    
    @classmethod
    def get_available_qualities(cls, info: VideoInfo) -> List[str]:
        """Get available quality options based on video formats."""
        available = set()
        
        for fmt in info.formats:
            if fmt.resolution:
                # Extract height from resolution string
                try:
                    if 'x' in fmt.resolution:
                        height = int(fmt.resolution.split('x')[1])
                    elif fmt.resolution.endswith('p'):
                        height = int(fmt.resolution[:-1])
                    else:
                        continue
                    
                    if height >= 2160:
                        available.add("4k")
                    if height >= 1080:
                        available.add("1080")
                    if height >= 720:
                        available.add("720")
                    if height >= 480:
                        available.add("480")
                    if height >= 360:
                        available.add("360")
                except ValueError:
                    continue
        
        # Always include best and worst
        available.add("best")
        available.add("worst")
        
        # Sort by quality (best first)
        order = ["best", "4k", "1080", "720", "480", "360", "worst"]
        return [q for q in order if q in available]
    
    @classmethod
    def get_best_format_for_quality(cls, info: VideoInfo, target_quality: str) -> Tuple[str, str]:
        """Get the best format ID and spec for a target quality."""
        heights = {
            "4k": 2160,
            "1080": 1080,
            "720": 720,
            "480": 480,
            "360": 360
        }
        
        target_height = heights.get(target_quality)
        if not target_height:
            return "best", "bestvideo+bestaudio/best"
        
        # Find best video format at or below target height
        video_formats = [f for f in info.formats if not f.is_audio_only]
        best_video = None
        
        for fmt in video_formats:
            try:
                if 'x' in fmt.resolution:
                    height = int(fmt.resolution.split('x')[1])
                elif fmt.resolution.endswith('p'):
                    height = int(fmt.resolution[:-1])
                else:
                    continue
                
                if height <= target_height:
                    if best_video is None:
                        best_video = (fmt, height)
                    elif height > best_video[1]:
                        best_video = (fmt, height)
            except (ValueError, AttributeError):
                continue
        
        if best_video:
            return best_video[0].format_id, f"{best_video[0].format_id}+bestaudio/best"
        
        return "best", "bestvideo+bestaudio/best"
    
    @classmethod
    def estimate_file_size(cls, info: VideoInfo, format_spec: str) -> Optional[int]:
        """Estimate file size for a format specification."""
        total_size = 0
        
        for fmt in info.formats:
            if fmt.format_id in format_spec or format_spec == "best":
                if fmt.filesize:
                    total_size += fmt.filesize
        
        return total_size if total_size > 0 else None
