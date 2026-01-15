"""
YT-DLP GUI - Log Panel
Log viewer with filtering and export capabilities.
"""

from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QCheckBox,
    QFileDialog, QFrame
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat

from ..utils.logger import get_logger, LogSignalEmitter


class LogPanel(QWidget):
    """Panel for displaying application logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self._auto_scroll = True
        self._filter_level = "ALL"
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📝 Log")
        title.setStyleSheet("font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        # Filter
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Info", "Warning", "Error", "Debug"])
        self.filter_combo.setFixedWidth(100)
        header.addWidget(self.filter_combo)
        
        # Auto-scroll
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        header.addWidget(self.auto_scroll_check)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedWidth(60)
        header.addWidget(self.clear_btn)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.setFixedWidth(60)
        header.addWidget(self.export_btn)
        
        layout.addLayout(header)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                background-color: #0a0a1a;
                color: #a0a0c0;
                border: 1px solid #0f3460;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_text)
    
    def _connect_signals(self):
        """Connect signals."""
        # Logger signals
        emitter = self.logger.get_signal_emitter()
        emitter.log_message.connect(self._on_log_message)
        
        # UI signals
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self.auto_scroll_check.toggled.connect(lambda x: setattr(self, '_auto_scroll', x))
        self.clear_btn.clicked.connect(self._clear_log)
        self.export_btn.clicked.connect(self._export_log)
    
    @Slot(str, str, str)
    def _on_log_message(self, level: str, timestamp: str, message: str):
        """Handle incoming log message."""
        # Check filter
        if self._filter_level != "ALL" and self._filter_level != level:
            return
        
        # Format colors
        colors = {
            'DEBUG': '#6a6a8a',
            'INFO': '#4ecdc4',
            'WARNING': '#f9ca24',
            'ERROR': '#ff6b6b',
            'CRITICAL': '#ff0000'
        }
        
        color = colors.get(level, '#a0a0c0')
        
        # Format message
        formatted = f'<span style="color: {color};">[{level}]</span> '
        formatted += f'<span style="color: #6a6a8a;">{timestamp}</span> | '
        formatted += f'<span style="color: #eaeaea;">{message}</span>'
        
        # Append to log
        self.log_text.append(formatted)
        
        # Auto-scroll
        if self._auto_scroll:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)
    
    def _on_filter_changed(self, text: str):
        """Handle filter change."""
        self._filter_level = text.upper() if text != "All" else "ALL"
    
    def _clear_log(self):
        """Clear log display."""
        self.log_text.clear()
    
    def _export_log(self):
        """Export log to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"yt-dlp-gui_log_{timestamp}.txt"
        
        file, _ = QFileDialog.getSaveFileName(
            self, "Export Log", default_name,
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file:
            try:
                text = self.log_text.toPlainText()
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.logger.info(f"Log exported to: {file}")
            except Exception as e:
                self.logger.error(f"Failed to export log: {e}")
    
    def add_message(self, level: str, message: str):
        """Add a log message programmatically."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._on_log_message(level, timestamp, message)
