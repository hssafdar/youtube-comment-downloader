#!/usr/bin/env python
"""
YouTube Community Post downloader
Downloads post content and comments from YouTube community posts
"""

import json
import re
import time
import os
import requests

from .downloader import YoutubeCommentDownloader, YT_CFG_RE, YT_INITIAL_DATA_RE, YT_HIDDEN_INPUT_RE, YOUTUBE_CONSENT_URL

YOUTUBE_POST_URL = 'https://www.youtube.com/post/{post_id}'


class YoutubePostDownloader(YoutubeCommentDownloader):
    """Extends YoutubeCommentDownloader to support community posts"""
    
    def get_post_metadata(self, post_url):
        """
        Extract post metadata including title, author info, images, and comment count
        
        Args:
            post_url: YouTube post URL
            
        Returns:
            Dictionary with post metadata, or None if extraction fails
        """
        try:
            response = self.session.get(post_url, timeout=30)
            
            if 'consent' in str(response.url):
                params = dict(re.findall(YT_HIDDEN_INPUT_RE, response.text))
                params.update({'continue': post_url, 'set_eom': False, 'set_ytc': True, 'set_apyt': True})
                response = self.session.post(YOUTUBE_CONSENT_URL, params=params)
            
            html = response.text
            data = json.loads(self.regex_search(html, YT_INITIAL_DATA_RE, default='{}'))
            
            metadata = {}
            
            # Extract post content from backstagePostRenderer
            post_renderer = next(self.search_dict(data, 'backstagePostRenderer'), None)
            if post_renderer:
                # Post text/content
                content_text = post_renderer.get('backstagePostThreadRenderer', {}).get('post', {}).get('backstagePostRenderer', {})
                if not content_text:
                    content_text = post_renderer
                
                # Extract text from contentText
                text_runs = content_text.get('contentText', {}).get('runs', [])
                if text_runs:
                    post_text = ''.join([run.get('text', '') for run in text_runs])
                    metadata['content'] = post_text
                    # Use first 100 chars as title
                    metadata['title'] = post_text[:100] if post_text else 'Community Post'
                else:
                    metadata['content'] = ''
                    metadata['title'] = 'Community Post'
                
                # Extract author info
                author_text = content_text.get('authorText', {}).get('runs', [])
                if author_text:
                    metadata['channel_name'] = author_text[0].get('text', '')
                
                # Extract channel ID from endpoint
                author_endpoint = content_text.get('authorEndpoint', {}).get('browseEndpoint', {})
                if author_endpoint:
                    metadata['channel_id'] = author_endpoint.get('browseId', '')
                
                # Extract author thumbnail
                author_thumbs = content_text.get('authorThumbnail', {}).get('thumbnails', [])
                if author_thumbs:
                    metadata['channel_thumbnail'] = author_thumbs[-1].get('url', '')
                
                # Extract attached images
                attachment = content_text.get('backstageAttachment', {})
                if 'backstageImageRenderer' in attachment:
                    image_data = attachment['backstageImageRenderer']
                    images = []
                    thumbs = image_data.get('image', {}).get('thumbnails', [])
                    if thumbs:
                        # Get highest quality image
                        images.append(thumbs[-1].get('url', ''))
                    metadata['images'] = images
                else:
                    metadata['images'] = []
            
            # Extract post ID from URL
            post_id_match = re.search(r'/post/([A-Za-z0-9_-]+)', post_url)
            if post_id_match:
                metadata['post_id'] = post_id_match.group(1)
            
            return metadata if metadata else None
            
        except (json.JSONDecodeError, requests.RequestException) as e:
            return None
    
    def get_post_comments(self, post_id, sort_by=1, language=None):
        """
        Get comments for a community post
        
        Args:
            post_id: YouTube post ID
            sort_by: Sort order (0=popular, 1=recent)
            language: Language code (optional)
            
        Yields:
            Comment dictionaries
        """
        # Community posts are accessed via the post URL
        post_url = YOUTUBE_POST_URL.format(post_id=post_id)
        
        # Get the initial page
        response = self.session.get(post_url, timeout=30)
        
        if 'consent' in str(response.url):
            params = dict(re.findall(YT_HIDDEN_INPUT_RE, response.text))
            params.update({'continue': post_url, 'set_eom': False, 'set_ytc': True, 'set_apyt': True})
            response = self.session.post(YOUTUBE_CONSENT_URL, params=params)
        
        html = response.text
        ytcfg = json.loads(self.regex_search(html, YT_CFG_RE, default='{}'))
        if not ytcfg:
            return
        
        data = json.loads(self.regex_search(html, YT_INITIAL_DATA_RE, default='{}'))
        
        # Find the comments section continuation
        # Community posts use similar structure to videos for comments
        section_contents = next(self.search_dict(data, 'itemSectionRenderer'), {})
        renderer = next(self.search_dict(section_contents, 'continuationItemRenderer'), {})
        
        if not renderer:
            # Try alternative path
            for section in self.search_dict(data, 'itemSectionRenderer'):
                if section.get('sectionIdentifier') == 'comment-item-section':
                    contents = section.get('contents', [])
                    if contents:
                        renderer = contents[0].get('continuationItemRenderer', {})
                        break
        
        if not renderer:
            return
        
        # Start yielding comments using the same mechanism as videos
        needs_sorting = sort_by != 1  # Recent is default
        
        for comment in self.get_comments_from_continuation(renderer, ytcfg, needs_sorting):
            yield comment
    
    def get_comments_from_continuation(self, renderer, ytcfg, needs_sorting):
        """
        Get comments from a continuation endpoint (same as video comments)
        
        Args:
            renderer: Initial continuation renderer
            ytcfg: YouTube config
            needs_sorting: Whether to apply sorting
            
        Yields:
            Comment dictionaries
        """
        continuation_endpoint = renderer.get('continuationEndpoint') or renderer.get('button', {}).get('buttonRenderer', {}).get('command')
        
        if not continuation_endpoint:
            return
        
        # Use the same comment parsing logic as the parent class
        for comment in self._get_comments_from_endpoint(continuation_endpoint, ytcfg):
            yield comment
    
    def _get_comments_from_endpoint(self, endpoint, ytcfg):
        """Internal method to get comments from an endpoint"""
        response = self.ajax_request(endpoint, ytcfg)
        
        if not response:
            return
        
        # Process the response to extract comments
        actions = list(self.search_dict(response, 'reloadContinuationItemsCommand')) + \
                 list(self.search_dict(response, 'appendContinuationItemsAction'))
        
        for action in actions:
            for item in action.get('continuationItems', []):
                # Check for comment thread
                if 'commentThreadRenderer' in item:
                    comment = self._parse_comment(item['commentThreadRenderer'])
                    if comment:
                        yield comment
                
                # Check for continuation
                elif 'continuationItemRenderer' in item:
                    continuation = item['continuationItemRenderer']
                    for comment in self._get_comments_from_endpoint(
                        continuation.get('continuationEndpoint') or 
                        continuation.get('button', {}).get('buttonRenderer', {}).get('command'),
                        ytcfg
                    ):
                        yield comment
    
    def _parse_comment(self, thread_renderer):
        """Parse a comment from a thread renderer (reuses parent class method if available)"""
        comment_renderer = thread_renderer.get('comment', {}).get('commentRenderer', {})
        
        if not comment_renderer:
            return None
        
        # Extract comment data
        comment = {}
        
        # Author
        author_text = comment_renderer.get('authorText', {})
        if isinstance(author_text, dict):
            comment['author'] = author_text.get('simpleText', '')
        else:
            comment['author'] = str(author_text) if author_text else 'Unknown'
        
        # Text
        text_runs = comment_renderer.get('contentText', {}).get('runs', [])
        comment['text'] = ''.join([run.get('text', '') for run in text_runs]) if text_runs else ''
        
        # Votes
        vote_count = comment_renderer.get('voteCount', {})
        if isinstance(vote_count, dict):
            comment['votes'] = vote_count.get('simpleText', '0')
        else:
            comment['votes'] = str(vote_count) if vote_count else '0'
        
        # Time
        time_text = comment_renderer.get('publishedTimeText', {})
        if isinstance(time_text, dict):
            comment['time'] = time_text.get('simpleText', '')
        else:
            comment['time'] = str(time_text) if time_text else ''
        
        # Comment ID
        comment['cid'] = comment_renderer.get('commentId', '')
        
        # Author thumbnail
        author_thumb = comment_renderer.get('authorThumbnail', {}).get('thumbnails', [])
        if author_thumb:
            comment['photo'] = author_thumb[-1].get('url', '')
        else:
            comment['photo'] = ''
        
        # Channel ID
        comment['channel'] = comment_renderer.get('authorEndpoint', {}).get('browseEndpoint', {}).get('browseId', '')
        
        # Heart
        comment['heart'] = bool(comment_renderer.get('creatorHeart'))
        
        # Reply flag
        comment['reply'] = False
        
        return comment
    
    def download_post_images(self, images, output_folder):
        """
        Download post images to assets folder
        
        Args:
            images: List of image URLs
            output_folder: Base output folder (posts/)
            
        Returns:
            List of local image paths
        """
        if not images:
            return []
        
        assets_folder = os.path.join(output_folder, 'assets')
        os.makedirs(assets_folder, exist_ok=True)
        
        local_paths = []
        for i, img_url in enumerate(images):
            try:
                response = requests.get(img_url, timeout=30)
                response.raise_for_status()
                
                # Determine file extension from URL or content-type
                ext = '.jpg'
                if 'content-type' in response.headers:
                    content_type = response.headers['content-type']
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'webp' in content_type:
                        ext = '.webp'
                
                filename = f'post_image_{i+1}{ext}'
                filepath = os.path.join(assets_folder, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                local_paths.append(filepath)
            except Exception:
                # Skip failed images
                continue
        
        return local_paths
