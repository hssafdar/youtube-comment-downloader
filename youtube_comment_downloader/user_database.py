#!/usr/bin/env python
"""
User database management for YouTube Comment Downloader
Stores user information and preferences for filtering
"""

import sqlite3
import os
from pathlib import Path


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
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
            return []
