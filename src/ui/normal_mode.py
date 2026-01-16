"""
YT-DLP GUI - Normal Mode Interface
Simplified download interface for quick video downloads.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QFileDialog,
    QProgressBar, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal

from .preview_widget import PreviewWidget
from ..core.ytdlp_wrapper import YTDLPWrapper, VideoInfo, DownloadProgress
from ..core.queue_manager import get_queue_manager
from ..core.config import get_config
from ..utils.logger import get_logger


class NormalMode(QWidget):
    """Normal mode interface for simple downloads."""
    
    download_started = Signal()
    add_to_queue = Signal(dict)
    switch_to_advanced = Signal(str)  # Emit URL when switching
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.config = get_config()
        self.ytdlp = YTDLPWrapper()
        self._current_info: Optional[VideoInfo] = None
        self._is_downloading = False
        self._current_task_id: Optional[str] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # URL Input Section
        url_group = QGroupBox("Video URL")
        url_layout = QHBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video URL here...")
        url_layout.addWidget(self.url_input)
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.setFixedWidth(80)
        url_layout.addWidget(self.paste_btn)
        
        self.fetch_btn = QPushButton("🔍 Fetch")
        self.fetch_btn.setObjectName("primaryButton")
        self.fetch_btn.setFixedWidth(100)
        url_layout.addWidget(self.fetch_btn)
        
        layout.addWidget(url_group)
        
        # Video Preview Section
        preview_group = QGroupBox("Video Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview = PreviewWidget()
        preview_layout.addWidget(self.preview)
        
        layout.addWidget(preview_group)
        
        # Download Options Section
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)
        
        # Format row
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Video + Audio (MP4)",
            "Video Only",
            "Audio Only (MP3)",
            "Audio Only (M4A)"
        ])
        self.format_combo.setMinimumWidth(180)
        format_row.addWidget(self.format_combo)
        
        format_row.addSpacing(20)
        format_row.addWidget(QLabel("Quality:"))
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Best Available",
            "1080p (Full HD)",
            "720p (HD)",
            "480p (SD)",
            "360p (Low)"
        ])
        self.quality_combo.setMinimumWidth(150)
        format_row.addWidget(self.quality_combo)
        
        format_row.addStretch()
        options_layout.addLayout(format_row)
        
        # Output folder row
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Save to:"))
        
        self.output_input = QLineEdit()
        self.output_input.setText(self.config.settings.download.output_path)
        folder_row.addWidget(self.output_input)
        
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.setFixedWidth(100)
        folder_row.addWidget(self.browse_btn)
        
        options_layout.addLayout(folder_row)
        layout.addWidget(options_group)
        
        # Progress Section
        self.progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)
        
        # Progress info
        info_row = QHBoxLayout()
        self.speed_label = QLabel("Speed: -")
        self.eta_label = QLabel("ETA: -")
        self.status_label = QLabel("Status: Ready")
        info_row.addWidget(self.speed_label)
        info_row.addStretch()
        info_row.addWidget(self.eta_label)
        info_row.addStretch()
        info_row.addWidget(self.status_label)
        progress_layout.addLayout(info_row)
        
        # Cancel button
        self.cancel_btn = QPushButton("✖ Cancel Download")
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.setVisible(False)
        progress_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        
        self.progress_group.setVisible(False)
        layout.addWidget(self.progress_group)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("▶ Download")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setEnabled(False)
        self.download_btn.setMinimumWidth(130)
        action_layout.addWidget(self.download_btn)
        
        self.queue_btn = QPushButton("+ Add to Queue")
        self.queue_btn.setObjectName("secondaryButton")
        self.queue_btn.setEnabled(False)
        self.queue_btn.setMinimumWidth(130)
        action_layout.addWidget(self.queue_btn)
        
        self.clear_btn = QPushButton("🗑 Clear")
        self.clear_btn.setMinimumWidth(100)
        action_layout.addWidget(self.clear_btn)
        
        self.advanced_btn = QPushButton("⚙ Advanced")
        self.advanced_btn.setMinimumWidth(120)
        action_layout.addWidget(self.advanced_btn)
        
        layout.addLayout(action_layout)
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.paste_btn.clicked.connect(self._paste_url)
        self.fetch_btn.clicked.connect(self._fetch_info)
        self.browse_btn.clicked.connect(self._browse_folder)
        self.download_btn.clicked.connect(self._start_download)
        self.queue_btn.clicked.connect(self._add_to_queue)
        self.clear_btn.clicked.connect(self._clear_all)
        self.advanced_btn.clicked.connect(lambda: self.switch_to_advanced.emit(self.url_input.text()))
        self.url_input.returnPressed.connect(self._fetch_info)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        self.cancel_btn.clicked.connect(self._cancel_download)
        
        # YT-DLP signals
        self.ytdlp.signals.info_ready.connect(self._on_info_ready)
        self.ytdlp.signals.error.connect(self._on_error)
        self.ytdlp.signals.progress.connect(self._on_progress)
        self.ytdlp.signals.finished.connect(self._on_finished)
    
    def _clear_all(self):
        """Clear all fields and reset UI."""
        self.url_input.clear()
        self.preview.clear()
        self._current_info = None
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
        self.progress_group.setVisible(False)
        self.progress_bar.setValue(0)
        self.speed_label.setText("Speed: -")
        self.eta_label.setText("ETA: -")
        self.status_label.setText("Status: Ready")
        self.format_combo.setCurrentIndex(0)
        self.quality_combo.setCurrentIndex(0)
        self.quality_combo.setEnabled(True)
        self.logger.info("UI cleared")
    
    def _paste_url(self):
        """Paste URL from clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.url_input.setText(text.strip())
            self._fetch_info()
    
    def _fetch_info(self):
        """Fetch video information."""
        url = self.url_input.text().strip()
        if not url:
            return
        
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("⏳ Loading...")
        self.preview.clear()
        self._current_info = None
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
        
        self.ytdlp.extract_info(url)
    
    def _on_info_ready(self, info: VideoInfo):
        """Handle received video info."""
        self._current_info = info
        self.preview.set_video_info(info)
        
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch")
        self.download_btn.setEnabled(True)
        self.queue_btn.setEnabled(True)
        
        self.logger.info(f"Video info loaded: {info.title}")
    
    def _on_error(self, error: str):
        """Handle error."""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch")
        
        QMessageBox.warning(self, "Error", f"Failed to fetch video info:\n{error}")
        self.logger.error(f"Fetch error: {error}")
    
    def _browse_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self.output_input.text()
        )
        if folder:
            self.output_input.setText(folder)
            self.config.settings.download.output_path = folder
            self.config.settings.add_recent_folder(folder)
            self.config.save()
    
    def _on_format_changed(self, index: int):
        """Handle format selection change."""
        # Disable quality for audio-only formats
        is_audio = index >= 2
        self.quality_combo.setEnabled(not is_audio)
    
    def _build_format_spec(self) -> str:
        """Build yt-dlp format specification."""
        format_idx = self.format_combo.currentIndex()
        quality_idx = self.quality_combo.currentIndex()
        
        # Quality mapping
        quality_heights = {
            0: None,     # Best
            1: 1080,
            2: 720,
            3: 480,
            4: 360
        }
        
        height = quality_heights.get(quality_idx)
        
        if format_idx == 0:  # Video + Audio
            # Always download separate video+audio and merge
            # Don't use /best fallback as it's often video-only
            if height:
                return f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio"
            return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio"
        elif format_idx == 1:  # Video Only
            if height:
                return f"bestvideo[height<={height}]"
            return "bestvideo"
        elif format_idx == 2:  # Audio MP3
            return "bestaudio"
        elif format_idx == 3:  # Audio M4A
            return "bestaudio[ext=m4a]/bestaudio"
        
        return "bestvideo+bestaudio"
    
    def _get_extra_args(self) -> list:
        """Get extra yt-dlp arguments based on format."""
        format_idx = self.format_combo.currentIndex()
        
        if format_idx == 2:  # Audio MP3
            return ["--extract-audio", "--audio-format", "mp3"]
        elif format_idx == 3:  # Audio M4A
            return ["--extract-audio", "--audio-format", "m4a"]
        
        return []
    
    def _start_download(self):
        """Start immediate download."""
        if not self._current_info:
            return
        
        if self._is_downloading:
            QMessageBox.warning(self, "Download in Progress", "Please wait for the current download to finish.")
            return
        
        self._is_downloading = True
        self._current_task_id = self._current_info.id
        self.progress_group.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Status: Starting...")
        self.speed_label.setText("Speed: -")
        self.eta_label.setText("ETA: -")
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        
        format_spec = self._build_format_spec()
        extra_args = self._get_extra_args()
        output_path = self.output_input.text()
        
        # Determine if video (needs merge format)
        format_idx = self.format_combo.currentIndex()
        is_video = format_idx <= 1
        
        options = {
            'extra_args': extra_args,
        }
        
        # Force MP4 container for video
        if is_video:
            options['merge_output_format'] = 'mp4'
        
        self.logger.info(f"Starting download: {self._current_info.title}")
        self.logger.debug(f"Format spec: {format_spec}")
        
        self.ytdlp.download(
            url=self._current_info.url,
            output_path=output_path,
            format_spec=format_spec,
            options=options,
            task_id=self._current_info.id
        )
        
        self.download_started.emit()
    
    def _cancel_download(self):
        """Cancel the current download."""
        if self._current_task_id and self._is_downloading:
            self.ytdlp.cancel(self._current_task_id)
            self.logger.info("Download cancelled by user")
            self.status_label.setText("Status: Cancelled")
            self._reset_after_download()
    
    def _reset_after_download(self):
        """Reset UI after download completes or cancels."""
        self._is_downloading = False
        self._current_task_id = None
        self.download_btn.setEnabled(True)
        self.queue_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
    
    def _on_progress(self, progress: DownloadProgress):
        """Update download progress."""
        if not self._is_downloading:
            return
        self.progress_bar.setValue(int(progress.percent))
        self.speed_label.setText(f"Speed: {progress.speed}")
        self.eta_label.setText(f"ETA: {progress.eta}")
        self.status_label.setText(f"Status: {progress.status.title()}")
    
    def _on_finished(self, success: bool, message: str):
        """Handle download completion."""
        if not self._is_downloading:
            return
        
        self._reset_after_download()
        
        if success:
            self.status_label.setText("Status: Complete!")
            self.progress_bar.setValue(100)
            self.logger.info(f"Download completed: {message}")
            QMessageBox.information(self, "Success", "Download completed successfully!")
        else:
            self.status_label.setText("Status: Failed")
            self.logger.error(f"Download failed: {message}")
            QMessageBox.warning(self, "Download Failed", f"Download failed:\n{message}")
    
    def _add_to_queue(self):
        """Add current video to download queue."""
        if not self._current_info:
            return
        
        queue = get_queue_manager()
        format_spec = self._build_format_spec()
        
        format_idx = self.format_combo.currentIndex()
        is_video = format_idx <= 1
        
        options = {
            'extra_args': self._get_extra_args(),
        }
        
        if is_video:
            options['merge_output_format'] = 'mp4'
        
        queue.add_url(
            url=self._current_info.url,
            title=self._current_info.title,
            thumbnail=self._current_info.thumbnail,
            duration=self._current_info.duration,
            format_spec=format_spec,
            output_path=self.output_input.text(),
            options=options
        )
        
        self.add_to_queue.emit({'title': self._current_info.title})
        self.logger.info(f"Added to queue: {self._current_info.title}")
        
        QMessageBox.information(self, "Added to Queue", f"'{self._current_info.title}' added to download queue.")
    
    def set_url(self, url: str):
        """Set URL externally (for sync from other modes)."""
        if url and url != self.url_input.text():
            self.url_input.setText(url)
    
    def get_url(self) -> str:
        """Get current URL."""
        return self.url_input.text().strip()
