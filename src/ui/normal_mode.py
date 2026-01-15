"""
YT-DLP GUI - Normal Mode Interface
Simple, user-friendly download interface.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QFileDialog,
    QProgressBar, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal

from .preview_widget import PreviewWidget
from ..core.ytdlp_wrapper import YTDLPWrapper, VideoInfo, DownloadProgress
from ..core.queue_manager import get_queue_manager
from ..core.format_extractor import FormatExtractor
from ..core.config import get_config
from ..utils.logger import get_logger


class NormalMode(QWidget):
    """Normal mode interface for simple video downloading."""
    
    download_started = Signal()
    add_to_queue = Signal(dict)  # video info dict
    switch_to_advanced = Signal(str)  # current URL
    url_changed = Signal(str)  # URL changed signal for sync
    
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
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # URL Input Section
        url_group = QGroupBox("Video URL")
        url_layout = QHBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        self.url_input.setClearButtonEnabled(True)
        url_layout.addWidget(self.url_input)
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.setFixedWidth(80)
        url_layout.addWidget(self.paste_btn)
        
        self.fetch_btn = QPushButton("🔍 Fetch")
        self.fetch_btn.setObjectName("primaryButton")
        self.fetch_btn.setFixedWidth(100)
        url_layout.addWidget(self.fetch_btn)
        
        layout.addWidget(url_group)
        
        # Preview Section
        preview_group = QGroupBox("Video Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview = PreviewWidget()
        preview_layout.addWidget(self.preview)
        
        layout.addWidget(preview_group)
        
        # Download Options Section
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)
        
        # Format and Quality row
        format_row = QHBoxLayout()
        
        format_label = QLabel("Format:")
        format_label.setFixedWidth(80)
        format_row.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Video + Audio",
            "Video Only",
            "Audio (MP3)",
            "Audio (M4A)",
            "Audio (Best)"
        ])
        format_row.addWidget(self.format_combo)
        
        format_row.addSpacing(20)
        
        quality_label = QLabel("Quality:")
        quality_label.setFixedWidth(60)
        format_row.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Best",
            "4K (2160p)",
            "1080p",
            "720p",
            "480p",
            "360p",
            "Worst"
        ])
        self.quality_combo.setCurrentIndex(2)  # Default to 1080p
        format_row.addWidget(self.quality_combo)
        
        options_layout.addLayout(format_row)
        
        # Output folder row
        output_row = QHBoxLayout()
        
        output_label = QLabel("Save to:")
        output_label.setFixedWidth(80)
        output_row.addWidget(output_label)
        
        self.output_input = QLineEdit()
        self.output_input.setText(self.config.settings.download.output_path)
        self.output_input.setReadOnly(True)
        output_row.addWidget(self.output_input)
        
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.setFixedWidth(100)
        output_row.addWidget(self.browse_btn)
        
        options_layout.addLayout(output_row)
        
        layout.addWidget(options_group)
        
        # Progress Section (initially hidden)
        self.progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        progress_info_row = QHBoxLayout()
        self.speed_label = QLabel("Speed: -")
        self.eta_label = QLabel("ETA: -")
        self.status_label = QLabel("Status: Ready")
        progress_info_row.addWidget(self.speed_label)
        progress_info_row.addStretch()
        progress_info_row.addWidget(self.eta_label)
        progress_info_row.addStretch()
        progress_info_row.addWidget(self.status_label)
        progress_layout.addLayout(progress_info_row)
        
        # Cancel button row (shown during download)
        cancel_row = QHBoxLayout()
        cancel_row.addStretch()
        
        self.cancel_btn = QPushButton("✖ Cancel Download")
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setMinimumWidth(150)
        cancel_row.addWidget(self.cancel_btn)
        
        cancel_row.addStretch()
        progress_layout.addLayout(cancel_row)
        
        self.progress_group.setVisible(False)
        layout.addWidget(self.progress_group)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)
        
        self.download_btn = QPushButton("▶ Download")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setEnabled(False)
        self.download_btn.setMinimumHeight(45)
        action_layout.addWidget(self.download_btn)
        
        self.queue_btn = QPushButton("+ Add to Queue")
        self.queue_btn.setObjectName("secondaryButton")
        self.queue_btn.setEnabled(False)
        self.queue_btn.setMinimumHeight(45)
        action_layout.addWidget(self.queue_btn)
        
        self.advanced_btn = QPushButton("⚙ Advanced Mode")
        self.advanced_btn.setMinimumHeight(45)
        action_layout.addWidget(self.advanced_btn)
        
        layout.addLayout(action_layout)
        
        # Spacer
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.paste_btn.clicked.connect(self._paste_url)
        self.fetch_btn.clicked.connect(self._fetch_info)
        self.browse_btn.clicked.connect(self._browse_folder)
        self.download_btn.clicked.connect(self._start_download)
        self.queue_btn.clicked.connect(self._add_to_queue)
        self.advanced_btn.clicked.connect(self._switch_to_advanced)
        self.url_input.returnPressed.connect(self._fetch_info)
        self.cancel_btn.clicked.connect(self._cancel_download)
        
        # URL change tracking
        self.url_input.textChanged.connect(self._on_url_changed)
        
        # Format change updates quality options
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        
        # yt-dlp signals
        self.ytdlp.signals.info_ready.connect(self._on_info_ready)
        self.ytdlp.signals.error.connect(self._on_error)
        self.ytdlp.signals.progress.connect(self._on_progress)
        self.ytdlp.signals.finished.connect(self._on_finished)
    
    def _on_url_changed(self, text: str):
        """Emit URL changed signal for sync with other modes."""
        self.url_changed.emit(text)
    
    def _switch_to_advanced(self):
        """Switch to advanced mode with current URL."""
        current_url = self.url_input.text().strip()
        self.switch_to_advanced.emit(current_url)
    
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
        
        self.logger.info(f"Fetching info for: {url}")
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
        # Disable quality selection for audio-only formats
        is_audio = index >= 2
        self.quality_combo.setEnabled(not is_audio)
        if is_audio:
            self.quality_combo.setCurrentIndex(0)  # Best
    
    def _get_format_type(self) -> str:
        """Get current format type string."""
        format_map = {
            0: "video_audio",
            1: "video_only",
            2: "audio_mp3",
            3: "audio_m4a",
            4: "audio_best"
        }
        return format_map.get(self.format_combo.currentIndex(), "video_audio")
    
    def _get_format_spec(self) -> str:
        """Build format specification from selections."""
        quality_map = {
            0: "best",
            1: "4k",
            2: "1080",
            3: "720",
            4: "480",
            5: "360",
            6: "worst"
        }
        
        format_type = self._get_format_type()
        quality = quality_map.get(self.quality_combo.currentIndex(), "best")
        
        return FormatExtractor.build_format_spec(format_type, quality)
    
    def _start_download(self):
        """Start immediate download."""
        if not self._current_info:
            return
        
        self._is_downloading = True
        self._current_task_id = self._current_info.id
        self.progress_group.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Status: Starting...")
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        
        format_type = self._get_format_type()
        format_spec = self._get_format_spec()
        extra_args = FormatExtractor.get_extra_args(format_type)
        output_path = self.output_input.text()
        
        # Determine container format (audio formats don't need merge)
        is_audio = format_type.startswith("audio_")
        
        options = {
            'embed_thumbnail': self.config.settings.download.embed_thumbnail,
            'embed_metadata': self.config.settings.download.embed_metadata,
            'extra_args': extra_args,
        }
        
        # Force MP4 container for video downloads
        if not is_audio:
            options['merge_output_format'] = 'mp4'
        
        self.logger.info(f"Starting download: {self._current_info.title}")
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
            
            QMessageBox.information(
                self,
                "Success",
                "Download completed successfully!"
            )
        else:
            self.status_label.setText("Status: Failed")
            self.logger.error(f"Download failed: {message}")
            
            QMessageBox.warning(
                self,
                "Download Failed",
                f"Download failed:\n{message}"
            )
    
    def _add_to_queue(self):
        """Add current video to download queue."""
        if not self._current_info:
            return
        
        queue = get_queue_manager()
        format_spec = self._get_format_spec()
        
        queue.add_url(
            url=self._current_info.url,
            title=self._current_info.title,
            thumbnail=self._current_info.thumbnail,
            duration=self._current_info.duration,
            format_spec=format_spec,
            output_path=self.output_input.text()
        )
        
        self.logger.info(f"Added to queue: {self._current_info.title}")
        
        self.add_to_queue.emit({
            'title': self._current_info.title,
            'url': self._current_info.url
        })
        
        # Clear for next video
        self.url_input.clear()
        self.preview.clear()
        self._current_info = None
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
    
    def set_url(self, url: str):
        """Set URL externally (for sync from other modes)."""
        if url != self.url_input.text():
            self.url_input.blockSignals(True)
            self.url_input.setText(url)
            self.url_input.blockSignals(False)
            if url:
                self._fetch_info()
    
    def get_url(self) -> str:
        """Get current URL."""
        return self.url_input.text().strip()
    
    def get_current_info(self) -> Optional[VideoInfo]:
        """Get current video info."""
        return self._current_info
