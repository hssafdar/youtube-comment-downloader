#!/usr/bin/env python
"""
JSON export functionality for YouTube comments
Generates structured JSON output with threading
"""

import json


def generate_json_output(comments, output_path, filtered_user=None):
    """
    Generate a JSON file with comments
    
    Args:
        comments: List of comment dictionaries
        output_path: Path to output JSON file
        filtered_user: Username that was filtered (for metadata)
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
    
    # Build output structure
    output_data = {
        'metadata': {
            'total_comments': len(comments),
            'root_comments': len(root_comments),
        },
        'comments': root_comments
    }
    
    if filtered_user:
        output_data['metadata']['filtered_by'] = filtered_user
    
    # Write JSON with proper formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
