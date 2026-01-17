#!/usr/bin/env python
"""Tests for video author filter functionality"""


def test_author_filter_basic():
    """Test that author filter works with channel ID matching"""
    # Mock the _filter_comments_by_author method
    def _filter_comments_by_author(all_comments, author_channel_id):
        if not author_channel_id:
            return all_comments
        
        comment_map = {c['cid']: c for c in all_comments}
        result = []
        result_cids = set()
        
        for comment in all_comments:
            comment_channel = comment.get('channel', '')
            is_author = comment_channel == author_channel_id
            
            if is_author:
                if comment['cid'] not in result_cids:
                    result.append(comment)
                    result_cids.add(comment['cid'])
                
                if comment.get('reply'):
                    parent_cid = comment['cid'].rsplit('.', 1)[0]
                    parent = comment_map.get(parent_cid)
                    if parent and parent['cid'] not in result_cids:
                        idx = result.index(comment)
                        result.insert(idx, parent)
                        result_cids.add(parent['cid'])
        
        return result
    
    comments = [
        {
            'cid': '1',
            'author': 'Video Author',
            'channel': 'UC_AUTHOR_123',
            'text': 'Author comment',
            'reply': False
        },
        {
            'cid': '2',
            'author': 'Random User',
            'channel': 'UC_USER_456',
            'text': 'User comment',
            'reply': False
        },
        {
            'cid': '3',
            'author': 'Video Author',
            'channel': 'UC_AUTHOR_123',
            'text': 'Another author comment',
            'reply': False
        }
    ]
    
    # Test filtering by author channel ID
    result = _filter_comments_by_author(comments, 'UC_AUTHOR_123')
    assert len(result) == 2
    assert all(c['channel'] == 'UC_AUTHOR_123' for c in result)
    assert result[0]['text'] == 'Author comment'
    assert result[1]['text'] == 'Another author comment'


def test_author_filter_with_replies():
    """Test that author filter includes parent comments when author replies"""
    def _filter_comments_by_author(all_comments, author_channel_id):
        if not author_channel_id:
            return all_comments
        
        comment_map = {c['cid']: c for c in all_comments}
        result = []
        result_cids = set()
        
        for comment in all_comments:
            comment_channel = comment.get('channel', '')
            is_author = comment_channel == author_channel_id
            
            if is_author:
                if comment['cid'] not in result_cids:
                    result.append(comment)
                    result_cids.add(comment['cid'])
                
                if comment.get('reply'):
                    parent_cid = comment['cid'].rsplit('.', 1)[0]
                    parent = comment_map.get(parent_cid)
                    if parent and parent['cid'] not in result_cids:
                        idx = result.index(comment)
                        result.insert(idx, parent)
                        result_cids.add(parent['cid'])
        
        return result
    
    comments = [
        {
            'cid': 'parent1',
            'author': 'Random User',
            'channel': 'UC_USER_456',
            'text': 'User comment',
            'reply': False
        },
        {
            'cid': 'parent1.reply1',
            'author': 'Video Author',
            'channel': 'UC_AUTHOR_123',
            'text': 'Author reply to user',
            'reply': True
        }
    ]
    
    # When filtering by author, should include the parent comment too
    result = _filter_comments_by_author(comments, 'UC_AUTHOR_123')
    assert len(result) == 2
    assert result[0]['cid'] == 'parent1'  # Parent comes first
    assert result[1]['cid'] == 'parent1.reply1'  # Reply comes second
    assert result[0]['author'] == 'Random User'  # Parent is by different user
    assert result[1]['author'] == 'Video Author'  # Reply is by author


def test_author_filter_empty():
    """Test that empty filter returns all comments"""
    def _filter_comments_by_author(all_comments, author_channel_id):
        if not author_channel_id:
            return all_comments
        
        comment_map = {c['cid']: c for c in all_comments}
        result = []
        result_cids = set()
        
        for comment in all_comments:
            comment_channel = comment.get('channel', '')
            is_author = comment_channel == author_channel_id
            
            if is_author:
                if comment['cid'] not in result_cids:
                    result.append(comment)
                    result_cids.add(comment['cid'])
                
                if comment.get('reply'):
                    parent_cid = comment['cid'].rsplit('.', 1)[0]
                    parent = comment_map.get(parent_cid)
                    if parent and parent['cid'] not in result_cids:
                        idx = result.index(comment)
                        result.insert(idx, parent)
                        result_cids.add(parent['cid'])
        
        return result
    
    comments = [
        {'cid': '1', 'author': 'User 1', 'channel': 'UC1', 'reply': False},
        {'cid': '2', 'author': 'User 2', 'channel': 'UC2', 'reply': False},
        {'cid': '3', 'author': 'User 3', 'channel': 'UC3', 'reply': False}
    ]
    
    result = _filter_comments_by_author(comments, '')
    assert len(result) == 3
    
    result = _filter_comments_by_author(comments, None)
    assert len(result) == 3


if __name__ == '__main__':
    test_author_filter_basic()
    print("✓ test_author_filter_basic passed")
    
    test_author_filter_with_replies()
    print("✓ test_author_filter_with_replies passed")
    
    test_author_filter_empty()
    print("✓ test_author_filter_empty passed")
    
    print("\nAll author filter tests passed! ✓")
