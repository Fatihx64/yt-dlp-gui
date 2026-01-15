"""
YT-DLP GUI - Preview Widget
Video thumbnail and metadata preview component.
"""

import requests
from io import BytesIO
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap, QImage

from ..core.ytdlp_wrapper import VideoInfo
from ..utils.helpers import format_duration, format_size


class ThumbnailLoader(QThread):
    """Background thread for loading thumbnails."""
    loaded = Signal(QPixmap)
    error = Signal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            
            image_data = BytesIO(response.content)
            image = QImage()
            image.loadFromData(image_data.read())
            
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                self.loaded.emit(pixmap)
            else:
                self.error.emit("Failed to load image")
        except Exception as e:
            self.error.emit(str(e))


class PreviewWidget(QWidget):
    """Widget for displaying video preview and metadata."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._thumbnail_loader: Optional[ThumbnailLoader] = None
        self._current_info: Optional[VideoInfo] = None
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Thumbnail
        self.thumbnail_frame = QFrame()
        self.thumbnail_frame.setFixedSize(240, 135)
        self.thumbnail_frame.setStyleSheet("""
            QFrame {
                background-color: #0f3460;
                border-radius: 8px;
            }
        """)
        
        thumb_layout = QVBoxLayout(self.thumbnail_frame)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        
        self.thumbnail_label = QLabel("No Preview")
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("color: #6a6a8a;")
        thumb_layout.addWidget(self.thumbnail_label)
        
        layout.addWidget(self.thumbnail_frame)
        
        # Metadata
        metadata_layout = QVBoxLayout()
        metadata_layout.setSpacing(8)
        
        # Title
        self.title_label = QLabel("No video selected")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(50)
        metadata_layout.addWidget(self.title_label)
        
        # Channel
        channel_row = QHBoxLayout()
        channel_icon = QLabel("👤")
        self.channel_label = QLabel("-")
        self.channel_label.setObjectName("subtitleLabel")
        channel_row.addWidget(channel_icon)
        channel_row.addWidget(self.channel_label)
        channel_row.addStretch()
        metadata_layout.addLayout(channel_row)
        
        # Duration and views row
        info_row = QHBoxLayout()
        
        duration_icon = QLabel("⏱️")
        self.duration_label = QLabel("-")
        info_row.addWidget(duration_icon)
        info_row.addWidget(self.duration_label)
        
        info_row.addSpacing(20)
        
        views_icon = QLabel("👁️")
        self.views_label = QLabel("-")
        info_row.addWidget(views_icon)
        info_row.addWidget(self.views_label)
        
        info_row.addStretch()
        metadata_layout.addLayout(info_row)
        
        # Upload date
        date_row = QHBoxLayout()
        date_icon = QLabel("📅")
        self.date_label = QLabel("-")
        date_row.addWidget(date_icon)
        date_row.addWidget(self.date_label)
        date_row.addStretch()
        metadata_layout.addLayout(date_row)
        
        metadata_layout.addStretch()
        layout.addLayout(metadata_layout, 1)
    
    def set_video_info(self, info: VideoInfo):
        """Update the preview with video information."""
        self._current_info = info
        
        # Update text fields
        self.title_label.setText(info.title)
        self.channel_label.setText(info.channel or "Unknown")
        self.duration_label.setText(format_duration(info.duration))
        
        if info.view_count > 0:
            views = f"{info.view_count:,}" if info.view_count < 1000000 else f"{info.view_count/1000000:.1f}M"
            self.views_label.setText(f"{views} views")
        else:
            self.views_label.setText("-")
        
        if info.upload_date:
            date = f"{info.upload_date[:4]}-{info.upload_date[4:6]}-{info.upload_date[6:]}"
            self.date_label.setText(date)
        else:
            self.date_label.setText("-")
        
        # Load thumbnail
        if info.thumbnail:
            self._load_thumbnail(info.thumbnail)
    
    def _load_thumbnail(self, url: str):
        """Load thumbnail from URL in background."""
        if self._thumbnail_loader and self._thumbnail_loader.isRunning():
            self._thumbnail_loader.terminate()
            self._thumbnail_loader.wait()
        
        self.thumbnail_label.setText("Loading...")
        
        self._thumbnail_loader = ThumbnailLoader(url)
        self._thumbnail_loader.loaded.connect(self._on_thumbnail_loaded)
        self._thumbnail_loader.error.connect(self._on_thumbnail_error)
        self._thumbnail_loader.start()
    
    def _on_thumbnail_loaded(self, pixmap: QPixmap):
        """Handle loaded thumbnail."""
        scaled = pixmap.scaled(
            self.thumbnail_frame.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.thumbnail_label.setPixmap(scaled)
    
    def _on_thumbnail_error(self, error: str):
        """Handle thumbnail loading error."""
        self.thumbnail_label.setText("No Preview")
    
    def clear(self):
        """Clear the preview."""
        self._current_info = None
        self.title_label.setText("No video selected")
        self.channel_label.setText("-")
        self.duration_label.setText("-")
        self.views_label.setText("-")
        self.date_label.setText("-")
        self.thumbnail_label.setText("No Preview")
        self.thumbnail_label.setPixmap(QPixmap())
    
    def get_current_info(self) -> Optional[VideoInfo]:
        """Get the current video info."""
        return self._current_info
