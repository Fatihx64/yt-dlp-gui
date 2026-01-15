"""
YT-DLP GUI - Download Manager
Manages concurrent downloads with queue integration.
"""

from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal, QThread

from .ytdlp_wrapper import YTDLPWrapper, DownloadProgress, VideoInfo
from .queue_manager import QueueManager, QueueItem, QueueItemStatus, get_queue_manager
from .config import get_config
from ..utils.logger import get_logger


class DownloadWorker(QThread):
    """Worker thread for individual downloads."""
    
    progress = Signal(str, DownloadProgress)  # item_id, progress
    finished = Signal(str, bool, str)  # item_id, success, message
    
    def __init__(self, item: QueueItem):
        super().__init__()
        self.item = item
        self.wrapper = YTDLPWrapper()
        self._cancelled = False
    
    def run(self):
        """Execute the download."""
        try:
            # Build options from item and config
            config = get_config()
            options = {
                'embed_thumbnail': config.settings.download.embed_thumbnail,
                'embed_metadata': config.settings.download.embed_metadata,
                'embed_subtitles': config.settings.download.embed_subtitles,
                'subtitle_langs': config.settings.download.subtitle_languages,
                'rate_limit': config.settings.download.rate_limit or self.item.options.get('rate_limit'),
                'proxy': config.settings.network.proxy or self.item.options.get('proxy'),
                'cookies_file': self.item.options.get('cookies_file'),
                'clip_start': self.item.options.get('clip_start'),
                'clip_end': self.item.options.get('clip_end'),
            }
            options.update(self.item.options)
            
            # Connect signals
            self.wrapper.signals.progress.connect(
                lambda p: self.progress.emit(self.item.id, p)
            )
            self.wrapper.signals.finished.connect(
                lambda success, msg: self.finished.emit(self.item.id, success, msg)
            )
            
            # Start download (synchronous in thread context)
            self.wrapper.download(
                url=self.item.url,
                output_path=self.item.output_path,
                format_spec=self.item.format_spec,
                options=options,
                task_id=self.item.id
            )
            
            # Wait for completion (signals handle the rest)
            while self.item.id in self.wrapper._active_processes:
                if self._cancelled:
                    self.wrapper.cancel(self.item.id)
                    break
                self.msleep(100)
                
        except Exception as e:
            self.finished.emit(self.item.id, False, str(e))
    
    def cancel(self):
        """Cancel the download."""
        self._cancelled = True
        self.wrapper.cancel(self.item.id)


class DownloadManagerSignals(QObject):
    """Qt signals for download manager."""
    download_started = Signal(str)  # item_id
    download_progress = Signal(str, DownloadProgress)  # item_id, progress
    download_finished = Signal(str, bool, str)  # item_id, success, message
    all_finished = Signal()
    queue_updated = Signal()


class DownloadManager(QObject):
    """Manages concurrent downloads with queue integration."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.config = get_config()
        self.queue = get_queue_manager()
        self.signals = DownloadManagerSignals()
        
        self._workers: Dict[str, DownloadWorker] = {}
        self._is_running = False
        self._max_concurrent = self.config.settings.download.concurrent_downloads
    
    @property
    def active_count(self) -> int:
        """Number of active downloads."""
        return len(self._workers)
    
    @property
    def is_running(self) -> bool:
        """Whether the download manager is processing queue."""
        return self._is_running
    
    def start_queue(self):
        """Start processing the download queue."""
        if self._is_running:
            return
        
        self._is_running = True
        self.queue.is_processing = True
        self.logger.info("Starting download queue processing")
        self._process_queue()
    
    def stop_queue(self):
        """Stop processing queue (doesn't cancel active downloads)."""
        self._is_running = False
        self.queue.is_processing = False
        self.logger.info("Stopped download queue processing")
    
    def pause_all(self):
        """Pause all active downloads."""
        for worker in list(self._workers.values()):
            worker.cancel()
        self._is_running = False
        self.queue.is_processing = False
    
    def _process_queue(self):
        """Process next items in queue."""
        if not self._is_running:
            return
        
        while self.active_count < self._max_concurrent:
            item = self.queue.get_next_pending()
            if not item:
                break
            
            self._start_download(item)
        
        # Check if all done
        if self.active_count == 0 and not self.queue.get_pending_items():
            self._is_running = False
            self.queue.is_processing = False
            self.signals.all_finished.emit()
            self.logger.info("All downloads completed")
    
    def _start_download(self, item: QueueItem):
        """Start downloading a single item."""
        if item.id in self._workers:
            return
        
        self.logger.info(f"Starting download: {item.title}")
        
        # Update queue item status
        self.queue.update_item(item.id, status=QueueItemStatus.DOWNLOADING)
        
        # Create and start worker
        worker = DownloadWorker(item)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        
        self._workers[item.id] = worker
        worker.start()
        
        self.signals.download_started.emit(item.id)
    
    def _on_progress(self, item_id: str, progress: DownloadProgress):
        """Handle download progress update."""
        status = QueueItemStatus.DOWNLOADING
        if progress.status == "processing":
            status = QueueItemStatus.PROCESSING
        
        self.queue.update_item(
            item_id,
            status=status,
            progress=progress.percent,
            speed=progress.speed,
            eta=progress.eta
        )
        
        self.signals.download_progress.emit(item_id, progress)
    
    def _on_finished(self, item_id: str, success: bool, message: str):
        """Handle download completion."""
        worker = self._workers.pop(item_id, None)
        if worker:
            worker.quit()
            worker.wait()
        
        if success:
            self.logger.info(f"Download completed: {item_id}")
            self.queue.update_item(
                item_id,
                status=QueueItemStatus.COMPLETED,
                progress=100.0,
                output_file=message
            )
        else:
            self.logger.error(f"Download failed: {item_id} - {message}")
            self.queue.update_item(
                item_id,
                status=QueueItemStatus.FAILED,
                error_message=message
            )
        
        self.signals.download_finished.emit(item_id, success, message)
        self.signals.queue_updated.emit()
        
        # Process next in queue
        self._process_queue()
    
    def download_single(self, item: QueueItem):
        """Download a single item immediately (bypasses queue)."""
        self._start_download(item)
    
    def cancel_download(self, item_id: str):
        """Cancel a specific download."""
        worker = self._workers.get(item_id)
        if worker:
            worker.cancel()
            self.queue.update_item(item_id, status=QueueItemStatus.CANCELLED)
    
    def retry_failed(self, item_id: str):
        """Retry a failed download."""
        item = self.queue.get_item(item_id)
        if item and item.status == QueueItemStatus.FAILED:
            self.queue.update_item(item_id, status=QueueItemStatus.PENDING, progress=0.0)
            if self._is_running:
                self._process_queue()


# Singleton instance
_download_manager: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """Get the singleton download manager instance."""
    global _download_manager
    if _download_manager is None:
        _download_manager = DownloadManager()
    return _download_manager
