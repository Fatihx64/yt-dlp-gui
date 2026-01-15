"""
YT-DLP GUI - Queue Panel
Download queue display and management panel.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMenu,
    QFrame, QProgressBar, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ..core.queue_manager import (
    QueueManager, QueueItem, QueueItemStatus, get_queue_manager
)
from ..core.downloader import get_download_manager
from ..utils.helpers import format_duration, open_folder
from ..utils.logger import get_logger


class QueueItemWidget(QFrame):
    """Custom widget for queue item display."""
    
    def __init__(self, item: QueueItem, parent=None):
        super().__init__(parent)
        self.item = item
        self._setup_ui()
        self.update_display()
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QueueItemWidget {
                background-color: #16213e;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
            QueueItemWidget:hover {
                background-color: #1a2a4e;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        
        # Top row: status icon + title + quality
        top_row = QHBoxLayout()
        
        self.status_icon = QLabel("⏳")
        self.status_icon.setFixedWidth(20)
        top_row.addWidget(self.status_icon)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setMaximumWidth(250)
        top_row.addWidget(self.title_label, 1)
        
        self.quality_label = QLabel()
        self.quality_label.setStyleSheet("color: #e94560;")
        top_row.addWidget(self.quality_label)
        
        layout.addLayout(top_row)
        
        # Progress row
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status row
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #8a8aaa; font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def update_display(self):
        """Update widget display from item data."""
        # Title (truncated)
        title = self.item.title
        if len(title) > 35:
            title = title[:32] + "..."
        self.title_label.setText(title)
        self.title_label.setToolTip(self.item.title)
        
        # Quality
        self.quality_label.setText(self.item.quality)
        
        # Status icon and styling
        status_icons = {
            QueueItemStatus.PENDING: ("⏳", "#8a8aaa"),
            QueueItemStatus.WAITING: ("⏳", "#8a8aaa"),
            QueueItemStatus.DOWNLOADING: ("▶", "#4ecdc4"),
            QueueItemStatus.PROCESSING: ("⚙", "#f9ca24"),
            QueueItemStatus.COMPLETED: ("✓", "#4ecdc4"),
            QueueItemStatus.FAILED: ("✗", "#ff6b6b"),
            QueueItemStatus.CANCELLED: ("⊘", "#8a8aaa"),
            QueueItemStatus.PAUSED: ("⏸", "#f9ca24"),
        }
        
        icon, color = status_icons.get(self.item.status, ("?", "#8a8aaa"))
        self.status_icon.setText(icon)
        self.status_icon.setStyleSheet(f"color: {color};")
        
        # Progress
        self.progress_bar.setValue(int(self.item.progress))
        
        # Status text
        if self.item.status == QueueItemStatus.DOWNLOADING:
            status = f"{self.item.progress:.1f}% - {self.item.speed} - ETA: {self.item.eta}"
        elif self.item.status == QueueItemStatus.PROCESSING:
            status = "Processing..."
        elif self.item.status == QueueItemStatus.COMPLETED:
            status = "Completed"
        elif self.item.status == QueueItemStatus.FAILED:
            status = f"Failed: {self.item.error_message[:50]}"
        elif self.item.status == QueueItemStatus.PENDING:
            status = "Waiting..."
        else:
            status = self.item.status.value.title()
        
        self.status_label.setText(status)


class QueuePanel(QWidget):
    """Panel for displaying and managing the download queue."""
    
    item_double_clicked = Signal(str)  # item_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.queue = get_queue_manager()
        self.download_manager = get_download_manager()
        self._item_widgets: dict = {}
        
        self._setup_ui()
        self._connect_signals()
        self._refresh_queue()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📋 Download Queue")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        # Stats
        self.stats_label = QLabel("0 items")
        self.stats_label.setStyleSheet("color: #8a8aaa;")
        header.addWidget(self.stats_label)
        
        layout.addLayout(header)
        
        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setSpacing(4)
        self.queue_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self._show_context_menu)
        self.queue_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.queue_list)
        
        # Control buttons
        controls = QHBoxLayout()
        controls.setSpacing(8)
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setObjectName("primaryButton")
        controls.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        controls.addWidget(self.pause_btn)
        
        self.clear_btn = QPushButton("🗑 Clear Done")
        controls.addWidget(self.clear_btn)
        
        layout.addLayout(controls)
        
        # Import button
        import_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("📥 Import URLs")
        import_layout.addWidget(self.import_btn)
        
        import_layout.addStretch()
        
        layout.addLayout(import_layout)
    
    def _connect_signals(self):
        """Connect signals."""
        # Queue signals
        self.queue.signals.item_added.connect(self._on_item_added)
        self.queue.signals.item_removed.connect(self._on_item_removed)
        self.queue.signals.item_updated.connect(self._on_item_updated)
        self.queue.signals.queue_cleared.connect(self._refresh_queue)
        
        # Download manager signals
        self.download_manager.signals.download_progress.connect(self._on_progress)
        self.download_manager.signals.download_finished.connect(self._on_finished)
        
        # Buttons
        self.start_btn.clicked.connect(self._start_queue)
        self.pause_btn.clicked.connect(self._pause_queue)
        self.clear_btn.clicked.connect(self._clear_completed)
        self.import_btn.clicked.connect(self._import_urls)
    
    def _refresh_queue(self):
        """Refresh the entire queue display."""
        self.queue_list.clear()
        self._item_widgets.clear()
        
        for item in self.queue.get_all_items():
            self._add_item_to_list(item)
        
        self._update_stats()
    
    def _add_item_to_list(self, item: QueueItem):
        """Add item to the list widget."""
        widget = QueueItemWidget(item)
        list_item = QListWidgetItem(self.queue_list)
        list_item.setData(Qt.UserRole, item.id)
        list_item.setSizeHint(widget.sizeHint())
        self.queue_list.setItemWidget(list_item, widget)
        self._item_widgets[item.id] = widget
    
    def _on_item_added(self, item: QueueItem):
        """Handle new item added."""
        self._add_item_to_list(item)
        self._update_stats()
    
    def _on_item_removed(self, item_id: str):
        """Handle item removed."""
        for i in range(self.queue_list.count()):
            list_item = self.queue_list.item(i)
            if list_item.data(Qt.UserRole) == item_id:
                self.queue_list.takeItem(i)
                break
        self._item_widgets.pop(item_id, None)
        self._update_stats()
    
    def _on_item_updated(self, item: QueueItem):
        """Handle item update."""
        widget = self._item_widgets.get(item.id)
        if widget:
            widget.item = item
            widget.update_display()
    
    def _on_progress(self, item_id: str, progress):
        """Handle download progress."""
        widget = self._item_widgets.get(item_id)
        if widget:
            widget.item.progress = progress.percent
            widget.item.speed = progress.speed
            widget.item.eta = progress.eta
            widget.update_display()
    
    def _on_finished(self, item_id: str, success: bool, message: str):
        """Handle download finished."""
        self._update_stats()
    
    def _update_stats(self):
        """Update statistics label."""
        stats = self.queue.get_queue_stats()
        parts = []
        if stats['downloading'] > 0:
            parts.append(f"{stats['downloading']} downloading")
        if stats['pending'] > 0:
            parts.append(f"{stats['pending']} pending")
        if stats['completed'] > 0:
            parts.append(f"{stats['completed']} done")
        if stats['failed'] > 0:
            parts.append(f"{stats['failed']} failed")
        
        self.stats_label.setText(" | ".join(parts) if parts else "Empty")
    
    def _show_context_menu(self, pos):
        """Show context menu for queue items."""
        item = self.queue_list.itemAt(pos)
        if not item:
            return
        
        item_id = item.data(Qt.UserRole)
        queue_item = self.queue.get_item(item_id)
        if not queue_item:
            return
        
        menu = QMenu(self)
        
        if queue_item.status in (QueueItemStatus.PENDING, QueueItemStatus.FAILED):
            start_action = menu.addAction("▶ Start Download")
            start_action.triggered.connect(lambda: self._start_single(item_id))
        
        if queue_item.status == QueueItemStatus.DOWNLOADING:
            cancel_action = menu.addAction("⏹ Cancel")
            cancel_action.triggered.connect(lambda: self._cancel_download(item_id))
        
        if queue_item.status == QueueItemStatus.FAILED:
            retry_action = menu.addAction("🔄 Retry")
            retry_action.triggered.connect(lambda: self._retry_download(item_id))
        
        if queue_item.status == QueueItemStatus.COMPLETED:
            folder_action = menu.addAction("📁 Open Folder")
            folder_action.triggered.connect(lambda: self._open_folder(queue_item))
        
        menu.addSeparator()
        
        move_up = menu.addAction("⬆ Move Up")
        move_up.triggered.connect(lambda: self.queue.move_item(item_id, -1))
        
        move_down = menu.addAction("⬇ Move Down")
        move_down.triggered.connect(lambda: self.queue.move_item(item_id, 1))
        
        menu.addSeparator()
        
        remove_action = menu.addAction("🗑 Remove")
        remove_action.triggered.connect(lambda: self.queue.remove_item(item_id))
        
        menu.exec_(self.queue_list.mapToGlobal(pos))
    
    def _on_item_double_clicked(self, list_item: QListWidgetItem):
        """Handle double-click on item."""
        item_id = list_item.data(Qt.UserRole)
        self.item_double_clicked.emit(item_id)
    
    def _start_queue(self):
        """Start queue processing."""
        self.download_manager.start_queue()
        self.logger.info("Queue started")
    
    def _pause_queue(self):
        """Pause queue processing."""
        self.download_manager.pause_all()
        self.logger.info("Queue paused")
    
    def _clear_completed(self):
        """Clear completed items."""
        self.queue.clear_completed()
        self._refresh_queue()
    
    def _start_single(self, item_id: str):
        """Start a single download."""
        item = self.queue.get_item(item_id)
        if item:
            self.download_manager.download_single(item)
    
    def _cancel_download(self, item_id: str):
        """Cancel a download."""
        self.download_manager.cancel_download(item_id)
    
    def _retry_download(self, item_id: str):
        """Retry failed download."""
        self.download_manager.retry_failed(item_id)
    
    def _open_folder(self, item: QueueItem):
        """Open download folder."""
        from pathlib import Path
        folder = Path(item.output_path)
        if folder.exists():
            open_folder(folder)
    
    def _import_urls(self):
        """Import URLs from file."""
        file, _ = QFileDialog.getOpenFileName(
            self, "Import URLs", "", "Text Files (*.txt);;All Files (*)"
        )
        if not file:
            return
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            for url in urls:
                if url.startswith('http'):
                    self.queue.add_url(url=url, title=f"URL: {url[:50]}...")
            
            self.logger.info(f"Imported {len(urls)} URLs from file")
            QMessageBox.information(
                self, "Import Complete",
                f"Added {len(urls)} URLs to queue"
            )
        except Exception as e:
            self.logger.error(f"Import error: {e}")
            QMessageBox.warning(self, "Import Error", str(e))
