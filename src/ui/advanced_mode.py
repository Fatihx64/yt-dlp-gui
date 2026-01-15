"""
YT-DLP GUI - Advanced Mode Interface
Full-featured download interface with advanced options.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QFileDialog,
    QTabWidget, QCheckBox, QSpinBox, QTextEdit,
    QFormLayout, QFrame, QScrollArea, QMessageBox, QApplication,
    QProgressBar, QSlider
)
from PySide6.QtCore import Qt, Signal

from .preview_widget import PreviewWidget
from ..core.ytdlp_wrapper import YTDLPWrapper, VideoInfo, DownloadProgress
from ..core.queue_manager import get_queue_manager
from ..core.format_extractor import FormatExtractor
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
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
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
        url_layout.addWidget(self.fetch_btn)
        
        layout.addLayout(url_layout)
        
        # Preview
        self.preview = PreviewWidget()
        layout.addWidget(self.preview)
        
        # Options Tabs
        self.options_tabs = QTabWidget()
        
        # Tab 1: Format Options
        self.options_tabs.addTab(self._create_format_tab(), "📹 Format")
        
        # Tab 2: Clip Extraction
        self.options_tabs.addTab(self._create_clip_tab(), "✂️ Clip")
        
        # Tab 3: Subtitles
        self.options_tabs.addTab(self._create_subtitles_tab(), "💬 Subtitles")
        
        # Tab 4: Output
        self.options_tabs.addTab(self._create_output_tab(), "📁 Output")
        
        # Tab 5: Network
        self.options_tabs.addTab(self._create_network_tab(), "🌐 Network")
        
        # Tab 6: Authentication
        self.options_tabs.addTab(self._create_auth_tab(), "🔐 Auth")
        
        layout.addWidget(self.options_tabs)
        
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
        
        # Cancel button
        cancel_row = QHBoxLayout()
        cancel_row.addStretch()
        self.cancel_btn = QPushButton("✖ Cancel Download")
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.setVisible(False)
        cancel_row.addWidget(self.cancel_btn)
        cancel_row.addStretch()
        progress_layout.addLayout(cancel_row)
        
        self.progress_group.setVisible(False)
        layout.addWidget(self.progress_group)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        
        self.normal_btn = QPushButton("◀ Simple Mode")
        action_layout.addWidget(self.normal_btn)
        
        action_layout.addStretch()
        
        self.queue_btn = QPushButton("+ Add to Queue")
        self.queue_btn.setObjectName("secondaryButton")
        self.queue_btn.setEnabled(False)
        action_layout.addWidget(self.queue_btn)
        
        self.download_btn = QPushButton("▶ Download Now")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setEnabled(False)
        action_layout.addWidget(self.download_btn)
        
        layout.addLayout(action_layout)
    
    def _create_format_tab(self) -> QWidget:
        """Create format options tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Video format
        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems([
            "Best Quality",
            "4K (2160p)",
            "1080p (Full HD)",
            "720p (HD)",
            "480p (SD)",
            "360p (Low)",
            "Worst Quality"
        ])
        self.video_format_combo.setCurrentIndex(2)
        layout.addRow("Video Quality:", self.video_format_combo)
        
        # Container format
        self.container_combo = QComboBox()
        self.container_combo.addItems(["mp4", "mkv", "webm", "avi"])
        layout.addRow("Container:", self.container_combo)
        
        # Video codec
        self.vcodec_combo = QComboBox()
        self.vcodec_combo.addItems(["Auto", "h264", "h265/HEVC", "VP9", "AV1"])
        layout.addRow("Video Codec:", self.vcodec_combo)
        
        # Audio format selection
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<b>Audio Options</b>"))
        
        self.audio_only_check = QCheckBox("Download Audio Only")
        layout.addRow("", self.audio_only_check)
        
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["Best", "mp3", "m4a", "opus", "flac", "wav"])
        layout.addRow("Audio Format:", self.audio_format_combo)
        
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["Best", "320k", "256k", "192k", "128k", "96k"])
        layout.addRow("Audio Quality:", self.audio_quality_combo)
        
        return widget
    
    def _create_clip_tab(self) -> QWidget:
        """Create clip extraction tab with sliders."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        self.clip_enabled = QCheckBox("Enable Clip Extraction")
        layout.addWidget(self.clip_enabled)
        
        time_group = QGroupBox("Time Range")
        time_layout = QVBoxLayout(time_group)
        
        # Start time
        start_row = QHBoxLayout()
        start_row.addWidget(QLabel("Start:"))
        self.clip_start_input = QLineEdit()
        self.clip_start_input.setPlaceholderText("00:00:00")
        self.clip_start_input.setFixedWidth(100)
        self.clip_start_input.setEnabled(False)
        start_row.addWidget(self.clip_start_input)
        
        self.clip_start_slider = QSlider(Qt.Horizontal)
        self.clip_start_slider.setMinimum(0)
        self.clip_start_slider.setMaximum(100)
        self.clip_start_slider.setValue(0)
        self.clip_start_slider.setEnabled(False)
        start_row.addWidget(self.clip_start_slider)
        
        self.start_time_label = QLabel("00:00:00")
        self.start_time_label.setFixedWidth(70)
        start_row.addWidget(self.start_time_label)
        time_layout.addLayout(start_row)
        
        # End time
        end_row = QHBoxLayout()
        end_row.addWidget(QLabel("End:  "))
        self.clip_end_input = QLineEdit()
        self.clip_end_input.setPlaceholderText("00:00:00")
        self.clip_end_input.setFixedWidth(100)
        self.clip_end_input.setEnabled(False)
        end_row.addWidget(self.clip_end_input)
        
        self.clip_end_slider = QSlider(Qt.Horizontal)
        self.clip_end_slider.setMinimum(0)
        self.clip_end_slider.setMaximum(100)
        self.clip_end_slider.setValue(100)
        self.clip_end_slider.setEnabled(False)
        end_row.addWidget(self.clip_end_slider)
        
        self.end_time_label = QLabel("00:00:00")
        self.end_time_label.setFixedWidth(70)
        end_row.addWidget(self.end_time_label)
        time_layout.addLayout(end_row)
        
        layout.addWidget(time_group)
        
        # Info label
        info_label = QLabel(
            "💡 Use sliders or enter times in HH:MM:SS format.\n"
            "Leave end time empty to download until the end."
        )
        info_label.setStyleSheet("color: #888888;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # Connect clip controls
        self.clip_enabled.toggled.connect(self._on_clip_toggled)
        self.clip_start_slider.valueChanged.connect(self._on_start_slider_changed)
        self.clip_end_slider.valueChanged.connect(self._on_end_slider_changed)
        
        return widget
    
    def _on_clip_toggled(self, enabled: bool):
        """Enable/disable clip controls."""
        self.clip_start_input.setEnabled(enabled)
        self.clip_end_input.setEnabled(enabled)
        self.clip_start_slider.setEnabled(enabled)
        self.clip_end_slider.setEnabled(enabled)
    
    def _on_start_slider_changed(self, value: int):
        """Update start time from slider."""
        if self._current_info and self._current_info.duration > 0:
            seconds = int(value * self._current_info.duration / 100)
            time_str = format_duration(seconds)
            self.clip_start_input.setText(time_str)
            self.start_time_label.setText(time_str)
    
    def _on_end_slider_changed(self, value: int):
        """Update end time from slider."""
        if self._current_info and self._current_info.duration > 0:
            seconds = int(value * self._current_info.duration / 100)
            time_str = format_duration(seconds)
            self.clip_end_input.setText(time_str)
            self.end_time_label.setText(time_str)
    
    def _create_subtitles_tab(self) -> QWidget:
        """Create subtitles options tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        self.subs_download = QCheckBox("Download Subtitles")
        layout.addWidget(self.subs_download)
        
        self.subs_embed = QCheckBox("Embed Subtitles in Video")
        self.subs_embed.setEnabled(False)
        layout.addWidget(self.subs_embed)
        
        self.subs_auto = QCheckBox("Include Auto-generated Subtitles")
        self.subs_auto.setEnabled(False)
        layout.addWidget(self.subs_auto)
        
        # Languages
        lang_group = QGroupBox("Subtitle Languages")
        lang_layout = QFormLayout(lang_group)
        
        self.subs_lang_input = QLineEdit()
        self.subs_lang_input.setPlaceholderText("en, es, de, fr...")
        self.subs_lang_input.setText("en")
        self.subs_lang_input.setEnabled(False)
        lang_layout.addRow("Languages:", self.subs_lang_input)
        
        self.subs_format_combo = QComboBox()
        self.subs_format_combo.addItems(["srt", "vtt", "ass", "lrc"])
        self.subs_format_combo.setEnabled(False)
        lang_layout.addRow("Format:", self.subs_format_combo)
        
        layout.addWidget(lang_group)
        layout.addStretch()
        
        # Connect checkbox
        self.subs_download.toggled.connect(lambda x: (
            self.subs_embed.setEnabled(x),
            self.subs_auto.setEnabled(x),
            self.subs_lang_input.setEnabled(x),
            self.subs_format_combo.setEnabled(x)
        ))
        
        return widget
    
    def _create_output_tab(self) -> QWidget:
        """Create output options tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Output folder
        folder_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setText(self.config.settings.download.output_path)
        folder_layout.addWidget(self.output_input)
        
        self.browse_btn = QPushButton("Browse")
        folder_layout.addWidget(self.browse_btn)
        layout.addLayout(folder_layout)
        
        # Filename template
        template_group = QGroupBox("Filename Template")
        template_layout = QVBoxLayout(template_group)
        
        self.template_input = QLineEdit()
        self.template_input.setText("%(title)s.%(ext)s")
        template_layout.addWidget(self.template_input)
        
        template_help = QLabel(
            "Available variables: %(title)s, %(id)s, %(ext)s, "
            "%(channel)s, %(upload_date)s, %(resolution)s"
        )
        template_help.setStyleSheet("color: #888888; font-size: 11px;")
        template_help.setWordWrap(True)
        template_layout.addWidget(template_help)
        
        layout.addWidget(template_group)
        
        # Metadata options
        meta_group = QGroupBox("Metadata")
        meta_layout = QVBoxLayout(meta_group)
        
        self.embed_thumbnail = QCheckBox("Embed Thumbnail")
        self.embed_thumbnail.setChecked(self.config.settings.download.embed_thumbnail)
        meta_layout.addWidget(self.embed_thumbnail)
        
        self.embed_metadata = QCheckBox("Embed Metadata (title, artist, etc.)")
        self.embed_metadata.setChecked(self.config.settings.download.embed_metadata)
        meta_layout.addWidget(self.embed_metadata)
        
        self.embed_chapters = QCheckBox("Embed Chapter Markers")
        meta_layout.addWidget(self.embed_chapters)
        
        layout.addWidget(meta_group)
        layout.addStretch()
        
        # Connect browse button
        self.browse_btn.clicked.connect(self._browse_folder)
        
        return widget
    
    def _create_network_tab(self) -> QWidget:
        """Create network options tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Proxy
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://proxy:port or socks5://proxy:port")
        layout.addRow("Proxy:", self.proxy_input)
        
        # Rate limit
        rate_layout = QHBoxLayout()
        self.rate_limit_input = QLineEdit()
        self.rate_limit_input.setPlaceholderText("e.g., 1M for 1MB/s")
        rate_layout.addWidget(self.rate_limit_input)
        layout.addRow("Rate Limit:", rate_layout)
        
        # Retries
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 100)
        self.retries_spin.setValue(10)
        layout.addRow("Retries:", self.retries_spin)
        
        # Concurrent fragments
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 16)
        self.concurrent_spin.setValue(4)
        layout.addRow("Concurrent Fragments:", self.concurrent_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Timeout:", self.timeout_spin)
        
        return widget
    
    def _create_auth_tab(self) -> QWidget:
        """Create authentication options tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Cookies
        cookie_group = QGroupBox("Cookie Authentication")
        cookie_layout = QVBoxLayout(cookie_group)
        
        cookie_file_layout = QHBoxLayout()
        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setPlaceholderText("Path to cookies.txt file")
        cookie_file_layout.addWidget(self.cookie_file_input)
        
        self.cookie_browse_btn = QPushButton("Browse")
        cookie_file_layout.addWidget(self.cookie_browse_btn)
        cookie_layout.addLayout(cookie_file_layout)
        
        cookie_info = QLabel(
            "💡 Export cookies from your browser using a cookie export extension.\n"
            "This allows downloading age-restricted or private videos."
        )
        cookie_info.setStyleSheet("color: #888888; font-size: 11px;")
        cookie_info.setWordWrap(True)
        cookie_layout.addWidget(cookie_info)
        
        layout.addWidget(cookie_group)
        
        # Browser cookies
        browser_group = QGroupBox("Extract from Browser")
        browser_layout = QFormLayout(browser_group)
        
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["None", "Chrome", "Firefox", "Edge", "Opera", "Brave"])
        browser_layout.addRow("Browser:", self.browser_combo)
        
        layout.addWidget(browser_group)
        layout.addStretch()
        
        # Connect browse button
        self.cookie_browse_btn.clicked.connect(self._browse_cookie_file)
        
        return widget
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.paste_btn.clicked.connect(self._paste_url)
        self.fetch_btn.clicked.connect(self._fetch_info)
        self.download_btn.clicked.connect(self._start_download)
        self.queue_btn.clicked.connect(self._add_to_queue)
        self.normal_btn.clicked.connect(self.switch_to_normal.emit)
        self.url_input.returnPressed.connect(self._fetch_info)
        self.cancel_btn.clicked.connect(self._cancel_download)
        
        self.ytdlp.signals.info_ready.connect(self._on_info_ready)
        self.ytdlp.signals.error.connect(self._on_error)
        self.ytdlp.signals.progress.connect(self._on_progress)
        self.ytdlp.signals.finished.connect(self._on_finished)
    
    def _load_settings(self):
        """Load settings into UI."""
        config = self.config.settings
        self.output_input.setText(config.download.output_path)
        self.proxy_input.setText(config.network.proxy)
        self.retries_spin.setValue(config.network.retries)
        self.timeout_spin.setValue(config.network.timeout)
    
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
        self.fetch_btn.setText("Loading...")
        self.preview.clear()
        self._current_info = None
        
        self.ytdlp.extract_info(url)
    
    def _on_info_ready(self, info: VideoInfo):
        """Handle received video info."""
        self._current_info = info
        self.preview.set_video_info(info)
        
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")
        self.download_btn.setEnabled(True)
        self.queue_btn.setEnabled(True)
        
        # Update sliders with video duration
        if info.duration > 0:
            self.clip_end_slider.setValue(100)
            self.end_time_label.setText(format_duration(info.duration))
            self.clip_end_input.setPlaceholderText(format_duration(info.duration))
    
    def _on_error(self, error: str):
        """Handle error."""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")
        QMessageBox.warning(self, "Error", f"Failed to fetch video info:\n{error}")
    
    def _browse_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", self.output_input.text()
        )
        if folder:
            self.output_input.setText(folder)
    
    def _browse_cookie_file(self):
        """Browse for cookie file."""
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Cookie File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file:
            self.cookie_file_input.setText(file)
    
    def _build_options(self) -> dict:
        """Build download options from UI."""
        container = self.container_combo.currentText()
        
        options = {
            'embed_thumbnail': self.embed_thumbnail.isChecked(),
            'embed_metadata': self.embed_metadata.isChecked(),
            'rate_limit': self.rate_limit_input.text() or None,
            'proxy': self.proxy_input.text() or None,
            'cookies_file': self.cookie_file_input.text() or None,
            'merge_output_format': container,  # Force container format
        }
        
        # Clip options
        if self.clip_enabled.isChecked():
            options['clip_start'] = self.clip_start_input.text() or None
            options['clip_end'] = self.clip_end_input.text() or None
        
        # Subtitles
        if self.subs_download.isChecked():
            options['embed_subtitles'] = self.subs_embed.isChecked()
            options['subtitle_langs'] = [
                l.strip() for l in self.subs_lang_input.text().split(',')
            ]
        
        # Browser cookies
        browser = self.browser_combo.currentText()
        if browser != "None":
            options['cookies_from_browser'] = browser.lower()
        
        return options
    
    def _get_format_spec(self) -> str:
        """Build format specification."""
        if self.audio_only_check.isChecked():
            return "bestaudio"
        
        quality_map = {
            0: "best",
            1: "4k",
            2: "1080",
            3: "720",
            4: "480",
            5: "360",
            6: "worst"
        }
        
        quality = quality_map.get(self.video_format_combo.currentIndex(), "best")
        return FormatExtractor.build_format_spec("video_audio", quality)
    
    def _get_format_type(self) -> str:
        """Get current format type."""
        if self.audio_only_check.isChecked():
            audio_fmt = self.audio_format_combo.currentText().lower()
            return f"audio_{audio_fmt}" if audio_fmt != "best" else "audio_best"
        return "video_audio"
    
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
        options = self._build_options()
        options['extra_args'] = extra_args
        output_path = self.output_input.text()
        
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
            QMessageBox.information(self, "Success", "Download completed successfully!")
        else:
            self.status_label.setText("Status: Failed")
            self.logger.error(f"Download failed: {message}")
            QMessageBox.warning(self, "Download Failed", f"Download failed:\n{message}")
    
    def _add_to_queue(self):
        """Add current video to queue."""
        if not self._current_info:
            return
        
        queue = get_queue_manager()
        format_spec = self._get_format_spec()
        options = self._build_options()
        
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
        
        # Clear
        self.url_input.clear()
        self.preview.clear()
        self._current_info = None
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)
    
    def set_url(self, url: str):
        """Set URL externally (for sync from other modes)."""
        if url and url != self.url_input.text():
            self.url_input.setText(url)
            self._fetch_info()
    
    def get_url(self) -> str:
        """Get current URL."""
        return self.url_input.text().strip()
    
    def get_current_info(self) -> Optional[VideoInfo]:
        """Get current video info."""
        return self._current_info
