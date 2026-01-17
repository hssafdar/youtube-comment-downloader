#!/usr/bin/env python
"""Tests for TXT export functionality"""

import os
import tempfile
from youtube_comment_downloader.txt_export import generate_txt_output


def test_txt_generation_basic():
    """Test basic TXT generation with sample comments"""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_path = f.name
    
    try:
        generate_txt_output(comments, output_path)
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Read and verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key elements
        assert 'YouTube Comments' in content
        assert 'Test comment' in content
        assert 'Test User' in content
        assert '1 day ago' in content
        assert '👍 10' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_txt_generation_with_replies():
    """Test TXT generation with nested replies"""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_path = f.name
    
    try:
        generate_txt_output(comments, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for reply structure
        assert 'Parent comment' in content
        assert 'Reply to parent' in content
        assert '↳ Reply to' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_txt_generation_with_hearted():
    """Test TXT generation with hearted comments"""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_path = f.name
    
    try:
        generate_txt_output(comments, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for hearted indicator
        assert '[♥ Hearted by Creator]' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_txt_generation_with_filter():
    """Test TXT generation with filtered user"""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_path = f.name
    
    try:
        generate_txt_output(comments, output_path, filtered_user='@TestUser')
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for filtered user in header
        assert 'Filtered by: @TestUser' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == '__main__':
    test_txt_generation_basic()
    print("✓ test_txt_generation_basic passed")
    
    test_txt_generation_with_replies()
    print("✓ test_txt_generation_with_replies passed")
    
    test_txt_generation_with_hearted()
    print("✓ test_txt_generation_with_hearted passed")
    
    test_txt_generation_with_filter()
    print("✓ test_txt_generation_with_filter passed")
    
    print("\nAll TXT export tests passed! ✓")
