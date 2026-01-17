#!/usr/bin/env python
"""Tests for PDF export functionality"""

import os
import tempfile
from youtube_comment_downloader.pdf_export import generate_pdf_output, REPORTLAB_AVAILABLE


def test_pdf_generation_basic():
    """Test basic PDF generation"""
    if not REPORTLAB_AVAILABLE:
        print("⚠ Skipping PDF tests - reportlab not installed")
        return
    
    comments = [
        {
            'cid': '1',
            'author': 'Test User',
            'text': 'This is a test comment',
            'time': '1 day ago',
            'votes': '5',
            'reply': False
        }
    ]
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        output_path = f.name
    
    try:
        generate_pdf_output(comments, output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
        print("✓ test_pdf_generation_basic passed")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_pdf_generation_with_replies():
    """Test PDF generation with replies"""
    if not REPORTLAB_AVAILABLE:
        print("⚠ Skipping PDF tests - reportlab not installed")
        return
    
    comments = [
        {
            'cid': 'parent1',
            'author': 'User 1',
            'text': 'Parent comment',
            'time': '2 days ago',
            'votes': '10',
            'reply': False
        },
        {
            'cid': 'parent1.reply1',
            'author': 'User 2',
            'text': 'Reply to parent',
            'time': '1 day ago',
            'votes': '3',
            'reply': True
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        output_path = f.name
    
    try:
        generate_pdf_output(comments, output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
        print("✓ test_pdf_generation_with_replies passed")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_pdf_generation_with_filter():
    """Test PDF generation with filter label"""
    if not REPORTLAB_AVAILABLE:
        print("⚠ Skipping PDF tests - reportlab not installed")
        return
    
    comments = [
        {
            'cid': '1',
            'author': 'Test User',
            'text': 'Filtered comment',
            'time': '1 day ago',
            'votes': '5',
            'reply': False
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        output_path = f.name
    
    try:
        generate_pdf_output(comments, output_path, filtered_user='Test User')
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
        print("✓ test_pdf_generation_with_filter passed")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == '__main__':
    test_pdf_generation_basic()
    test_pdf_generation_with_replies()
    test_pdf_generation_with_filter()
    print("\nAll PDF export tests passed! ✓")
