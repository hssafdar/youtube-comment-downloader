#!/usr/bin/env python
"""Tests for JSON export functionality"""

import json
import os
import tempfile
from youtube_comment_downloader.json_export import generate_json_output


def test_json_generation_basic():
    """Test basic JSON generation with sample comments"""
    comments = [
        {
            'cid': 'test1',
            'text': 'Test comment',
            'time': '1 day ago',
            'author': 'Test User',
            'channel': 'UC123',
            'votes': '10',
            'replies': 0,
            'photo': 'https://example.com/photo.jpg',
            'heart': False,
            'reply': False
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        generate_json_output(comments, output_path)
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Read and parse JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check structure
        assert 'metadata' in data
        assert 'comments' in data
        assert data['metadata']['total_comments'] == 1
        assert data['metadata']['root_comments'] == 1
        assert len(data['comments']) == 1
        assert data['comments'][0]['text'] == 'Test comment'
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_json_generation_with_replies():
    """Test JSON generation with nested replies"""
    comments = [
        {
            'cid': 'parent1',
            'text': 'Parent comment',
            'time': '2 days ago',
            'author': 'Parent User',
            'channel': 'UC456',
            'votes': '20',
            'replies': 1,
            'photo': '',
            'heart': False,
            'reply': False
        },
        {
            'cid': 'parent1.reply1',
            'text': 'Reply to parent',
            'time': '1 day ago',
            'author': 'Reply User',
            'channel': 'UC789',
            'votes': '5',
            'replies': 0,
            'photo': '',
            'heart': False,
            'reply': True
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        generate_json_output(comments, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check for threading
        assert data['metadata']['total_comments'] == 2
        assert data['metadata']['root_comments'] == 1
        assert len(data['comments']) == 1
        assert 'thread_replies' in data['comments'][0]
        assert len(data['comments'][0]['thread_replies']) == 1
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_json_generation_with_filter():
    """Test JSON generation with filtered user"""
    comments = [
        {
            'cid': 'test1',
            'text': 'Test comment',
            'time': '1 day ago',
            'author': 'Test User',
            'channel': 'UC123',
            'votes': '10',
            'replies': 0,
            'photo': '',
            'heart': False,
            'reply': False
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        generate_json_output(comments, output_path, filtered_user='@TestUser')
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check for filtered user in metadata
        assert 'filtered_by' in data['metadata']
        assert data['metadata']['filtered_by'] == '@TestUser'
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_json_generation_with_hearted():
    """Test JSON generation preserves heart field"""
    comments = [
        {
            'cid': 'test1',
            'text': 'Hearted comment',
            'time': '1 day ago',
            'author': 'Test User',
            'channel': 'UC123',
            'votes': '100',
            'replies': 0,
            'photo': '',
            'heart': True,
            'reply': False
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        generate_json_output(comments, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check for heart field
        assert data['comments'][0]['heart'] == True
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == '__main__':
    test_json_generation_basic()
    print("✓ test_json_generation_basic passed")
    
    test_json_generation_with_replies()
    print("✓ test_json_generation_with_replies passed")
    
    test_json_generation_with_filter()
    print("✓ test_json_generation_with_filter passed")
    
    test_json_generation_with_hearted()
    print("✓ test_json_generation_with_hearted passed")
    
    print("\nAll JSON export tests passed! ✓")
