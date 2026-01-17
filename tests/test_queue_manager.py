#!/usr/bin/env python
"""Tests for queue management functionality"""

import os
import tempfile
import shutil
from pathlib import Path
from youtube_comment_downloader.queue_manager import QueueManager, QueueItem, QueueItemStatus


def test_queue_manager_initialization():
    """Test QueueManager initialization"""
    manager = QueueManager()
    assert manager.queue == []
    assert manager.current_index == 0
    assert manager.is_paused == False
    assert isinstance(manager.settings, dict)


def test_add_item_to_queue():
    """Test adding items to queue"""
    manager = QueueManager()
    
    # Add first item
    result = manager.add_item('video123', 'https://youtube.com/watch?v=video123', 'Test Video')
    assert result == True
    assert len(manager.queue) == 1
    assert manager.queue[0].video_id == 'video123'
    assert manager.queue[0].title == 'Test Video'
    assert manager.queue[0].status == QueueItemStatus.PENDING
    
    # Try to add duplicate
    result = manager.add_item('video123', 'https://youtube.com/watch?v=video123', 'Test Video')
    assert result == False
    assert len(manager.queue) == 1


def test_remove_item_from_queue():
    """Test removing items from queue"""
    manager = QueueManager()
    
    manager.add_item('video1', 'url1', 'Video 1')
    manager.add_item('video2', 'url2', 'Video 2')
    manager.add_item('video3', 'url3', 'Video 3')
    
    assert len(manager.queue) == 3
    
    # Remove middle item
    manager.remove_item(1)
    assert len(manager.queue) == 2
    assert manager.queue[0].video_id == 'video1'
    assert manager.queue[1].video_id == 'video3'


def test_clear_queue():
    """Test clearing all items from queue"""
    manager = QueueManager()
    
    manager.add_item('video1', 'url1', 'Video 1')
    manager.add_item('video2', 'url2', 'Video 2')
    
    assert len(manager.queue) == 2
    
    manager.clear_queue()
    assert len(manager.queue) == 0
    assert manager.current_index == 0


def test_get_next_pending():
    """Test getting next pending item"""
    manager = QueueManager()
    
    # Add items with different statuses
    item1 = QueueItem('video1', 'url1', 'Video 1')
    item1.status = QueueItemStatus.COMPLETE
    manager.queue.append(item1)
    
    item2 = QueueItem('video2', 'url2', 'Video 2')
    item2.status = QueueItemStatus.PENDING
    manager.queue.append(item2)
    
    item3 = QueueItem('video3', 'url3', 'Video 3')
    item3.status = QueueItemStatus.PENDING
    manager.queue.append(item3)
    
    # Should return first pending item
    next_item = manager.get_next_pending()
    assert next_item is not None
    assert next_item.video_id == 'video2'


def test_has_pending_items():
    """Test checking for pending items"""
    manager = QueueManager()
    
    # Empty queue
    assert manager.has_pending_items() == False
    
    # Add completed item
    item1 = QueueItem('video1', 'url1', 'Video 1')
    item1.status = QueueItemStatus.COMPLETE
    manager.queue.append(item1)
    assert manager.has_pending_items() == False
    
    # Add pending item
    item2 = QueueItem('video2', 'url2', 'Video 2')
    item2.status = QueueItemStatus.PENDING
    manager.queue.append(item2)
    assert manager.has_pending_items() == True
    
    # Add paused item
    item3 = QueueItem('video3', 'url3', 'Video 3')
    item3.status = QueueItemStatus.PAUSED
    manager.queue.append(item3)
    assert manager.has_pending_items() == True


def test_queue_item_serialization():
    """Test QueueItem to/from dict conversion"""
    item = QueueItem('video123', 'https://youtube.com/watch?v=video123', 'Test Video')
    item.status = QueueItemStatus.DOWNLOADING
    item.comments_downloaded = 50
    item.total_comments = 100
    item.error_message = None
    
    # Convert to dict
    data = item.to_dict()
    assert data['video_id'] == 'video123'
    assert data['video_url'] == 'https://youtube.com/watch?v=video123'
    assert data['title'] == 'Test Video'
    assert data['status'] == 'downloading'
    assert data['comments_downloaded'] == 50
    assert data['total_comments'] == 100
    
    # Convert back from dict
    restored_item = QueueItem.from_dict(data)
    assert restored_item.video_id == 'video123'
    assert restored_item.video_url == 'https://youtube.com/watch?v=video123'
    assert restored_item.title == 'Test Video'
    assert restored_item.status == QueueItemStatus.DOWNLOADING
    assert restored_item.comments_downloaded == 50
    assert restored_item.total_comments == 100


def test_save_and_load_state():
    """Test saving and loading queue state"""
    # Create temp directory for state file
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Override state directory
        manager = QueueManager()
        manager.state_dir = Path(temp_dir)
        manager.state_file = manager.state_dir / 'queue_state.json'
        
        # Add items
        manager.add_item('video1', 'url1', 'Video 1')
        manager.add_item('video2', 'url2', 'Video 2')
        manager.settings = {'export_folder': '/tmp/exports'}
        
        # Save state
        manager.save_state()
        
        # Verify file exists
        assert manager.state_file.exists()
        
        # Create new manager and load state
        manager2 = QueueManager()
        manager2.state_dir = Path(temp_dir)
        manager2.state_file = manager2.state_dir / 'queue_state.json'
        
        result = manager2.load_state()
        assert result == True
        assert len(manager2.queue) == 2
        assert manager2.queue[0].video_id == 'video1'
        assert manager2.queue[1].video_id == 'video2'
        assert manager2.settings == {'export_folder': '/tmp/exports'}
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_load_state_no_file():
    """Test loading state when no file exists"""
    manager = QueueManager()
    manager.state_file = Path('/nonexistent/queue_state.json')
    
    result = manager.load_state()
    assert result == False


if __name__ == '__main__':
    test_queue_manager_initialization()
    print("✓ test_queue_manager_initialization passed")
    
    test_add_item_to_queue()
    print("✓ test_add_item_to_queue passed")
    
    test_remove_item_from_queue()
    print("✓ test_remove_item_from_queue passed")
    
    test_clear_queue()
    print("✓ test_clear_queue passed")
    
    test_get_next_pending()
    print("✓ test_get_next_pending passed")
    
    test_has_pending_items()
    print("✓ test_has_pending_items passed")
    
    test_queue_item_serialization()
    print("✓ test_queue_item_serialization passed")
    
    test_save_and_load_state()
    print("✓ test_save_and_load_state passed")
    
    test_load_state_no_file()
    print("✓ test_load_state_no_file passed")
    
    print("\nAll queue manager tests passed! ✓")
