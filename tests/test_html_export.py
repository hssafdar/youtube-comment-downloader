#!/usr/bin/env python
"""Tests for HTML export functionality"""

import os
import tempfile
from youtube_comment_downloader.html_export import generate_html_output


def test_html_generation_basic():
    """Test basic HTML generation with sample comments"""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        generate_html_output(comments, output_path)
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Read and verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key elements
        assert '<!DOCTYPE html>' in content
        assert 'Test comment' in content
        assert 'Test User' in content
        assert '1 day ago' in content
        assert 'YouTube Comments' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_html_generation_with_replies():
    """Test HTML generation with nested replies"""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        generate_html_output(comments, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for reply structure
        assert 'Parent comment' in content
        assert 'Reply to parent' in content
        assert 'toggleReplies' in content
        assert 'replies-container' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_html_generation_with_filter():
    """Test HTML generation with filtered user"""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        generate_html_output(comments, output_path, filtered_user='@TestUser')
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for filtered user in title
        assert 'Filtered by @TestUser' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_html_generation_empty_comments():
    """Test HTML generation with no comments"""
    comments = []
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        generate_html_output(comments, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for "no comments" message
        assert 'No comments available' in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_html_xss_protection():
    """Test that HTML special characters are escaped"""
    comments = [
        {
            'cid': 'test1',
            'text': '<script>alert("XSS")</script>',
            'time': '1 day ago',
            'author': 'Hacker<script>',
            'channel': 'UC123',
            'votes': '10',
            'replies': 0,
            'photo': '',
            'heart': False,
            'reply': False
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        generate_html_output(comments, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify that script tags are escaped
        assert '&lt;script&gt;' in content
        assert '<script>alert("XSS")</script>' not in content
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
