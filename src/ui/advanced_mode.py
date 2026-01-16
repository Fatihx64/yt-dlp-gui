"""
YT-DLP GUI - Advanced Mode Interface
Full-featured download interface with advanced options.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QFileDialog,
    QTabWidget, QCheckBox, QSpinBox,
    QFormLayout, QMessageBox, QApplication,
    QProgressBar, QSlider
)
from PySide6.QtCore import Qt, Signal

from .preview_widget import PreviewWidget
from ..core.ytdlp_wrapper import YTDLPWrapper, VideoInfo, DownloadProgress
from ..core.queue_manager import get_queue_manager
from ..core.config import get_config
from ..utils.logger import get_logger
from ..utils.helpers import format_duration


class AdvancedMode(QWidget):
    """Advanced mode interface with full feature access."""
    
    download_started = Signal()
    add_to_queue = Signal(dict)
    switch_to_normal = Signal()
    
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
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # URL Section
        url_layout = QHBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL...")
        url_layout.addWidget(self.url_input)
        
        self.paste_btn = QPushButton("📋")
        self.paste_btn.setFixedWidth(40)
        self.paste_btn.setToolTip("Paste from clipboard")
        url_layout.addWidget(self.paste_btn)
        
        self.fetch_btn = QPushButton("Fetch Info")
        self.fetch_btn.setObjectName("primaryButton")
        self.fetch_btn.setFixedWidth(100)
        url_layout.addWidget(self.fetch_btn)
        
        layout.addLayout(url_layout)
        
        # Preview
        self.preview = PreviewWidget()
        self.preview.setMaximumHeight(150)
        layout.addWidget(self.preview)
        
        # Options Tabs
        self.options_tabs = QTabWidget()
        self.options_tabs.setMaximumHeight(280)
        
        self.options_tabs.addTab(self._create_format_tab(), "📹 Format")
        self.options_tabs.addTab(self._create_clip_tab(), "✂️ Clip")
        self.options_tabs.addTab(self._create_output_tab(), "📁 Output")
        self.options_tabs.addTab(self._create_network_tab(), "🌐 Network")
        
        layout.addWidget(self.options_tabs)
        
        # Progress Section
        self.progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)
        
        progress_info = QHBoxLayout()
        self.speed_label = QLabel("Speed: -")
        self.eta_label = QLabel("ETA: -")
        self.status_label = QLabel("Status: Ready")
        progress_info.addWidget(self.speed_label)
        progress_info.addStretch()
        progress_info.addWidget(self.eta_label)
        progress_info.addStretch()
        progress_info.addWidget(self.status_label)
        progress_layout.addLayout(progress_info)
        
        self.cancel_btn = QPushButton("✖ Cancel")
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setFixedWidth(120)
        progress_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        
        self.progress_group.setVisible(False)
        layout.addWidget(self.progress_group)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        
        self.normal_btn = QPushButton("◀ Simple Mode")
        self.normal_btn.setFixedWidth(130)
        action_layout.addWidget(self.normal_btn)
        
        self.clear_btn = QPushButton("🗑 Clear")
        self.clear_btn.setFixedWidth(100)
        action_layout.addWidget(self.clear_btn)
        
        action_layout.addStretch()
        
        self.queue_btn = QPushButton("+ Add to Queue")
        self.queue_btn.setObjectName("secondaryButton")
        self.queue_btn.setEnabled(False)
        self.queue_btn.setFixedWidth(140)
        action_layout.addWidget(self.queue_btn)
        
        self.download_btn = QPushButton("▶ Download Now")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setEnabled(False)
        self.download_btn.setFixedWidth(150)
        action_layout.addWidget(self.download_btn)
        
        layout.addLayout(action_layout)
    
    def _create_format_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        
        # Video Quality
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Best Available",
            "4K (2160p)",
            "1080p (Full HD)",
            "720p (HD)",
            "480p (SD)",
            "360p (Low)",
            "Worst Quality"
        ])
        self.quality_combo.setCurrentIndex(2)  # 1080p default
        layout.addRow("Video Quality:", self.quality_combo)
        
        # Container
        self.container_combo = QComboBox()
        self.container_combo.addItems(["mp4", "mkv", "webm"])
        layout.addRow("Container:", self.container_combo)
        
        # Audio Only
        self.audio_only = QCheckBox("Download Audio Only")
        layout.addRow("", self.audio_only)
        
        # Audio Format
        self.audio_format = QComboBox()
        self.audio_format.addItems(["mp3", "m4a", "opus", "best"])
        self.audio_format.setEnabled(False)
        layout.addRow("Audio Format:", self.audio_format)
        
        # Connect audio only checkbox
        self.audio_only.toggled.connect(lambda x: (
            self.audio_format.setEnabled(x),
            self.quality_combo.setEnabled(not x),
            self.container_combo.setEnabled(not x)
        ))
        
        return widget
    
    def _create_clip_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        self.clip_enabled = QCheckBox("Enable Clip Extraction")
        layout.addWidget(self.clip_enabled)
        
        # Time range group
        time_group = QGroupBox("Time Range")
        time_layout = QVBoxLayout(time_group)
        
        # Start time row
        start_row = QHBoxLayout()
        start_row.addWidget(QLabel("Start:"))
        self.clip_start = QLineEdit()
        self.clip_start.setPlaceholderText("00:00:00")
        self.clip_start.setEnabled(False)
        self.clip_start.setFixedWidth(80)
        start_row.addWidget(self.clip_start)
        
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(100)
        self.start_slider.setValue(0)
        self.start_slider.setEnabled(False)
        start_row.addWidget(self.start_slider)
        
        self.start_label = QLabel("00:00")
        self.start_label.setFixedWidth(50)
        start_row.addWidget(self.start_label)
        time_layout.addLayout(start_row)
        
        # End time row
        end_row = QHBoxLayout()
        end_row.addWidget(QLabel("End:  "))
        self.clip_end = QLineEdit()
        self.clip_end.setPlaceholderText("00:00:00")
        self.clip_end.setEnabled(False)
        self.clip_end.setFixedWidth(80)
        end_row.addWidget(self.clip_end)
        
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(100)
        self.end_slider.setValue(100)
        self.end_slider.setEnabled(False)
        end_row.addWidget(self.end_slider)
        
        self.end_label = QLabel("00:00")
        self.end_label.setFixedWidth(50)
        end_row.addWidget(self.end_label)
        time_layout.addLayout(end_row)
        
        layout.addWidget(time_group)
        
        info = QLabel("💡 Use sliders or enter times in HH:MM:SS format.\nFFmpeg required for clip extraction.")
        info.setStyleSheet("color: #888;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        # Connect signals
        self.clip_enabled.toggled.connect(self._on_clip_toggled)
        self.start_slider.valueChanged.connect(self._on_start_slider)
        self.end_slider.valueChanged.connect(self._on_end_slider)
        
        return widget
    
    def _on_clip_toggled(self, enabled):
        self.clip_start.setEnabled(enabled)
        self.clip_end.setEnabled(enabled)
        self.start_slider.setEnabled(enabled)
        self.end_slider.setEnabled(enabled)
    
    def _on_start_slider(self, value):
        if self._current_info and self._current_info.duration > 0:
            seconds = int(value * self._current_info.duration / 100)
            self.clip_start.setText(self._format_time(seconds))
            self.start_label.setText(self._format_time(seconds))
    
    def _on_end_slider(self, value):
        if self._current_info and self._current_info.duration > 0:
            seconds = int(value * self._current_info.duration / 100)
            self.clip_end.setText(self._format_time(seconds))
            self.end_label.setText(self._format_time(seconds))
    
    def _format_time(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    
    def _create_output_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # Output folder
        folder_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setText(self.config.settings.download.output_path)
        folder_layout.addWidget(self.output_input)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedWidth(80)
        folder_layout.addWidget(self.browse_btn)
        layout.addLayout(folder_layout)
        
        # Metadata options
        self.embed_thumb = QCheckBox("Embed Thumbnail")
        layout.addWidget(self.embed_thumb)
        
        self.embed_meta = QCheckBox("Embed Metadata")
        layout.addWidget(self.embed_meta)
        
        layout.addStretch()
        
        self.browse_btn.clicked.connect(self._browse_folder)
        
        return widget
    
    def _create_network_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://proxy:port")
        layout.addRow("Proxy:", self.proxy_input)
        
        self.rate_limit = QLineEdit()
        self.rate_limit.setPlaceholderText("e.g., 1M")
        layout.addRow("Rate Limit:", self.rate_limit)
        
        self.retries = QSpinBox()
        self.retries.setRange(0, 50)
        self.retries.setValue(10)
        layout.addRow("Retries:", self.retries)
        
        return widget
    
    def _connect_signals(self):
        self.paste_btn.clicked.connect(self._paste_url)
        self.fetch_btn.clicked.connect(self._fetch_info)
        self.download_btn.clicked.connect(self._start_download)
        self.queue_btn.clicked.connect(self._add_to_queue)
        self.normal_btn.clicked.connect(self.switch_to_normal.emit)
        self.url_input.returnPressed.connect(self._fetch_info)
        self.cancel_btn.clicked.connect(self._cancel_download)
        self.clear_btn.clicked.connect(self._clear_all)
        
        self.ytdlp.signals.info_ready.connect(self._on_info_ready)
        self.ytdlp.signals.error.connect(self._on_error)
        self.ytdlp.signals.progress.connect(self._on_progress)
        self.ytdlp.signals.finished.connect(self._on_finished)
    
    def _clear_all(self):
        """Clear all fields and reset UI to default state."""
        # Reset URL and preview
        self.url_input.clear()
        self.preview.clear()
        self._current_info = None
        
        # Reset Format tab
        self.quality_combo.setCurrentIndex(2)  # 1080p default
        self.container_combo.setCurrentIndex(0)  # mp4
        self.audio_only.setChecked(False)
        self.audio_format.setCurrentIndex(0)
        self.audio_format.setEnabled(False)
        self.quality_combo.setEnabled(True)
        self.container_combo.setEnabled(True)
        
        # Reset Clip tab
        self.clip_enabled.setChecked(False)
        self.clip_start.clear()
        self.clip_start.setEnabled(False)
        self.clip_end.clear()
        self.clip_end.setEnabled(False)
        self.start_slider.setValue(0)
        self.start_slider.setEnabled(False)
        self.end_slider.setValue(100)
        self.end_slider.setEnabled(False)
        self.start_label.setText("00:00")
        self.end_label.setText("00:00")
        
        # Reset Output tab
        self.embed_thumb.setChecked(False)
        self.embed_meta.setChecked(False)
        
        # Reset Network tab
        self.proxy_input.clear()
        self.rate_limit.clear()
        self.retries.setValue(10)
        
        # Reset progress and buttons
        self.progress_group.setVisible(False)
        self.progress_bar.setValue(0)
        self.speed_label.setText("Speed: -")
        self.eta_label.setText("ETA: -")
        self.status_label.setText("Status: Ready")
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        
        self.logger.info("UI cleared")
    
    def _paste_url(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.url_input.setText(text.strip())
            self._fetch_info()
    
    def _fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            return
        
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Loading...")
        self.preview.clear()
        self._current_info = None
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
        
        self.ytdlp.extract_info(url)
    
    def _on_info_ready(self, info: VideoInfo):
        self._current_info = info
        self.preview.set_video_info(info)
        
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")
        self.download_btn.setEnabled(True)
        self.queue_btn.setEnabled(True)
    
    def _on_error(self, error: str):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")
        QMessageBox.warning(self, "Error", f"Failed to fetch video info:\n{error}")
    
    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", self.output_input.text()
        )
        if folder:
            self.output_input.setText(folder)
    
    def _build_format_spec(self) -> str:
        if self.audio_only.isChecked():
            return "bestaudio"
        
        quality_idx = self.quality_combo.currentIndex()
        heights = {0: None, 1: 2160, 2: 1080, 3: 720, 4: 480, 5: 360, 6: None}
        height = heights.get(quality_idx)
        
        if quality_idx == 6:  # Worst
            return "worstvideo+worstaudio"
        
        # Always use bestvideo+bestaudio, never fallback to /best (single stream)
        if height:
            return f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio"
        
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio"
    
    def _build_options(self) -> dict:
        container = self.container_combo.currentText()
        
        options = {}
        
        if self.audio_only.isChecked():
            audio_fmt = self.audio_format.currentText()
            if audio_fmt == "best":
                options['extra_args'] = ["--extract-audio"]
            else:
                options['extra_args'] = ["--extract-audio", "--audio-format", audio_fmt]
        else:
            options['merge_output_format'] = container
        
        if self.embed_thumb.isChecked():
            options['embed_thumbnail'] = True
        
        if self.embed_meta.isChecked():
            options['embed_metadata'] = True
        
        if self.clip_enabled.isChecked():
            if self.clip_start.text():
                options['clip_start'] = self.clip_start.text()
            if self.clip_end.text():
                options['clip_end'] = self.clip_end.text()
        
        if self.proxy_input.text():
            options['proxy'] = self.proxy_input.text()
        
        if self.rate_limit.text():
            options['rate_limit'] = self.rate_limit.text()
        
        return options
    
    def _start_download(self):
        if not self._current_info:
            return
        
        if self._is_downloading:
            QMessageBox.warning(self, "Busy", "Download already in progress.")
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
        options = self._build_options()
        
        self.logger.info(f"Starting download: {self._current_info.title}")
        self.logger.debug(f"Format: {format_spec}, Options: {options}")
        
        self.ytdlp.download(
            url=self._current_info.url,
            output_path=self.output_input.text(),
            format_spec=format_spec,
            options=options,
            task_id=self._current_info.id
        )
        
        self.download_started.emit()
    
    def _cancel_download(self):
        if self._current_task_id and self._is_downloading:
            self.ytdlp.cancel(self._current_task_id)
            self.status_label.setText("Status: Cancelled")
            self._reset_ui()
    
    def _reset_ui(self):
        self._is_downloading = False
        self._current_task_id = None
        self.download_btn.setEnabled(True)
        self.queue_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
    
    def _on_progress(self, progress: DownloadProgress):
        if not self._is_downloading:
            return
        self.progress_bar.setValue(int(progress.percent))
        self.speed_label.setText(f"Speed: {progress.speed}")
        self.eta_label.setText(f"ETA: {progress.eta}")
        self.status_label.setText(f"Status: {progress.status.title()}")
    
    def _on_finished(self, success: bool, message: str):
        if not self._is_downloading:
            return
        
        self._reset_ui()
        
        if success:
            self.status_label.setText("Status: Complete!")
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", "Download completed!")
        else:
            self.status_label.setText("Status: Failed")
            QMessageBox.warning(self, "Failed", f"Download failed:\n{message}")
    
    def _add_to_queue(self):
        if not self._current_info:
            return
        
        queue = get_queue_manager()
        
        queue.add_url(
            url=self._current_info.url,
            title=self._current_info.title,
            thumbnail=self._current_info.thumbnail,
            duration=self._current_info.duration,
            format_spec=self._build_format_spec(),
            output_path=self.output_input.text(),
            options=self._build_options()
        )
        
        self.add_to_queue.emit({'title': self._current_info.title})
        QMessageBox.information(self, "Added", f"Added to queue: {self._current_info.title}")
    
    def set_url(self, url: str):
        if url and url != self.url_input.text():
            self.url_input.setText(url)
    
    def get_url(self) -> str:
        return self.url_input.text().strip()
    
    def get_current_info(self) -> Optional[VideoInfo]:
        return self._current_info
