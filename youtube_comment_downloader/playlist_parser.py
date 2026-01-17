#!/usr/bin/env python
"""
YouTube Playlist Parser
Extracts video IDs from YouTube playlists
"""

import re
import json
import requests

from .downloader import YT_INITIAL_DATA_RE, YT_HIDDEN_INPUT_RE, YOUTUBE_CONSENT_URL, USER_AGENT


class PlaylistParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = USER_AGENT
        self.session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
    
    def extract_playlist_id(self, url):
        """Extract playlist ID from URL"""
        # Match ?list=PLxxxxx or &list=PLxxxxx
        match = re.search(r'[?&]list=([A-Za-z0-9_-]+)', url)
        return match.group(1) if match else None
    
    def is_playlist_url(self, url):
        """Check if URL contains a playlist"""
        return 'list=' in url
    
    def get_playlist_videos(self, playlist_id):
        """
        Get all video IDs and titles from a playlist
        
        Returns:
            List of dicts with 'video_id', 'title', 'url'
        """
        url = f'https://www.youtube.com/playlist?list={playlist_id}'
        
        response = self.session.get(url, timeout=30)
        
        if 'consent' in str(response.url):
            params = dict(re.findall(YT_HIDDEN_INPUT_RE, response.text))
            params.update({'continue': url, 'set_eom': False, 'set_ytc': True, 'set_apyt': True})
            response = self.session.post(YOUTUBE_CONSENT_URL, params=params)
        
        html = response.text
        
        # Extract ytInitialData
        match = re.search(YT_INITIAL_DATA_RE, html)
        if not match:
            return []
        
        data = json.loads(match.group(1))
        
        videos = []
        
        # Find playlistVideoListRenderer
        for renderer in self._search_dict(data, 'playlistVideoRenderer'):
            video_id = renderer.get('videoId')
            title_runs = renderer.get('title', {}).get('runs', [])
            title = title_runs[0].get('text', '') if title_runs else 'Unknown'
            
            if video_id:
                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                })
        
        return videos
    
    def _search_dict(self, partial, search_key):
        """Recursively search for key in nested dict"""
        stack = [partial]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key == search_key:
                        yield value
                    else:
                        stack.append(value)
            elif isinstance(current, list):
                stack.extend(current)
