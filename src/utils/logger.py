"""
YT-DLP GUI - Logger Module
Custom logging system with GUI signal emission and file rotation.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal


class LogSignalEmitter(QObject):
    """Qt signal emitter for log messages."""
    log_message = Signal(str, str, str)  # level, timestamp, message


class GUILogHandler(logging.Handler):
    """Custom log handler that emits signals to the GUI."""
    
    def __init__(self, signal_emitter: LogSignalEmitter):
        super().__init__()
        self.signal_emitter = signal_emitter
        self.setFormatter(logging.Formatter('%(message)s'))
    
    def emit(self, record):
        try:
            msg = self.format(record)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.signal_emitter.log_message.emit(
                record.levelname,
                timestamp,
                msg
            )
        except Exception:
            self.handleError(record)


class Logger:
    """Application logger with file and GUI output."""
    
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
        self.signal_emitter = LogSignalEmitter()
        self.logger = logging.getLogger('yt-dlp-gui')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '[%(levelname)s] %(asctime)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # GUI handler
        gui_handler = GUILogHandler(self.signal_emitter)
        gui_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(gui_handler)
        
        # File handler
        self._setup_file_handler()
    
    def _setup_file_handler(self):
        """Setup rotating file handler."""
        log_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'yt-dlp-gui_{datetime.now().strftime("%Y%m%d")}.log'
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '[%(levelname)s] %(asctime)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)
    
    def get_signal_emitter(self) -> LogSignalEmitter:
        """Get the signal emitter for GUI connection."""
        return self.signal_emitter


# Global logger instance
def get_logger() -> Logger:
    """Get the singleton logger instance."""
    return Logger()
