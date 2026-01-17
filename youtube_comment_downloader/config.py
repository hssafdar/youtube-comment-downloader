#!/usr/bin/env python
"""
Configuration management for YouTube Comment Downloader
Handles persistent storage of user settings
"""

import json
import os
from pathlib import Path


class Config:
    """Manages application configuration and persistent settings"""
    
    DEFAULT_CONFIG = {
        'export_folder': '',
        'last_sort': 'Recent',
        'last_format': 'Dark HTML',
    }
    
    def __init__(self):
        """Initialize config with default values"""
        self.config_dir = Path.home() / '.youtube_comment_downloader'
        self.config_file = self.config_dir / 'config.json'
        self.settings = self.DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Update settings with loaded values, keeping defaults for missing keys
                    self.settings.update(loaded)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
            # If there's any error loading, just use defaults
            pass
    
    def save(self):
        """Save configuration to file"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except (PermissionError, OSError):
            # Silently fail if we can't save
            pass
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value"""
        self.settings[key] = value
        self.save()
    
    def get_export_folder(self):
        """Get the configured export folder"""
        return self.settings.get('export_folder', '')
    
    def set_export_folder(self, folder):
        """Set the export folder and save"""
        self.set('export_folder', folder)
