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
    
    def __init__(self):
        """Initialize the database"""
        # Store database in user's home directory
        self.db_dir = Path.home() / '.youtube_comment_downloader'
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / 'users.db'
        self._init_db()
    
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
            
            # Make request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
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
            
            # Try to find channel ID
            # Method 1: From channelId in metadata
            metadata = self._search_dict(data, 'channelId')
            for channel_id in metadata:
                if channel_id and isinstance(channel_id, str) and channel_id.startswith('UC'):
                    user_info['user_id'] = channel_id
                    break
            
            # Method 2: From externalId
            if 'user_id' not in user_info:
                external_ids = self._search_dict(data, 'externalId')
                for ext_id in external_ids:
                    if ext_id and isinstance(ext_id, str) and ext_id.startswith('UC'):
                        user_info['user_id'] = ext_id
                        break
            
            # Extract display name/title
            titles = self._search_dict(data, 'title')
            for title in titles:
                if isinstance(title, str) and title and len(title) > 0 and len(title) < 100:
                    user_info['display_name'] = title
                    break
            
            # Extract profile picture
            avatars = self._search_dict(data, 'avatar')
            for avatar in avatars:
                if isinstance(avatar, dict) and 'thumbnails' in avatar:
                    thumbnails = avatar['thumbnails']
                    if thumbnails and len(thumbnails) > 0:
                        # Get highest resolution thumbnail
                        user_info['profile_pic_url'] = thumbnails[-1].get('url', '')
                        break
            
            # Validate we have the minimum required info
            if 'user_id' not in user_info or 'display_name' not in user_info:
                return None
            
            # Set username as display name if not already set
            if 'username' not in user_info:
                user_info['username'] = user_info['display_name']
            
            user_info['channel_url'] = f"https://www.youtube.com/channel/{user_info['user_id']}"
            
            return user_info
            
        except (requests.RequestException, json.JSONDecodeError, ValueError, KeyError):
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
