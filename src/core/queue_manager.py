"""
YT-DLP GUI - Queue Manager
Download queue management with persistence and state tracking.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional
from PySide6.QtCore import QObject, Signal

from .config import get_config
from ..utils.logger import get_logger


class QueueItemStatus(Enum):
    """Status of a queue item."""
    PENDING = "pending"
    WAITING = "waiting"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class QueueItem:
    """Represents an item in the download queue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    url: str = ""
    title: str = "Unknown"
    thumbnail: str = ""
    duration: int = 0
    status: QueueItemStatus = QueueItemStatus.PENDING
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    format_spec: str = "best"
    quality: str = "best"
    output_path: str = ""
    output_file: str = ""
    error_message: str = ""
    added_time: str = field(default_factory=lambda: datetime.now().isoformat())
    options: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QueueItem':
        """Create QueueItem from dictionary."""
        data['status'] = QueueItemStatus(data.get('status', 'pending'))
        return cls(**data)


class QueueSignals(QObject):
    """Qt signals for queue operations."""
    item_added = Signal(QueueItem)
    item_removed = Signal(str)  # item_id
    item_updated = Signal(QueueItem)
    queue_cleared = Signal()
    download_started = Signal(str)  # item_id
    download_finished = Signal(str, bool)  # item_id, success
    all_finished = Signal()


class QueueManager(QObject):
    """Manages the download queue with persistence."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.config = get_config()
        self.signals = QueueSignals()
        
        self._queue: List[QueueItem] = []
        self._queue_file = Path(self.config._config_dir) / "queue.json"
        self._is_processing = False
        self._current_download: Optional[str] = None
        
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from file."""
        if self._queue_file.exists():
            try:
                with open(self._queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._queue = [QueueItem.from_dict(item) for item in data]
                
                # Reset in-progress items to pending
                for item in self._queue:
                    if item.status in (QueueItemStatus.DOWNLOADING, QueueItemStatus.PROCESSING):
                        item.status = QueueItemStatus.PENDING
                        item.progress = 0.0
                
                self.logger.info(f"Loaded {len(self._queue)} items from queue")
            except Exception as e:
                self.logger.error(f"Error loading queue: {e}")
                self._queue = []
    
    def _save_queue(self):
        """Save queue to file."""
        try:
            data = [item.to_dict() for item in self._queue]
            with open(self._queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving queue: {e}")
    
    def add_item(self, item: QueueItem) -> str:
        """Add item to queue."""
        self._queue.append(item)
        self._save_queue()
        self.signals.item_added.emit(item)
        self.logger.info(f"Added to queue: {item.title}")
        return item.id
    
    def add_url(
        self,
        url: str,
        title: str = "Unknown",
        thumbnail: str = "",
        duration: int = 0,
        format_spec: str = "best",
        quality: str = "best",
        output_path: str = "",
        options: Optional[Dict] = None
    ) -> str:
        """Create and add a new queue item from URL."""
        if not output_path:
            output_path = self.config.settings.download.output_path
        
        item = QueueItem(
            url=url,
            title=title,
            thumbnail=thumbnail,
            duration=duration,
            format_spec=format_spec,
            quality=quality,
            output_path=output_path,
            options=options or {}
        )
        
        return self.add_item(item)
    
    def remove_item(self, item_id: str):
        """Remove item from queue."""
        self._queue = [item for item in self._queue if item.id != item_id]
        self._save_queue()
        self.signals.item_removed.emit(item_id)
        self.logger.info(f"Removed from queue: {item_id}")
    
    def get_item(self, item_id: str) -> Optional[QueueItem]:
        """Get item by ID."""
        for item in self._queue:
            if item.id == item_id:
                return item
        return None
    
    def update_item(self, item_id: str, **kwargs):
        """Update item properties."""
        item = self.get_item(item_id)
        if item:
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            self._save_queue()
            self.signals.item_updated.emit(item)
    
    def get_all_items(self) -> List[QueueItem]:
        """Get all queue items."""
        return self._queue.copy()
    
    def get_pending_items(self) -> List[QueueItem]:
        """Get items waiting to be downloaded."""
        return [
            item for item in self._queue
            if item.status in (QueueItemStatus.PENDING, QueueItemStatus.WAITING)
        ]
    
    def get_completed_items(self) -> List[QueueItem]:
        """Get completed items."""
        return [item for item in self._queue if item.status == QueueItemStatus.COMPLETED]
    
    def clear_completed(self):
        """Remove all completed items."""
        self._queue = [
            item for item in self._queue
            if item.status != QueueItemStatus.COMPLETED
        ]
        self._save_queue()
        self.signals.queue_cleared.emit()
    
    def clear_all(self):
        """Clear entire queue."""
        self._queue = []
        self._save_queue()
        self.signals.queue_cleared.emit()
    
    def move_item(self, item_id: str, direction: int):
        """Move item up or down in queue."""
        for i, item in enumerate(self._queue):
            if item.id == item_id:
                new_index = max(0, min(len(self._queue) - 1, i + direction))
                if new_index != i:
                    self._queue.pop(i)
                    self._queue.insert(new_index, item)
                    self._save_queue()
                break
    
    def get_next_pending(self) -> Optional[QueueItem]:
        """Get next item to download."""
        for item in self._queue:
            if item.status == QueueItemStatus.PENDING:
                return item
        return None
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        stats = {
            'total': len(self._queue),
            'pending': 0,
            'downloading': 0,
            'completed': 0,
            'failed': 0
        }
        
        for item in self._queue:
            if item.status == QueueItemStatus.PENDING:
                stats['pending'] += 1
            elif item.status in (QueueItemStatus.DOWNLOADING, QueueItemStatus.PROCESSING):
                stats['downloading'] += 1
            elif item.status == QueueItemStatus.COMPLETED:
                stats['completed'] += 1
            elif item.status == QueueItemStatus.FAILED:
                stats['failed'] += 1
        
        return stats
    
    @property
    def is_processing(self) -> bool:
        return self._is_processing
    
    @is_processing.setter
    def is_processing(self, value: bool):
        self._is_processing = value


# Singleton instance
_queue_manager: Optional[QueueManager] = None


def get_queue_manager() -> QueueManager:
    """Get the singleton queue manager instance."""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager()
    return _queue_manager
