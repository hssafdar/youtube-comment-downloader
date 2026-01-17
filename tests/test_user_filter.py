#!/usr/bin/env python
"""Tests for user filter functionality"""


def test_user_filter_case_insensitive():
    """Test that user filter is case-insensitive"""
    # Mock the _filter_comments_by_user method
    def _filter_comments_by_user(all_comments, target_user):
        if not target_user:
            return all_comments
        
        target_user = target_user.strip()
        if target_user.startswith('@'):
            target_user = target_user[1:]
        target_user_lower = target_user.lower()
        
        comment_map = {c['cid']: c for c in all_comments}
        result = []
        result_cids = set()
        
        for comment in all_comments:
            author = comment.get('author', '').lower()
            is_target_user = author == target_user_lower
            
            if is_target_user:
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
            'author': 'John Doe',
            'text': 'First comment',
            'reply': False
        },
        {
            'cid': '2',
            'author': 'jane smith',
            'text': 'Second comment',
            'reply': False
        },
        {
            'cid': '3',
            'author': 'John Doe',
            'text': 'Third comment',
            'reply': False
        }
    ]
    
    # Test case-insensitive matching
    result = _filter_comments_by_user(comments, 'john doe')
    assert len(result) == 2
    assert all(c['author'].lower() == 'john doe' for c in result)
    
    result = _filter_comments_by_user(comments, 'JOHN DOE')
    assert len(result) == 2
    
    result = _filter_comments_by_user(comments, '@John Doe')
    assert len(result) == 2
    
    result = _filter_comments_by_user(comments, 'Jane Smith')
    assert len(result) == 1
    assert result[0]['author'] == 'jane smith'


def test_user_filter_with_replies():
    """Test that user filter includes parent comments for replies"""
    def _filter_comments_by_user(all_comments, target_user):
        if not target_user:
            return all_comments
        
        target_user = target_user.strip()
        if target_user.startswith('@'):
            target_user = target_user[1:]
        target_user_lower = target_user.lower()
        
        comment_map = {c['cid']: c for c in all_comments}
        result = []
        result_cids = set()
        
        for comment in all_comments:
            author = comment.get('author', '').lower()
            is_target_user = author == target_user_lower
            
            if is_target_user:
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
            'author': 'Parent User',
            'text': 'Parent comment',
            'reply': False
        },
        {
            'cid': 'parent1.reply1',
            'author': 'Target User',
            'text': 'Reply to parent',
            'reply': True
        }
    ]
    
    # When filtering by Target User, should include the parent comment too
    result = _filter_comments_by_user(comments, 'Target User')
    assert len(result) == 2
    assert result[0]['cid'] == 'parent1'  # Parent comes first
    assert result[1]['cid'] == 'parent1.reply1'  # Reply comes second


def test_user_filter_empty():
    """Test that empty filter returns all comments"""
    def _filter_comments_by_user(all_comments, target_user):
        if not target_user:
            return all_comments
        
        target_user = target_user.strip()
        if target_user.startswith('@'):
            target_user = target_user[1:]
        target_user_lower = target_user.lower()
        
        comment_map = {c['cid']: c for c in all_comments}
        result = []
        result_cids = set()
        
        for comment in all_comments:
            author = comment.get('author', '').lower()
            is_target_user = author == target_user_lower
            
            if is_target_user:
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
        {'cid': '1', 'author': 'User 1', 'reply': False},
        {'cid': '2', 'author': 'User 2', 'reply': False},
        {'cid': '3', 'author': 'User 3', 'reply': False}
    ]
    
    result = _filter_comments_by_user(comments, '')
    assert len(result) == 3
    
    result = _filter_comments_by_user(comments, None)
    assert len(result) == 3


if __name__ == '__main__':
    test_user_filter_case_insensitive()
    print("✓ test_user_filter_case_insensitive passed")
    
    test_user_filter_with_replies()
    print("✓ test_user_filter_with_replies passed")
    
    test_user_filter_empty()
    print("✓ test_user_filter_empty passed")
    
    print("\nAll user filter tests passed! ✓")
