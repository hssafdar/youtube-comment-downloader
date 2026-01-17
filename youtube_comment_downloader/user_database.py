#!/usr/bin/env python
"""
User database management for YouTube Comment Downloader
Stores user information and preferences for filtering
"""

import sqlite3
import os
import re
import json
from pathlib import Path
import requests


class UserDatabase:
    """Manages storage and retrieval of YouTube user information"""
    
    # Constants for validation
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 100
    MIN_CHANNEL_ID_LENGTH = 20
    
    def __init__(self):
        """Initialize the database"""
        # Store database in user's home directory
        self.db_dir = Path.home() / '.youtube_comment_downloader'
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / 'users.db'
        self._init_db()
    
    def _is_valid_channel_id(self, channel_id):
        """
        Validate if a string is a valid YouTube channel ID
        
        Args:
            channel_id: String to validate
        
        Returns:
            Boolean indicating if valid
        """
        return (isinstance(channel_id, str) and 
                channel_id.startswith('UC') and 
                len(channel_id) > self.MIN_CHANNEL_ID_LENGTH)
    
    def _init_db(self):
        """Create the database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                display_name TEXT,
                profile_pic_url TEXT,
                channel_url TEXT,
                in_dropdown INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, display_name=None, profile_pic_url=None, channel_url=None, in_dropdown=True):
        """
        Add or update a user in the database
        
        Args:
            user_id: YouTube channel ID (unique identifier)
            username: Username/handle
            display_name: Display name (optional)
            profile_pic_url: URL to profile picture (optional)
            channel_url: URL to channel (optional)
            in_dropdown: Whether to show in dropdown (default True)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, display_name, profile_pic_url, channel_url, in_dropdown)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, display_name or username, profile_pic_url, channel_url, 1 if in_dropdown else 0))
            
            conn.commit()
            conn.close()
            return True
        except (sqlite3.Error, OSError):
            return False
    
    def get_user(self, user_id):
        """
        Get a user by their ID
        
        Args:
            user_id: YouTube channel ID
        
        Returns:
            Dictionary with user info or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except (sqlite3.Error, OSError):
            return None
    
    def get_all_users(self):
        """
        Get all users in the database
        
        Returns:
            List of user dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users ORDER BY username')
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except (sqlite3.Error, OSError):
            return []
    
    def get_dropdown_users(self):
        """
        Get users that should appear in the dropdown
        
        Returns:
            List of user dictionaries where in_dropdown is True
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE in_dropdown = 1 ORDER BY username')
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except (sqlite3.Error, OSError):
            return []
    
    def update_dropdown_status(self, user_id, in_dropdown):
        """
        Update whether a user appears in the dropdown
        
        Args:
            user_id: YouTube channel ID
            in_dropdown: Boolean for dropdown visibility
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE users SET in_dropdown = ? WHERE user_id = ?',
                (1 if in_dropdown else 0, user_id)
            )
            
            conn.commit()
            conn.close()
            return True
        except (sqlite3.Error, OSError):
            return False
    
    def delete_user(self, user_id):
        """
        Delete a user from the database
        
        Args:
            user_id: YouTube channel ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except (sqlite3.Error, OSError):
            return False
    
    def clear_all_users(self):
        """
        Clear all users from the database
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users')
            
            conn.commit()
            conn.close()
            return True
        except (sqlite3.Error, OSError):
            return False
    
    def search_users(self, query):
        """
        Search for users by username or display name
        
        Args:
            query: Search string
        
        Returns:
            List of matching user dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f'%{query}%'
            cursor.execute(
                'SELECT * FROM users WHERE username LIKE ? OR display_name LIKE ? ORDER BY username',
                (search_pattern, search_pattern)
            )
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except (sqlite3.Error, OSError):
            return []
    
    def fetch_user_from_url(self, url):
        """
        Fetch user information from a YouTube channel URL
        
        Supports various URL formats:
        - https://www.youtube.com/@username
        - https://www.youtube.com/channel/UC...
        - https://www.youtube.com/c/channelname
        
        Args:
            url: YouTube channel URL
        
        Returns:
            Dictionary with user info (user_id, username, display_name, profile_pic_url)
            or None if extraction fails
        """
        try:
            # Normalize URL
            url = url.strip()
            if not url.startswith('http'):
                url = 'https://' + url
            
            # Validate it's a YouTube URL to prevent SSRF
            parsed_url = requests.utils.urlparse(url)
            if parsed_url.netloc not in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
                return None
            
            # Extract channel ID directly from URL if it's a /channel/ URL
            channel_id_match = re.search(r'/channel/(UC[A-Za-z0-9_-]+)', url)
            if channel_id_match:
                # For /channel/ URLs, we can extract ID directly
                channel_id = channel_id_match.group(1)
                # Still need to fetch the page for other info
            else:
                channel_id = None
            
            # Make request with better headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Set cookie to bypass consent
            session = requests.Session()
            session.headers.update(headers)
            session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            html = response.text
            
            # Extract data from ytInitialData
            yt_initial_data_pattern = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;\s*(?:var\s+meta|</script|\n)'
            match = re.search(yt_initial_data_pattern, html, re.DOTALL)
            
            if not match:
                return None
            
            data = json.loads(match.group(1))
            
            # Extract channel metadata
            user_info = {}
            
            # Use channel ID from URL if we found it
            if channel_id:
                user_info['user_id'] = channel_id
            
            # Try to find channel ID from page data
            if 'user_id' not in user_info:
                # Method 1: From channelId in metadata
                metadata = self._search_dict(data, 'channelId')
                for ch_id in metadata:
                    if self._is_valid_channel_id(ch_id):
                        user_info['user_id'] = ch_id
                        break
            
            # Method 2: From externalId
            if 'user_id' not in user_info:
                external_ids = self._search_dict(data, 'externalId')
                for ext_id in external_ids:
                    if self._is_valid_channel_id(ext_id):
                        user_info['user_id'] = ext_id
                        break
            
            # Extract display name/title - look for channel metadata
            # Try to find the channel name from header
            headers_data = self._search_dict(data, 'header')
            for header in headers_data:
                if isinstance(header, dict):
                    # Look for c4TabbedHeaderRenderer or pageHeaderRenderer
                    for renderer_key in ['c4TabbedHeaderRenderer', 'pageHeaderRenderer', 'carouselHeaderRenderer']:
                        if renderer_key in header:
                            renderer = header[renderer_key]
                            # Try to get title
                            if 'title' in renderer:
                                title = renderer['title']
                                if isinstance(title, str):
                                    user_info['display_name'] = title
                                elif isinstance(title, dict) and 'simpleText' in title:
                                    user_info['display_name'] = title['simpleText']
                            # Try to get avatar/thumbnail
                            if 'avatar' in renderer and 'thumbnails' in renderer['avatar']:
                                thumbnails = renderer['avatar']['thumbnails']
                                if thumbnails and len(thumbnails) > 0:
                                    user_info['profile_pic_url'] = thumbnails[-1].get('url', '')
                            break
                    if 'display_name' in user_info:
                        break
            
            # Fallback: Extract from metadata
            if 'display_name' not in user_info:
                metadata_list = self._search_dict(data, 'metadata')
                for metadata in metadata_list:
                    if isinstance(metadata, dict) and 'channelMetadataRenderer' in metadata:
                        renderer = metadata['channelMetadataRenderer']
                        if 'title' in renderer:
                            user_info['display_name'] = renderer['title']
                        if 'avatar' in renderer and 'thumbnails' in renderer['avatar']:
                            thumbnails = renderer['avatar']['thumbnails']
                            if thumbnails:
                                user_info['profile_pic_url'] = thumbnails[-1].get('url', '')
                        break
            
            # Last resort: look for any title field
            if 'display_name' not in user_info:
                titles = self._search_dict(data, 'title')
                for title in titles:
                    if isinstance(title, str) and title and self.MIN_TITLE_LENGTH < len(title) < self.MAX_TITLE_LENGTH:
                        user_info['display_name'] = title
                        break
                    elif isinstance(title, dict) and 'simpleText' in title:
                        text = title['simpleText']
                        if text and self.MIN_TITLE_LENGTH < len(text) < self.MAX_TITLE_LENGTH:
                            user_info['display_name'] = text
                            break
            
            # Validate we have the minimum required info
            if 'user_id' not in user_info or 'display_name' not in user_info:
                return None
            
            # Set username as display name if not already set
            if 'username' not in user_info:
                user_info['username'] = user_info['display_name']
            
            user_info['channel_url'] = f"https://www.youtube.com/channel/{user_info['user_id']}"
            
            return user_info
            
        except (requests.RequestException, json.JSONDecodeError, ValueError, KeyError) as e:
            # Return None on any error
            return None
    
    def _search_dict(self, data, key):
        """
        Recursively search for a key in nested dictionaries and lists
        
        Args:
            data: Dictionary or list to search
            key: Key to search for
        
        Yields:
            Values found for the key
        """
        if isinstance(data, dict):
            if key in data:
                yield data[key]
            for value in data.values():
                yield from self._search_dict(value, key)
        elif isinstance(data, list):
            for item in data:
                yield from self._search_dict(item, key)
    
    def user_folder_exists(self, export_dir, username):
        """
        Check if a user's folder exists in the export directory
        
        Args:
            export_dir: Export directory path
            username: Username to check
        
        Returns:
            Boolean indicating if the folder exists
        """
        from .file_utils import sanitize_filename
        user_folder = os.path.join(export_dir, sanitize_filename(username))
        return os.path.isdir(user_folder)
