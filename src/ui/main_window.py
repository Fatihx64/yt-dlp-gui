"""
YT-DLP GUI - Main Window
Primary application window with all UI components.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QSplitter, QMenuBar, QMenu,
    QStatusBar, QLabel, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon

from .styles import get_theme
from .normal_mode import NormalMode
from .advanced_mode import AdvancedMode
from .queue_panel import QueuePanel
from .log_panel import LogPanel
from ..core.config import get_config
from ..core.ytdlp_wrapper import YTDLPWrapper
from ..core.downloader import get_download_manager
from ..utils.logger import get_logger


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.config = get_config()
        self.ytdlp = YTDLPWrapper()
        self.download_manager = get_download_manager()
        
        self._setup_window()
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()
        self._check_dependencies()
        
        self.logger.info("YT-DLP GUI started")
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("YT-DLP GUI - YouTube Video Downloader")
        
        # Set window icon
        self._set_window_icon()
        
        # Apply theme
        theme = get_theme(self.config.settings.ui.theme)
        self.setStyleSheet(theme)
        
        # Restore window geometry
        ui = self.config.settings.ui
        if ui.window_x >= 0 and ui.window_y >= 0:
            self.setGeometry(ui.window_x, ui.window_y, ui.window_width, ui.window_height)
        else:
            self.resize(ui.window_width, ui.window_height)
            self._center_window()
    
    def _set_window_icon(self):
        """Set the application window icon."""
        import sys
        
        # Determine icon path based on whether we're running as EXE or from source
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            base_path = Path(sys.executable).parent
        else:
            # Running from source
            base_path = Path(__file__).parent.parent.parent
        
        icon_path = base_path / 'assets' / 'icon.ico'
        
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            self.logger.debug(f"Window icon set from: {icon_path}")
        else:
            self.logger.warning(f"Icon not found at: {icon_path}")
    
    def _center_window(self):
        """Center window on screen."""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        """Setup main UI components."""
        # Set minimum window size to prevent breaking
        self.setMinimumSize(1000, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main splitter (horizontal: content | queue)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)  # Prevent collapsing
        
        # Left side: Main content with log panel
        left_widget = QWidget()
        left_widget.setMinimumWidth(650)  # Minimum width for content
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Content splitter (vertical: mode | logs)
        self.content_splitter = QSplitter(Qt.Vertical)
        self.content_splitter.setChildrenCollapsible(False)  # Prevent collapsing
        
        # Mode stack (Normal/Advanced)
        self.mode_stack = QStackedWidget()
        self.mode_stack.setMinimumHeight(400)  # Minimum height for mode
        
        self.normal_mode = NormalMode()
        self.mode_stack.addWidget(self.normal_mode)
        
        self.advanced_mode = AdvancedMode()
        self.mode_stack.addWidget(self.advanced_mode)
        
        # Set initial mode
        self.mode_stack.setCurrentIndex(1 if self.config.settings.ui.advanced_mode else 0)
        
        self.content_splitter.addWidget(self.mode_stack)
        
        # Log panel
        self.log_panel = LogPanel()
        self.log_panel.setMinimumHeight(100)
        self.log_panel.setMaximumHeight(250)
        self.content_splitter.addWidget(self.log_panel)
        
        # Set splitter sizes (content area takes more space)
        self.content_splitter.setSizes([550, 150])
        self.content_splitter.setStretchFactor(0, 3)  # Mode takes 3x space
        self.content_splitter.setStretchFactor(1, 1)  # Log takes 1x space
        
        left_layout.addWidget(self.content_splitter)
        
        self.main_splitter.addWidget(left_widget)
        
        # Right side: Queue panel
        self.queue_panel = QueuePanel()
        self.queue_panel.setMinimumWidth(280)
        self.queue_panel.setMaximumWidth(350)
        self.main_splitter.addWidget(self.queue_panel)
        
        # Set main splitter sizes
        self.main_splitter.setSizes([800, 350])
        
        main_layout.addWidget(self.main_splitter)
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        import_action = QAction("Import URLs...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.queue_panel._import_urls)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        self.toggle_mode_action = QAction("Toggle Advanced Mode", self)
        self.toggle_mode_action.setShortcut("Ctrl+T")
        self.toggle_mode_action.triggered.connect(self._toggle_mode)
        view_menu.addAction(self.toggle_mode_action)
        
        self.toggle_log_action = QAction("Toggle Log Panel", self)
        self.toggle_log_action.setShortcut("Ctrl+L")
        self.toggle_log_action.triggered.connect(self._toggle_log_panel)
        view_menu.addAction(self.toggle_log_action)
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        
        dark_action = QAction("Night Mode (Dark)", self)
        dark_action.triggered.connect(lambda: self._set_theme("dark"))
        theme_menu.addAction(dark_action)
        
        light_action = QAction("Day Mode (Light)", self)
        light_action.triggered.connect(lambda: self._set_theme("light"))
        theme_menu.addAction(light_action)
        
        # Queue menu
        queue_menu = menubar.addMenu("&Queue")
        
        start_action = QAction("Start Queue", self)
        start_action.setShortcut("Ctrl+R")
        start_action.triggered.connect(self.queue_panel._start_queue)
        queue_menu.addAction(start_action)
        
        pause_action = QAction("Pause Queue", self)
        pause_action.triggered.connect(self.queue_panel._pause_queue)
        queue_menu.addAction(pause_action)
        
        queue_menu.addSeparator()
        
        clear_action = QAction("Clear Completed", self)
        clear_action.triggered.connect(self.queue_panel._clear_completed)
        queue_menu.addAction(clear_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        check_update_action = QAction("Check for Updates", self)
        check_update_action.triggered.connect(self._check_updates)
        help_menu.addAction(check_update_action)
    
    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = self.statusBar()
        
        # yt-dlp version
        version = self.ytdlp.get_version()
        version_text = f"yt-dlp: {version}" if version else "yt-dlp: Not Found"
        self.version_label = QLabel(version_text)
        self.statusbar.addPermanentWidget(self.version_label)
        
        # Download stats
        self.stats_label = QLabel("Ready")
        self.statusbar.addWidget(self.stats_label)
    
    def _connect_signals(self):
        """Connect component signals."""
        # Mode switching with URL sync
        self.normal_mode.switch_to_advanced.connect(self._switch_to_advanced_with_url)
        self.advanced_mode.switch_to_normal.connect(self._switch_to_normal_with_url)
        
        # Queue additions
        self.normal_mode.add_to_queue.connect(self._on_queue_add)
        self.advanced_mode.add_to_queue.connect(self._on_queue_add)
        
        # Download manager
        self.download_manager.signals.download_started.connect(self._on_download_started)
        self.download_manager.signals.all_finished.connect(self._on_all_finished)
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        # Check yt-dlp
        if not self.ytdlp.check_available():
            QMessageBox.warning(
                self,
                "Dependency Missing",
                "yt-dlp executable not found!\n\n"
                "Please download yt-dlp.exe and place it in the application folder "
                "or add it to your system PATH.\n\n"
                "Download from: https://github.com/yt-dlp/yt-dlp/releases"
            )
        
        # Check FFmpeg
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check FFmpeg and offer to download if missing."""
        from ..utils.ffmpeg_downloader import get_ffmpeg_downloader
        
        downloader = get_ffmpeg_downloader()
        
        if not downloader.is_installed():
            reply = QMessageBox.question(
                self,
                "FFmpeg Not Found",
                "FFmpeg is not installed. FFmpeg is required for:\n"
                "• Merging video and audio streams\n"
                "• Clip extraction (downloading parts of videos)\n"
                "• Audio format conversion\n\n"
                "Would you like to download FFmpeg automatically?\n"
                "(This is a one-time setup, ~70MB download)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self._download_ffmpeg(downloader)
    
    def _download_ffmpeg(self, downloader):
        """Download FFmpeg with progress display."""
        from PySide6.QtWidgets import QProgressDialog
        
        progress = QProgressDialog("Downloading FFmpeg...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Installing FFmpeg")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        def on_progress(percent):
            progress.setValue(percent)
        
        def on_finished(success, message):
            progress.close()
            if success:
                self.stats_label.setText("FFmpeg installed!")
                QMessageBox.information(
                    self,
                    "FFmpeg Installed",
                    "FFmpeg was installed successfully!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Installation Failed",
                    f"Failed to install FFmpeg:\n{message}\n\n"
                    "Please download manually from:\n"
                    "https://ffmpeg.org/download.html"
                )
        
        def on_status(status):
            progress.setLabelText(status)
        
        downloader.signals.progress.connect(on_progress)
        downloader.signals.finished.connect(on_finished)
        downloader.signals.status.connect(on_status)
        
        downloader.download()
        progress.show()
    
    def _toggle_mode(self):
        """Toggle between Normal and Advanced mode."""
        current = self.mode_stack.currentIndex()
        if current == 0:
            # Going from Normal to Advanced
            url = self.normal_mode.get_url()
            self._switch_to_advanced_with_url(url)
        else:
            # Going from Advanced to Normal
            self._switch_to_normal_with_url()
    
    def _switch_to_advanced_with_url(self, url: str):
        """Switch to Advanced mode and sync URL."""
        self.mode_stack.setCurrentIndex(1)
        if url:
            self.advanced_mode.set_url(url)
        self.config.settings.ui.advanced_mode = True
        self.config.save()
        self.logger.info("Switched to Advanced mode")
    
    def _switch_to_normal_with_url(self):
        """Switch to Normal mode and sync URL."""
        url = self.advanced_mode.get_url()
        self.mode_stack.setCurrentIndex(0)
        if url:
            self.normal_mode.set_url(url)
        self.config.settings.ui.advanced_mode = False
        self.config.save()
        self.logger.info("Switched to Normal mode")
    
    def _toggle_log_panel(self):
        """Toggle log panel visibility."""
        is_visible = self.log_panel.isVisible()
        self.log_panel.setVisible(not is_visible)
        self.config.settings.ui.show_log_panel = not is_visible
        self.config.save()
    
    def _set_theme(self, theme_name: str):
        """Set application theme."""
        self.setStyleSheet(get_theme(theme_name))
        self.config.settings.ui.theme = theme_name
        self.config.save()
        mode = "Night Mode" if theme_name == "dark" else "Day Mode"
        self.logger.info(f"Theme changed to {mode}")
    
    def _on_queue_add(self, info: dict):
        """Handle item added to queue."""
        self.stats_label.setText(f"Added: {info.get('title', 'item')[:40]}")
        QTimer.singleShot(3000, lambda: self.stats_label.setText("Ready"))
    
    def _on_download_started(self, item_id: str):
        """Handle download started."""
        self.stats_label.setText("Downloading...")
    
    def _on_all_finished(self):
        """Handle all downloads finished."""
        self.stats_label.setText("All downloads complete!")
    
    def _show_about(self):
        """Show about dialog."""
        version = self.ytdlp.get_version() or "Unknown"
        
        QMessageBox.about(
            self,
            "About YT-DLP GUI",
            f"<h2>YT-DLP GUI</h2>"
            f"<p>A modern YouTube video downloader</p>"
            f"<p>Version: 1.0.0</p>"
            f"<p>yt-dlp version: {version}</p>"
            f"<hr>"
            f"<p>Built with PySide6 and yt-dlp</p>"
            f"<p><a href='https://github.com/yt-dlp/yt-dlp'>yt-dlp on GitHub</a></p>"
        )
    
    def _check_updates(self):
        """Check for yt-dlp updates."""
        QMessageBox.information(
            self,
            "Check Updates",
            "To update yt-dlp, run:\n\nyt-dlp -U\n\nin your command prompt."
        )
    
    def closeEvent(self, event):
        """Handle window close."""
        # Save window geometry
        geo = self.geometry()
        self.config.settings.ui.window_x = geo.x()
        self.config.settings.ui.window_y = geo.y()
        self.config.settings.ui.window_width = geo.width()
        self.config.settings.ui.window_height = geo.height()
        
        # Save log panel height
        sizes = self.content_splitter.sizes()
        if len(sizes) > 1:
            self.config.settings.ui.log_panel_height = sizes[1]
        
        self.config.save()
        
        self.logger.info("Application closed")
        event.accept()
