#!/usr/bin/env python
"""
Utilities for file system operations and organization
"""

import os
import re
import platform
import subprocess


def sanitize_filename(filename):
    """
    Sanitize a filename by removing or replacing invalid characters
    
    Args:
        filename: Original filename
    
    Returns:
        Safe filename string
    """
    # Remove or replace invalid characters
    # Windows: < > : " / \ | ? *
    # Also remove control characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    
    # Trim whitespace
    filename = filename.strip()
    
    # Limit length (leave room for extension and path)
    max_length = 200
    if len(filename) > max_length:
        filename = filename[:max_length].strip()
    
    # If empty after sanitization, use a default
    if not filename:
        filename = 'untitled'
    
    return filename


def create_export_path(base_folder, creator_name, video_title, export_format, is_filtered=False, is_post=False):
    """
    Create the full export path following the folder organization structure
    
    Args:
        base_folder: Base export directory
        creator_name: Name of the content creator
        video_title: Title of the video or post
        export_format: Export format (html, txt, json)
        is_filtered: Whether this is a filtered export
        is_post: Whether this is a community post (vs video)
    
    Returns:
        Tuple of (full_path, directory_path)
    """
    # Sanitize names
    safe_creator = sanitize_filename(creator_name)
    safe_title = sanitize_filename(video_title)
    
    # Build directory structure
    creator_folder = os.path.join(base_folder, safe_creator)
    
    if is_post:
        content_folder = os.path.join(creator_folder, 'posts')
    else:
        content_folder = os.path.join(creator_folder, 'videos')
    
    # Create directory if it doesn't exist
    os.makedirs(content_folder, exist_ok=True)
    
    # Build filename
    filtered_suffix = ' - filtered' if is_filtered else ''
    filename = f"{safe_title} - comments{filtered_suffix}.{export_format}"
    
    full_path = os.path.join(content_folder, filename)
    
    return full_path, content_folder


def open_folder(folder_path):
    """
    Open a folder in the system's file explorer
    
    Args:
        folder_path: Path to the folder to open
    """
    try:
        system = platform.system()
        
        if system == 'Windows':
            os.startfile(folder_path)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', folder_path], check=False)
        else:  # Linux and other Unix-like systems
            subprocess.run(['xdg-open', folder_path], check=False)
    except (OSError, subprocess.SubprocessError):
        # Silently fail if we can't open the folder
        pass
