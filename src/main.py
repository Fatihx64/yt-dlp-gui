#!/usr/bin/env python3
"""
YT-DLP GUI - YouTube Video Downloader
A modern, feature-rich GUI for yt-dlp.

Usage:
    python main.py
    
    or run the compiled executable:
    yt-dlp-gui.exe
"""

import sys
import os

# Add src to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.ui.main_window import MainWindow
from src.utils.logger import get_logger


def main():
    """Application entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("YT-DLP GUI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("YT-DLP GUI")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Initialize logger
    logger = get_logger()
    logger.info("=" * 50)
    logger.info("YT-DLP GUI Starting...")
    logger.info("=" * 50)
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        
        # Run application
        exit_code = app.exec()
        
        logger.info("Application exiting normally")
        return exit_code
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main())
