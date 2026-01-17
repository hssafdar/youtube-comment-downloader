#!/usr/bin/env python
"""
Date filtering for YouTube comments
"""

from datetime import datetime, timedelta
import dateparser


class DateFilter:
    """Handles date range filtering for comments"""
    
    PRESETS = {
        'all': None,
        'day': timedelta(days=1),
        'week': timedelta(weeks=1),
        'month': timedelta(days=30),
        'year': timedelta(days=365),
    }
    
    def __init__(self, preset='all', after_date=None, before_date=None):
        self.preset = preset
        self.after_date = after_date
        self.before_date = before_date
    
    def get_date_range(self):
        """Get after and before dates based on preset or custom range"""
        if self.preset == 'custom':
            return self.after_date, self.before_date
        
        if self.preset == 'all' or self.preset not in self.PRESETS:
            return None, None
        
        delta = self.PRESETS[self.preset]
        after = datetime.now() - delta
        return after, None
    
    def filter_comments(self, comments):
        """Filter comments by date range"""
        after_date, before_date = self.get_date_range()
        
        if after_date is None and before_date is None:
            return comments
        
        filtered = []
        for comment in comments:
            time_text = comment.get('time', '')
            
            # Parse relative time like "2 weeks ago"
            parsed_date = dateparser.parse(time_text)
            
            # Only include comments with parseable dates when filtering is active
            if parsed_date:
                if after_date and parsed_date < after_date:
                    continue
                if before_date and parsed_date > before_date:
                    continue
                filtered.append(comment)
        
        return filtered
    
    def to_dict(self):
        """Serialize for saving"""
        return {
            'preset': self.preset,
            'after_date': self.after_date.isoformat() if self.after_date else None,
            'before_date': self.before_date.isoformat() if self.before_date else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize from saved state"""
        after = datetime.fromisoformat(data['after_date']) if data.get('after_date') else None
        before = datetime.fromisoformat(data['before_date']) if data.get('before_date') else None
        return cls(data.get('preset', 'all'), after, before)
