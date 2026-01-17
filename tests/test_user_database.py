#!/usr/bin/env python
"""Tests for user database functionality"""

import os
import tempfile
from pathlib import Path
from youtube_comment_downloader.user_database import UserDatabase


def test_user_database_add_user():
    """Test adding a user to the database"""
    # Create a temporary database
    temp_dir = tempfile.mkdtemp()
    db = UserDatabase()
    db.db_path = Path(temp_dir) / 'test.db'
    db._init_db()
    
    try:
        # Add a user
        result = db.add_user('UC123', 'testuser', 'Test User', 
                            'http://example.com/pic.jpg',
                            'http://youtube.com/channel/UC123')
        assert result == True
        
        # Retrieve the user
        user = db.get_user('UC123')
        assert user is not None
        assert user['user_id'] == 'UC123'
        assert user['username'] == 'testuser'
        assert user['display_name'] == 'Test User'
        
    finally:
        # Cleanup
        if os.path.exists(db.db_path):
            os.unlink(db.db_path)
        os.rmdir(temp_dir)


def test_user_database_get_all_users():
    """Test retrieving all users"""
    temp_dir = tempfile.mkdtemp()
    db = UserDatabase()
    db.db_path = Path(temp_dir) / 'test.db'
    db._init_db()
    
    try:
        # Add multiple users
        db.add_user('UC123', 'user1', 'User One')
        db.add_user('UC456', 'user2', 'User Two')
        db.add_user('UC789', 'user3', 'User Three')
        
        # Get all users
        users = db.get_all_users()
        assert len(users) == 3
        assert any(u['username'] == 'user1' for u in users)
        assert any(u['username'] == 'user2' for u in users)
        assert any(u['username'] == 'user3' for u in users)
        
    finally:
        if os.path.exists(db.db_path):
            os.unlink(db.db_path)
        os.rmdir(temp_dir)


def test_user_database_delete_user():
    """Test deleting a user"""
    temp_dir = tempfile.mkdtemp()
    db = UserDatabase()
    db.db_path = Path(temp_dir) / 'test.db'
    db._init_db()
    
    try:
        # Add a user
        db.add_user('UC123', 'testuser', 'Test User')
        
        # Verify it exists
        user = db.get_user('UC123')
        assert user is not None
        
        # Delete it
        result = db.delete_user('UC123')
        assert result == True
        
        # Verify it's gone
        user = db.get_user('UC123')
        assert user is None
        
    finally:
        if os.path.exists(db.db_path):
            os.unlink(db.db_path)
        os.rmdir(temp_dir)


def test_user_database_dropdown_status():
    """Test updating dropdown visibility"""
    temp_dir = tempfile.mkdtemp()
    db = UserDatabase()
    db.db_path = Path(temp_dir) / 'test.db'
    db._init_db()
    
    try:
        # Add a user
        db.add_user('UC123', 'testuser', 'Test User')
        
        # Get dropdown users (should include this user)
        users = db.get_dropdown_users()
        assert len(users) == 1
        
        # Remove from dropdown
        db.update_dropdown_status('UC123', False)
        
        # Get dropdown users again (should be empty)
        users = db.get_dropdown_users()
        assert len(users) == 0
        
        # But user still exists
        user = db.get_user('UC123')
        assert user is not None
        
    finally:
        if os.path.exists(db.db_path):
            os.unlink(db.db_path)
        os.rmdir(temp_dir)


def test_user_database_search():
    """Test searching for users"""
    temp_dir = tempfile.mkdtemp()
    db = UserDatabase()
    db.db_path = Path(temp_dir) / 'test.db'
    db._init_db()
    
    try:
        # Add users
        db.add_user('UC123', 'alice', 'Alice Smith')
        db.add_user('UC456', 'bob', 'Bob Jones')
        db.add_user('UC789', 'charlie', 'Charlie Brown')
        
        # Search by username
        results = db.search_users('alice')
        assert len(results) == 1
        assert results[0]['username'] == 'alice'
        
        # Search by display name
        results = db.search_users('Brown')
        assert len(results) == 1
        assert results[0]['display_name'] == 'Charlie Brown'
        
        # Search with no matches
        results = db.search_users('xyz')
        assert len(results) == 0
        
    finally:
        if os.path.exists(db.db_path):
            os.unlink(db.db_path)
        os.rmdir(temp_dir)


if __name__ == '__main__':
    test_user_database_add_user()
    print("✓ test_user_database_add_user passed")
    
    test_user_database_get_all_users()
    print("✓ test_user_database_get_all_users passed")
    
    test_user_database_delete_user()
    print("✓ test_user_database_delete_user passed")
    
    test_user_database_dropdown_status()
    print("✓ test_user_database_dropdown_status passed")
    
    test_user_database_search()
    print("✓ test_user_database_search passed")
    
    print("\nAll user database tests passed! ✓")
