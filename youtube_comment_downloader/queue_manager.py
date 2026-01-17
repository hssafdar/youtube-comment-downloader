#!/usr/bin/env python
"""
Queue management for YouTube Comment Downloader
Handles queue state, persistence, and operations
"""

import json
import os
from pathlib import Path
from datetime import datetime
from enum import Enum


class QueueItemStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETE = "complete"
    SKIPPED = "skipped"
    ERROR = "error"


class QueueItem:
    def __init__(self, video_id, video_url, title=None):
        self.video_id = video_id
        self.video_url = video_url
        self.title = title or "Loading..."
        self.status = QueueItemStatus.PENDING
        self.comments_downloaded = 0
        self.total_comments = 0
        self.error_message = None
    
    def to_dict(self):
        return {
            'video_id': self.video_id,
            'video_url': self.video_url,
            'title': self.title,
            'status': self.status.value,
            'comments_downloaded': self.comments_downloaded,
            'total_comments': self.total_comments,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(data['video_id'], data['video_url'], data.get('title'))
        item.status = QueueItemStatus(data.get('status', 'pending'))
        item.comments_downloaded = data.get('comments_downloaded', 0)
        item.total_comments = data.get('total_comments', 0)
        item.error_message = data.get('error_message')
        return item


class QueueManager:
    def __init__(self):
        self.queue = []
        self.current_index = 0
        self.is_paused = False
        self.settings = {}
        
        self.state_dir = Path.home() / '.youtube_comment_downloader'
        self.state_file = self.state_dir / 'queue_state.json'
    
    def add_item(self, video_id, video_url, title=None):
        """Add item to queue"""
        # Check for duplicates
        for item in self.queue:
            if item.video_id == video_id:
                return False
        
        item = QueueItem(video_id, video_url, title)
        self.queue.append(item)
        self.save_state()
        return True
    
    def remove_item(self, index):
        """Remove item from queue"""
        if 0 <= index < len(self.queue):
            self.queue.pop(index)
            self.save_state()
    
    def clear_queue(self):
        """Clear all items from queue"""
        self.queue.clear()
        self.current_index = 0
        self.save_state()
    
    def get_next_pending(self):
        """Get next pending item"""
        for item in self.queue:
            if item.status == QueueItemStatus.PENDING:
                return item
        return None
    
    def save_state(self):
        """Save queue state to file"""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        state = {
            'queue': [item.to_dict() for item in self.queue],
            'settings': self.settings,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Load queue state from file"""
        if not self.state_file.exists():
            return False
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.queue = [QueueItem.from_dict(d) for d in state.get('queue', [])]
            self.settings = state.get('settings', {})
            return True
        except (json.JSONDecodeError, KeyError):
            return False
    
    def has_pending_items(self):
        """Check if there are pending or paused items"""
        return any(item.status in (QueueItemStatus.PENDING, QueueItemStatus.PAUSED) 
                   for item in self.queue)
