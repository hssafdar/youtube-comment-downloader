#!/usr/bin/env python
"""
Plain text export functionality for YouTube comments
Generates readable plain text transcripts with threading
"""


def generate_txt_output(comments, output_path, filtered_user=None):
    """
    Generate a plain text file with comments
    
    Args:
        comments: List of comment dictionaries
        output_path: Path to output TXT file
        filtered_user: Username that was filtered (for display in header)
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
    
    # Generate text content
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("=" * 80 + "\n")
        f.write("YouTube Comments\n")
        if filtered_user:
            f.write(f"Filtered by: {filtered_user}\n")
        f.write("=" * 80 + "\n\n")
        
        if not root_comments:
            f.write("No comments available.\n")
        else:
            # Write each comment thread
            for i, comment in enumerate(root_comments):
                if i > 0:
                    f.write("\n" + "-" * 80 + "\n\n")
                _write_comment(f, comment, comment_map)


def _write_comment(f, comment, comment_map, indent_level=0):
    """
    Write a single comment and its replies to the file
    
    Args:
        f: File object
        comment: Comment dictionary
        comment_map: Map of all comments by ID
        indent_level: Current indentation level
    """
    indent = "  " * indent_level
    
    # Write comment header
    author = comment.get('author', 'Unknown')
    time_str = comment.get('time', '')
    hearted = comment.get('heart', False)
    
    # Format: [Username] (timestamp):
    f.write(f"{indent}[{author}] ({time_str}):\n")
    
    # Add hearted indicator if applicable
    if hearted:
        f.write(f"{indent}[♥ Hearted by Creator]\n")
    
    # Write comment text
    text = comment.get('text', '')
    # Indent multi-line comments properly
    for line in text.split('\n'):
        f.write(f"{indent}{line}\n")
    
    # Write vote count if present
    votes = comment.get('votes', '0')
    if votes and votes != '0':
        f.write(f"{indent}👍 {votes}\n")
    
    # Write replies
    replies = comment.get('thread_replies', [])
    if replies:
        f.write("\n")
        for reply in replies:
            # Add reply indicator
            if indent_level == 0:
                f.write(f"{indent}  ↳ Reply to [{author}]:\n")
            _write_comment(f, reply, comment_map, indent_level + 1)
            f.write("\n")
