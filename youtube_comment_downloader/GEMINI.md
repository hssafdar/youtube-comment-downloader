# YouTube Comment Downloader

A Python-based utility to download YouTube comments without using the official YouTube API. It supports both a Command Line Interface (CLI) and a Graphical User Interface (GUI).

## Project Overview

The project uses the internal YouTube InnerTube API (via `requests`) to fetch comments. It can handle regular videos, shorts, and community posts.

### Technologies
- **Python 3**
- **Libraries**: `requests`, `dateparser`, `tkinter` (GUI)
- **Architecture**:
  - `downloader.py`: Core logic for scraping comments using regex and JSON parsing of YouTube responses.
  - `gui.py`: Tkinter-based user interface.
  - `__init__.py`: Argument parsing and entry point for the CLI.

## Building and Running

### Prerequisites
Install dependencies:
```bash
pip install requests dateparser
```

### CLI Usage
Download comments from a video URL:
```bash
python3 -m youtube_comment_downloader --url "https://www.youtube.com/watch?v=VIDEO_ID" --output comments.json
```

Key arguments:
- `--url`, `-u`: YouTube video URL.
- `--youtubeid`, `-y`: YouTube video ID.
- `--limit`, `-l`: Maximum number of comments (Default: 250).
- `--sort`, `-s`: Sort order (0 for popular, 1 for recent).
- `--pretty`, `-p`: Pretty-print JSON output.

### GUI Usage
Launch the graphical interface:
```bash
python3 -m youtube_comment_downloader.gui
```

## Development Conventions

- **Surgical Updates**: Changes to CLI defaults should be reflected in `__init__.py`, while GUI defaults are in `gui.py`.
- **Parsing**: YouTube's response format changes frequently; `downloader.py` uses robust dictionary searching (`search_dict`) and regex to handle updates.
- **Output**: The default output format is line-delimited JSON (JSONL), unless the `--pretty` flag is used.

## Recent Changes
- Updated the default comment limit to **250** in both the CLI and GUI (per user request for more comprehensive comment collection).
- Added macOS Quick Actions infrastructure to enable right-click URL comment downloading with two workflows:
  - **Download Popular YouTube Comments**: Right-click any YouTube URL → downloads top 250 popular comments (sorted by likes/engagement)
  - **Download Recent YouTube Comments**: Right-click any YouTube URL → downloads 250 most recent comments (sorted by time)
  - Both workflows automatically save timestamped JSON files to `~/Downloads`

### Quick Actions Setup (macOS)
The Quick Actions are located in `quick_actions/` and can be installed by:
1. Double-clicking each `.workflow` file to install via Automator
2. Once installed, right-click any YouTube URL in Safari, Chrome, or text documents
3. Select **Services** → **Download Popular/Recent YouTube Comments**
4. Output files appear in `~/Downloads` as `popular_comments_YYYYMMDD_HHMMSS.json` or `recent_comments_YYYYMMDD_HHMMSS.json`
