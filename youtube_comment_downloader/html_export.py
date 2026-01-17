#!/usr/bin/env python
"""
HTML export functionality for YouTube comments
Generates a YouTube-like interface with collapsible reply threads
"""

import html
from datetime import datetime


def generate_html_output(comments, output_path, filtered_user=None):
    """
    Generate an HTML file with YouTube-style comment display
    
    Args:
        comments: List of comment dictionaries
        output_path: Path to output HTML file
        filtered_user: Username that was filtered (for display in title)
    """
    # Build comment hierarchy
    comment_map = {c['cid']: c for c in comments}
    root_comments = []
    
    # Organize comments into threads
    for comment in comments:
        if comment.get('reply'):
            # This is a reply - find its parent
            parent_cid = comment['cid'].rsplit('.', 1)[0]
            parent = comment_map.get(parent_cid)
            if parent:
                if 'thread_replies' not in parent:
                    parent['thread_replies'] = []
                parent['thread_replies'].append(comment)
        else:
            # This is a root comment
            root_comments.append(comment)
    
    # Generate HTML (always using dark mode)
    html_content = _generate_html_template(root_comments, filtered_user)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def _generate_html_template(root_comments, filtered_user=None):
    """Generate the complete HTML document (always in dark mode)"""
    
    title = "YouTube Comments"
    if filtered_user:
        title += f" - Filtered by {filtered_user}"
    
    # Always use dark mode colors
    colors = {
        'bg_body': '#0f0f0f',
        'bg_container': '#212121',
        'text_primary': '#f1f1f1',
        'text_secondary': '#aaaaaa',
        'border': '#3f3f3f',
        'link': '#3ea6ff',
        'link_hover': '#3ea6ff',
        'button_hover_bg': 'rgba(62, 166, 255, 0.1)',
        'avatar_bg': '#3f3f3f',
        'avatar_text': '#aaaaaa',
        'shadow': 'rgba(0,0,0,0.3)',
    }
    
    header = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: "Roboto", "Arial", sans-serif;
            background-color: {colors['bg_body']};
            color: {colors['text_primary']};
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: {colors['bg_container']};
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 1px 2px {colors['shadow']};
        }}
        
        h1 {{
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid {colors['border']};
            color: {colors['text_primary']};
        }}
        
        .comment {{
            display: flex;
            margin-bottom: 16px;
            padding: 12px 0;
        }}
        
        .comment-avatar {{
            flex-shrink: 0;
            margin-right: 16px;
        }}
        
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            background-color: {colors['avatar_bg']};
        }}
        
        .comment-content {{
            flex: 1;
            min-width: 0;
        }}
        
        .comment-header {{
            display: flex;
            align-items: center;
            margin-bottom: 4px;
        }}
        
        .comment-author {{
            font-weight: 500;
            font-size: 13px;
            color: {colors['text_primary']};
            text-decoration: none;
            margin-right: 4px;
        }}
        
        .comment-author:hover {{
            color: {colors['link_hover']};
        }}
        
        .comment-time {{
            font-size: 12px;
            color: {colors['text_secondary']};
        }}
        
        .comment-text {{
            font-size: 14px;
            color: {colors['text_primary']};
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 8px 0;
            line-height: 1.8;
        }}
        
        .comment-footer {{
            display: flex;
            align-items: center;
            margin-top: 8px;
            gap: 8px;
        }}
        
        .comment-votes {{
            display: flex;
            align-items: center;
            font-size: 12px;
            color: {colors['text_secondary']};
        }}
        
        .vote-icon {{
            margin-right: 6px;
        }}
        
        .heart-icon {{
            color: #ff0000;
            margin-left: 8px;
        }}
        
        .replies-toggle {{
            display: inline-flex;
            align-items: center;
            color: {colors['link_hover']};
            background: none;
            border: none;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            padding: 8px 0;
            margin-top: 8px;
        }}
        
        .replies-toggle:hover {{
            background-color: {colors['button_hover_bg']};
            padding: 8px 12px;
            margin-left: -12px;
            border-radius: 18px;
        }}
        
        .replies-icon {{
            margin-right: 8px;
            font-size: 12px;
        }}
        
        .replies-container {{
            display: none;
            margin-top: 16px;
            padding-left: 56px;
        }}
        
        .replies-container.expanded {{
            display: block;
        }}
        
        .reply-comment {{
            margin-bottom: 16px;
        }}
        
        .no-comments {{
            text-align: center;
            padding: 48px;
            color: {colors['text_secondary']};
            font-size: 16px;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 16px;
            }}
            
            .replies-container {{
                padding-left: 40px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{html.escape(title)}</h1>
"""
    
    if not root_comments:
        header += """        <div class="no-comments">No comments available</div>
"""
    else:
        # Generate comments HTML
        comments_html = ""
        for comment in root_comments:
            comments_html += _generate_comment_html(comment)
        
        header += comments_html
    
    footer = """    </div>
    
    <script>
        function toggleReplies(commentId) {
            const container = document.getElementById('replies-' + commentId);
            const toggle = document.getElementById('toggle-' + commentId);
            
            if (container.classList.contains('expanded')) {
                container.classList.remove('expanded');
                const replyCount = container.querySelectorAll('.reply-comment').length;
                toggle.innerHTML = '<span class="replies-icon">▼</span>View ' + replyCount + ' ' + (replyCount === 1 ? 'reply' : 'replies');
            } else {
                container.classList.add('expanded');
                toggle.innerHTML = '<span class="replies-icon">▲</span>Hide replies';
            }
        }
    </script>
</body>
</html>"""
    
    return header + footer


def _generate_comment_html(comment, is_reply=False):
    """Generate HTML for a single comment and its replies"""
    
    # Escape user-generated content
    author = html.escape(comment.get('author', 'Unknown'))
    text = html.escape(comment.get('text', ''))
    time_str = html.escape(comment.get('time', ''))
    votes = html.escape(str(comment.get('votes', '0')))
    photo = html.escape(comment.get('photo', ''))
    channel = comment.get('channel', '')
    cid = html.escape(comment['cid'])
    
    # Generate avatar initial (safely escaped for SVG)
    # Use first character of unescaped author name, but ensure it's safe for SVG
    author_raw = comment.get('author', 'Unknown')
    avatar_initial = author_raw[0].upper() if author_raw else '?'
    # Only use alphanumeric characters for avatar initial to ensure SVG safety
    if not avatar_initial.isalnum():
        avatar_initial = '?'
    
    # Default avatar if photo URL is missing
    if photo:
        # Create fallback SVG data URL
        svg_fallback = (
            'data:image/svg+xml,'
            '<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>'
            '<circle cx=%2250%22 cy=%2250%22 r=%2250%22 fill=%22%23e5e5e5%22/>'
            f'<text x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 '
            f'text-anchor=%22middle%22 font-size=%2240%22 fill=%22%23606060%22>{avatar_initial}</text>'
            '</svg>'
        )
        avatar_html = f'<img src="{photo}" alt="{author}" class="avatar" onerror="this.src=\'{svg_fallback}\'">'
    else:
        # No photo provided, use div with initial
        avatar_html = (
            f'<div class="avatar" style="background-color: #e5e5e5; display: flex; '
            f'align-items: center; justify-content: center; font-size: 18px; '
            f'font-weight: 500; color: #606060;">{avatar_initial}</div>'
        )
    
    # Channel link
    channel_url = f"https://www.youtube.com/channel/{channel}" if channel else "#"
    
    # Heart indicator
    heart_html = ' <span class="heart-icon" title="Hearted by creator">❤️</span>' if comment.get('heart') else ''
    
    comment_class = "reply-comment" if is_reply else "comment"
    
    html_output = f"""        <div class="{comment_class}">
            <div class="comment-avatar">
                {avatar_html}
            </div>
            <div class="comment-content">
                <div class="comment-header">
                    <a href="{channel_url}" class="comment-author" target="_blank">{author}</a>
                    <span class="comment-time">{time_str}</span>
                </div>
                <div class="comment-text">{text}</div>
                <div class="comment-footer">
                    <div class="comment-votes">
                        <span class="vote-icon">👍</span>
                        {votes}
                    </div>
                    {heart_html}
                </div>
"""
    
    # Add replies if present
    replies = comment.get('thread_replies', [])
    if replies:
        reply_count = len(replies)
        plural = 'reply' if reply_count == 1 else 'replies'
        
        html_output += f"""                <button class="replies-toggle" id="toggle-{cid}" onclick="toggleReplies('{cid}')">
                    <span class="replies-icon">▼</span>
                    View {reply_count} {plural}
                </button>
                <div class="replies-container" id="replies-{cid}">
"""
        
        for reply in replies:
            html_output += _generate_comment_html(reply, is_reply=True)
        
        html_output += """                </div>
"""
    
    html_output += """            </div>
        </div>
"""
    
    return html_output
