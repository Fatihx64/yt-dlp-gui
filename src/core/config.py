"""
YT-DLP GUI - Configuration Management
Settings persistence and application configuration.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class DownloadSettings:
    """Download-related settings."""
    output_path: str = ""
    default_format: str = "best"  # best, bestvideo+bestaudio, bestaudio
    default_quality: str = "1080"  # 4k, 1080, 720, 480, 360
    embed_thumbnail: bool = False  # Default off - increases file size
    embed_metadata: bool = False   # Default off - single video download
    embed_subtitles: bool = False
    subtitle_languages: List[str] = field(default_factory=lambda: ["en"])
    concurrent_downloads: int = 3
    rate_limit: str = ""  # e.g., "1M" for 1MB/s
    
    def __post_init__(self):
        if not self.output_path:
            self.output_path = str(Path.home() / "Downloads")


@dataclass
class NetworkSettings:
    """Network-related settings."""
    proxy: str = ""
    retries: int = 10
    fragment_retries: int = 10
    timeout: int = 30
    use_aria2: bool = False


@dataclass
class UISettings:
    """UI-related settings."""
    theme: str = "dark"  # dark, light
    advanced_mode: bool = False
    window_width: int = 1200
    window_height: int = 800
    window_x: int = -1
    window_y: int = -1
    show_log_panel: bool = True
    log_panel_height: int = 150


@dataclass
class AppSettings:
    """Main application settings container."""
    download: DownloadSettings = field(default_factory=DownloadSettings)
    network: NetworkSettings = field(default_factory=NetworkSettings)
    ui: UISettings = field(default_factory=UISettings)
    recent_urls: List[str] = field(default_factory=list)
    recent_folders: List[str] = field(default_factory=list)
    
    def add_recent_url(self, url: str):
        """Add URL to recent list."""
        if url in self.recent_urls:
            self.recent_urls.remove(url)
        self.recent_urls.insert(0, url)
        self.recent_urls = self.recent_urls[:20]  # Keep last 20
    
    def add_recent_folder(self, folder: str):
        """Add folder to recent list."""
        if folder in self.recent_folders:
            self.recent_folders.remove(folder)
        self.recent_folders.insert(0, folder)
        self.recent_folders = self.recent_folders[:10]  # Keep last 10


class Config:
    """Configuration manager singleton."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._config_dir = self._get_config_directory()
        self._config_file = self._config_dir / "settings.json"
        self.settings = self._load_settings()
    
    def _get_config_directory(self) -> Path:
        """Get the configuration directory."""
        # Use app directory for portable mode
        app_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
        config_dir = app_dir / "config"
        config_dir.mkdir(exist_ok=True)
        return config_dir
    
    def _load_settings(self) -> AppSettings:
        """Load settings from file."""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Reconstruct nested dataclasses
                download = DownloadSettings(**data.get('download', {}))
                network = NetworkSettings(**data.get('network', {}))
                ui = UISettings(**data.get('ui', {}))
                
                return AppSettings(
                    download=download,
                    network=network,
                    ui=ui,
                    recent_urls=data.get('recent_urls', []),
                    recent_folders=data.get('recent_folders', [])
                )
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return AppSettings()
    
    def save(self):
        """Save current settings to file."""
        try:
            data = {
                'download': asdict(self.settings.download),
                'network': asdict(self.settings.network),
                'ui': asdict(self.settings.ui),
                'recent_urls': self.settings.recent_urls,
                'recent_folders': self.settings.recent_folders
            }
            
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def reset(self):
        """Reset settings to defaults."""
        self.settings = AppSettings()
        self.save()


# Global config accessor
def get_config() -> Config:
    """Get the singleton config instance."""
    return Config()
