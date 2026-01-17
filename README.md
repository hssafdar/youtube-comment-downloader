# youtube-comment-downloader
Simple script for downloading Youtube comments without using the Youtube API. The output is in line delimited JSON.

### Installation

Preferably inside a [python virtual environment](https://virtualenv.pypa.io/en/latest/) install this package via:

```
pip install youtube-comment-downloader
```

Or directly from the GitHub repository:

```
pip install https://github.com/egbertbouman/youtube-comment-downloader/archive/master.zip
```

#### Optional Dependencies

For enhanced functionality, you can install optional packages:

```bash
# For PDF export support
pip install reportlab

# For macOS: Fix app name in dock (shows "YouTube Comment Downloader" instead of "Python")
pip install pyobjc-framework-Cocoa

# Or install all optional dependencies at once
pip install -r requirements-optional.txt
```

### Usage as command-line interface
```
$ youtube-comment-downloader --help
usage: youtube-comment-downloader [--help] [--youtubeid YOUTUBEID] [--url URL] [--output OUTPUT] [--limit LIMIT] [--language LANGUAGE] [--sort SORT]

Download Youtube comments without using the Youtube API

optional arguments:
  --help, -h                             Show this help message and exit
  --youtubeid YOUTUBEID, -y YOUTUBEID    ID of Youtube video for which to download the comments
  --url URL, -u URL                      Youtube URL for which to download the comments
  --output OUTPUT, -o OUTPUT             Output filename (output format is line delimited JSON)
  --pretty, -p                           Change the output format to indented JSON
  --limit LIMIT, -l LIMIT                Limit the number of comments
  --language LANGUAGE, -a LANGUAGE       Language for Youtube generated text (e.g. en)
  --sort SORT, -s SORT                   Whether to download popular (0) or recent comments (1). Defaults to 1
```

For example:
```
youtube-comment-downloader --url https://www.youtube.com/watch?v=ScMzIvxBSi4 --output ScMzIvxBSi4.json
```
or using the Youtube ID:
```
youtube-comment-downloader --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.json
```

For Youtube IDs starting with - (dash) you will need to run the script with:
`-y=idwithdash` or `--youtubeid=idwithdash`


### GUI Usage

A graphical user interface (GUI) is available for users who prefer not to use the command line.

After installation, you can launch the GUI using:

```
python -m youtube_comment_downloader.gui
```

Or if you installed via pip, you can use the shortcut command:

```
youtube-comment-downloader-gui
```

The GUI provides an easy-to-use interface with the following features:

#### Core Features
- Input fields for YouTube URL or video ID
- **Default limit of 1,000 comments** (can be changed or cleared for unlimited)
- Sort options (Popular or Recent)
- Optional language setting
- **Progress bar** with real-time percentage and comment count updates

#### Export Formats
Choose from three export formats:
- **Dark HTML** - Generate a YouTube-style HTML interface with:
  - Clean, modern dark mode styling similar to YouTube's comment section
  - Profile pictures (with fallback for missing avatars)
  - Collapsible reply threads
  - Timestamps, like counts, and heart indicators (❤️) for creator-hearted comments
- **JSON** - Structured JSON output with:
  - Complete metadata including total comment count
  - Nested reply threading
  - `"heart": true/false` field for hearted comments
- **PDF** - Professional PDF document with formatted comments:
  - Clean typography with proper spacing
  - Hierarchical layout with indented replies
  - Timestamps, like counts, and heart indicators
  - Requires `reportlab` package: `pip install reportlab`

#### Dual Export with Raw TXT
- **Include Raw TXT** checkbox (enabled by default)
- When checked, automatically creates a plain text version alongside your primary export format
- TXT files are saved in a `Raw/` subfolder for better organization
- No need to download comments twice - both formats are generated in one pass
- Plain text format includes:
  - Readable threading with `↳` reply indicators
  - `[♥ Hearted by Creator]` tags for hearted comments
  - Author names, timestamps, and like counts

#### User Filtering & Database
- **Filter by User** dropdown with options:
  - **None** - Download all comments (default)
  - **Video Author** - Automatically filter to show only the video creator's comments
  - **Saved Users** - Filter by users you've previously saved to the database
  - **More...** - Opens the User Database Manager
- **User Database Manager** - Enhanced dialog with improved UX:
  - View all saved users with display name and @handle
  - **Larger, clearer user entries** (12pt bold display names)
  - **Folder button** (📁) next to each user - opens their folder in file explorer
    - Greyed out if no folder exists yet
    - Enabled when you've downloaded content from that user
  - **Download Posts button** - Download all posts from a user's community tab
    - Downloads all posts from the selected user's community tab
    - Posts are saved to `[Export]/[Username]/posts/` folder
    - Images are saved to `posts/assets/` subfolder
    - No comments are downloaded (community posts don't support reliable comment downloads)
  - **Right-click context menu** - Right-click on any user to access:
    - **Open Channel** - Opens the user's YouTube channel in your default browser
  - **Add User by URL** - Add any YouTube channel:
    - Click "Add User..." button
    - Enter a YouTube channel URL (supports `@username`, `/channel/UC...`, `/c/name` formats)
    - Automatically fetches channel name and ID
    - Channel is added to your database for future filtering
  - Automatically saves video authors when downloading their content
  - Select users for filtering in future downloads
  - Delete users from the database
  - Users persist between sessions
- When filtering, parent comments are automatically included when the filtered user replied to them (for conversation context)

#### YouTube Community Posts
- **Download posts from a user's community tab** (not individual post URLs)
- Use the "Download Posts" button in the User Database Manager
- Features:
  - Downloads all posts from a creator's community tab
  - Extracts post content (text)
  - Downloads attached images to `posts/assets/` folder
  - Generates individual HTML files for each post (no comments)
- Posts are saved to a separate `posts/` folder (see folder structure below)
- **Note:** Community post URLs are no longer supported in the main URL field. Use the "Download Posts" button instead.

#### Automatic Folder Organization
- Select a base export folder once (remembered between sessions)
- Files are automatically organized into a clean folder structure:
  ```
  [Export Folder]/
  ├── [Creator Name]/
  │   ├── videos/
  │   │   ├── [Video Title] - comments.html      (or .json, .pdf)
  │   │   ├── [Video Title] - comments - filtered.html
  │   │   └── Raw/
  │   │       ├── [Video Title] - comments.txt
  │   │       └── [Video Title] - comments - filtered.txt
  │   └── posts/
  │       ├── 2026-01-17 - Post Title.html       (post content, no comments)
  │       └── assets/
  │           ├── post_image_1.jpg
  │           └── post_image_2.png
  └── [Another Creator]/
      └── ...
  ```
- Filenames are automatically sanitized for compatibility
- `Raw/` subfolder is inside `videos/` folders only (created when "Include Raw TXT" is enabled)
- `assets/` subfolder stores images from community posts
- After download completes, the export folder opens automatically

#### Real-time Progress Tracking
- Live progress bar showing download percentage
- Status updates: "Downloading... 50/1,234 comments (4%)"
- Comment count estimation before download begins
- Updates every 10 comments for efficiency

**Note:** The GUI uses Tkinter, which is included with Python on macOS (both system Python and Homebrew Python). No additional dependencies are required.


### Usage as library
You can also use this script as a library. For instance, if you want to print out the 10 most popular comments for a particular Youtube video you can do the following:


```python
from itertools import islice
from youtube_comment_downloader import *
downloader = YoutubeCommentDownloader()
comments = downloader.get_comments_from_url('https://www.youtube.com/watch?v=ScMzIvxBSi4', sort_by=SORT_BY_POPULAR)
for comment in islice(comments, 10):
    print(comment)
```
