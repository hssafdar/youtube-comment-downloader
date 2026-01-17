# Queue System and New Features Guide

## Overview

The YouTube Comment Downloader now includes a powerful queue system for batch downloading comments from multiple videos and playlists. This guide covers all the new features added.

## New Features

### 1. Queue System

The application now supports batch downloading with a queue interface:

- **Add videos to queue** instead of downloading immediately
- **Process multiple videos** sequentially
- **Track status** of each video in the queue
- **Pause and resume** downloads
- **Save queue state** between sessions

#### Queue Status Icons

- 📋 **Pending** - Waiting to be processed
- ⏳ **Downloading** - Currently downloading
- ✅ **Complete** - Successfully downloaded
- ⏭️ **Skipped** - Already exists in export folder
- ❌ **Error** - Failed with error message
- ⏸️ **Paused** - Paused by user

#### Queue Controls

- **Add to Queue** - Add current URL to queue without starting download
- **Start Queue** - Begin processing all pending items
- **Pause** - Pause after current video completes
- **Stop** - Stop immediately and save progress
- **Clear Queue** - Remove all items (with confirmation)
- **Download (Single)** - Immediate single-video download (backward compatible)

### 2. Playlist Support

The downloader now automatically detects and handles YouTube playlists:

- **Playlist URLs** - `youtube.com/playlist?list=PLxxxxx`
- **Video URLs with playlist** - `watch?v=xxx&list=PLxxxxx`

When you add a playlist URL:
1. All videos in the playlist are extracted
2. Each video is added to the queue individually
3. Videos are processed one by one
4. Duplicates are automatically skipped

### 3. Date Range Filtering

Filter comments by when they were posted:

#### Quick Presets
- **All Comments** - No filtering (default)
- **Past 24 Hours** - Only comments from last day
- **Past Week** - Only comments from last 7 days
- **Past Month** - Only comments from last 30 days
- **Past Year** - Only comments from last 365 days
- **Custom Range...** - Specify exact date range

#### Custom Date Range
When selecting "Custom Range...":
1. Enter start date (YYYY-MM-DD format) or leave blank
2. Enter end date (YYYY-MM-DD format) or leave blank
3. Click Apply to filter
4. Comments outside the range are excluded from export

**Note:** Comments with unparseable dates are excluded when date filtering is active.

### 4. Skip Already Downloaded

The queue system automatically detects and skips videos that have already been downloaded:

- Checks export folder before downloading each video
- Matches by video ID (11-character YouTube ID)
- Marks as "Skipped" in queue
- Moves to next video automatically
- Prevents duplicate downloads

**How it works:**
- Scans the export folder for files containing the video ID
- Looks for patterns like: `_videoID_`, `videoID_`, or `_videoID.`
- Only exact 11-character matches are considered

### 5. Queue State Persistence

Your queue is automatically saved and can be resumed:

#### Auto-Save
Queue state is saved automatically:
- After each video completes
- When you pause the queue
- When you stop the queue
- When you close the application

#### Resume on Startup
When you launch the application:
- If a saved queue with pending/paused items exists
- A dialog appears: "Resume previous queue?"
- Click **Yes** to resume where you left off
- Click **No** to clear the saved queue

#### State File Location
Queue state is saved to:
- **Linux/Mac:** `~/.youtube_comment_downloader/queue_state.json`
- **Windows:** `%USERPROFILE%\.youtube_comment_downloader\queue_state.json`

## Usage Examples

### Example 1: Download Single Video (Original Behavior)

1. Enter video URL
2. Configure settings (format, filter, etc.)
3. Click **Download (Single)**
4. Wait for completion

### Example 2: Download Multiple Videos

1. Enter first video URL
2. Click **Add to Queue**
3. Enter second video URL
4. Click **Add to Queue**
5. Repeat for all videos
6. Click **Start Queue**
7. Videos download sequentially

### Example 3: Download Entire Playlist

1. Copy playlist URL from YouTube
2. Paste into URL field
3. Click **Add to Queue**
4. All videos are added to queue automatically
5. Click **Start Queue**
6. Playlist downloads video by video

### Example 4: Filter Recent Comments

1. Set Date Range to "Past Week"
2. Add videos to queue or download single
3. Only comments from last 7 days will be included

### Example 5: Resume Interrupted Downloads

1. Start processing a queue
2. Close application mid-download
3. Relaunch application
4. Click **Yes** when prompted to resume
5. Queue continues from where it stopped

## Backward Compatibility

All existing features continue to work:

- **Single-video downloads** - Use "Download (Single)" button
- **Sort options** - Popular or Recent
- **Language filtering** - Specify language code
- **Comment limit** - Set maximum comments
- **Export formats** - Dark HTML, JSON, PDF
- **Include Raw TXT** - Additional text export
- **User filtering** - Filter by specific user
- **User database** - Manage favorite creators

## Tips and Best Practices

1. **Use queue for multiple videos** - More efficient than individual downloads
2. **Enable skip detection** - Prevents wasting time on duplicates
3. **Save queue state** - Don't lose progress on accidental close
4. **Use date filters** - Get only relevant recent comments
5. **Check queue status** - Watch for errors or skipped items
6. **Pause for adjustments** - Pause queue to change settings
7. **Clear completed items** - Keep queue organized

## Troubleshooting

### Queue not starting
- Check that items have "Pending" status
- Ensure export folder is valid
- Verify internet connection

### Videos marked as "Skipped"
- Files with same video ID already exist
- Check export folder for existing downloads
- Clear queue and re-add to force re-download (use single download mode)

### Date filter not working
- Verify date format is YYYY-MM-DD
- Check that comments have parseable timestamps
- Comments without dates are excluded when filtering

### Queue state not saving
- Check write permissions in home directory
- Verify `.youtube_comment_downloader` folder exists
- Look for `queue_state.json` file

## Technical Details

### Dependencies

New optional dependency:
- `dateparser` - For parsing relative time strings

Install with:
```bash
pip install dateparser
```

### File Structure

Queue state is saved as JSON:
```json
{
  "queue": [
    {
      "video_id": "dQw4w9WgXcQ",
      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "title": "Video Title",
      "status": "complete",
      "comments_downloaded": 1523,
      "total_comments": 1523
    }
  ],
  "settings": {
    "export_folder": "/path/to/exports",
    "format": "Dark HTML"
  },
  "last_updated": "2026-01-17T12:00:00"
}
```

### Thread Safety

- Queue operations are thread-safe
- State saves are atomic
- Download thread properly manages queue updates

## Support

For issues or questions:
- Check existing GitHub issues
- Create new issue with details
- Include queue state file if relevant

## Version Information

Queue system added in version 0.2
- Playlist support
- Date range filtering
- Skip detection
- State persistence
