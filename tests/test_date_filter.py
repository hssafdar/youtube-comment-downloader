#!/usr/bin/env python
"""Tests for date filtering functionality"""

from datetime import datetime, timedelta
from youtube_comment_downloader.date_filter import DateFilter


def test_date_filter_all_comments():
    """Test that 'all' preset returns all comments"""
    filter = DateFilter(preset='all')
    
    comments = [
        {'text': 'Comment 1', 'time': '1 day ago'},
        {'text': 'Comment 2', 'time': '1 week ago'},
        {'text': 'Comment 3', 'time': '1 month ago'},
    ]
    
    filtered = filter.filter_comments(comments)
    assert len(filtered) == 3


def test_date_filter_day_preset():
    """Test that 'day' preset filters correctly"""
    filter = DateFilter(preset='day')
    
    comments = [
        {'text': 'Comment 1', 'time': '1 hour ago'},
        {'text': 'Comment 2', 'time': '12 hours ago'},
        {'text': 'Comment 3', 'time': '2 days ago'},
        {'text': 'Comment 4', 'time': '1 week ago'},
    ]
    
    filtered = filter.filter_comments(comments)
    # Should include comments from past day only (1 hour, 12 hours)
    assert len(filtered) == 2
    assert filtered[0]['text'] == 'Comment 1'
    assert filtered[1]['text'] == 'Comment 2'


def test_date_filter_week_preset():
    """Test that 'week' preset filters correctly"""
    filter = DateFilter(preset='week')
    
    comments = [
        {'text': 'Comment 1', 'time': '1 day ago'},
        {'text': 'Comment 2', 'time': '5 days ago'},
        {'text': 'Comment 3', 'time': '2 weeks ago'},
        {'text': 'Comment 4', 'time': '1 month ago'},
    ]
    
    filtered = filter.filter_comments(comments)
    # Should include comments from past week only
    assert len(filtered) == 2
    assert filtered[0]['text'] == 'Comment 1'
    assert filtered[1]['text'] == 'Comment 2'


def test_date_filter_custom_range():
    """Test custom date range filtering"""
    after_date = datetime(2024, 1, 1)
    before_date = datetime(2024, 12, 31)
    
    filter = DateFilter(preset='custom', after_date=after_date, before_date=before_date)
    
    comments = [
        {'text': 'Comment 1', 'time': '2024-06-15'},  # In range
        {'text': 'Comment 2', 'time': '2023-12-01'},  # Before range
        {'text': 'Comment 3', 'time': '2025-01-01'},  # After range
        {'text': 'Comment 4', 'time': '2024-03-20'},  # In range
    ]
    
    filtered = filter.filter_comments(comments)
    # Should only include comments in 2024
    assert len(filtered) == 2


def test_date_filter_excludes_unparseable():
    """Test that unparseable dates are excluded when filtering is active"""
    filter = DateFilter(preset='week')
    
    comments = [
        {'text': 'Comment 1', 'time': '1 day ago'},
        {'text': 'Comment 2', 'time': 'invalid date'},
        {'text': 'Comment 3', 'time': ''},
        {'text': 'Comment 4', 'time': '3 days ago'},
    ]
    
    filtered = filter.filter_comments(comments)
    # Should only include parseable dates within range
    assert len(filtered) == 2
    assert filtered[0]['text'] == 'Comment 1'
    assert filtered[1]['text'] == 'Comment 4'


def test_date_filter_serialization():
    """Test DateFilter to/from dict conversion"""
    after_date = datetime(2024, 1, 1)
    before_date = datetime(2024, 12, 31)
    
    filter = DateFilter(preset='custom', after_date=after_date, before_date=before_date)
    
    # Convert to dict
    data = filter.to_dict()
    assert data['preset'] == 'custom'
    assert data['after_date'] == '2024-01-01T00:00:00'
    assert data['before_date'] == '2024-12-31T00:00:00'
    
    # Convert back from dict
    restored_filter = DateFilter.from_dict(data)
    assert restored_filter.preset == 'custom'
    assert restored_filter.after_date == after_date
    assert restored_filter.before_date == before_date


def test_date_filter_get_date_range():
    """Test getting date range from preset"""
    # Test 'all' preset
    filter = DateFilter(preset='all')
    after, before = filter.get_date_range()
    assert after is None
    assert before is None
    
    # Test 'day' preset
    filter = DateFilter(preset='day')
    after, before = filter.get_date_range()
    assert after is not None
    assert before is None
    # Should be approximately 1 day ago
    assert datetime.now() - after < timedelta(days=1, seconds=10)
    
    # Test 'custom' preset
    custom_after = datetime(2024, 1, 1)
    custom_before = datetime(2024, 12, 31)
    filter = DateFilter(preset='custom', after_date=custom_after, before_date=custom_before)
    after, before = filter.get_date_range()
    assert after == custom_after
    assert before == custom_before


if __name__ == '__main__':
    test_date_filter_all_comments()
    print("✓ test_date_filter_all_comments passed")
    
    test_date_filter_day_preset()
    print("✓ test_date_filter_day_preset passed")
    
    test_date_filter_week_preset()
    print("✓ test_date_filter_week_preset passed")
    
    test_date_filter_custom_range()
    print("✓ test_date_filter_custom_range passed")
    
    test_date_filter_excludes_unparseable()
    print("✓ test_date_filter_excludes_unparseable passed")
    
    test_date_filter_serialization()
    print("✓ test_date_filter_serialization passed")
    
    test_date_filter_get_date_range()
    print("✓ test_date_filter_get_date_range passed")
    
    print("\nAll date filter tests passed! ✓")
