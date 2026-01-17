#!/usr/bin/env python
"""
Tkinter GUI for YouTube Comment Downloader
"""

import io
import json
import os
import re
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT
from .html_export import generate_html_output

INDENT = 4


def to_json(comment, indent=None):
    """Convert comment to JSON string with optional indentation"""
    comment_str = json.dumps(comment, ensure_ascii=False, indent=indent)
    if indent is None:
        return comment_str
    padding = ' ' * (2 * indent) if indent else ''
    return ''.join(padding + line for line in comment_str.splitlines(True))


class YouTubeCommentDownloaderGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Comment Downloader")
        
        # Set window size and center on screen
        window_width = 700
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.download_thread = None
        self.is_downloading = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # YouTube URL/ID
        ttk.Label(main_frame, text="YouTube URL or ID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Sort
        ttk.Label(main_frame, text="Sort:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sort_var = tk.IntVar(value=SORT_BY_RECENT)
        sort_frame = ttk.Frame(main_frame)
        sort_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        # Create a mapping between display values and actual values
        self.sort_options = {"Popular": SORT_BY_POPULAR, "Recent": SORT_BY_RECENT}
        self.sort_display_var = tk.StringVar(value="Recent")
        ttk.Combobox(sort_frame, textvariable=self.sort_display_var, 
                     values=list(self.sort_options.keys()), 
                     state="readonly", width=15).pack(side=tk.LEFT)
        row += 1
        
        # Language
        ttk.Label(main_frame, text="Language (optional):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.language_entry = ttk.Entry(main_frame, width=20)
        self.language_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="(e.g., en)").grid(row=row, column=2, sticky=tk.W, pady=5)
        row += 1
        
        # Limit
        ttk.Label(main_frame, text="Limit (optional):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.limit_entry = ttk.Entry(main_frame, width=20)
        self.limit_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="(number of comments)").grid(row=row, column=2, sticky=tk.W, pady=5)
        row += 1
        
        # Filter by Video Author
        self.filter_author_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Filter by Video Author", 
                       variable=self.filter_author_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # HTML export (checked by default)
        self.html_export_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Export as HTML", 
                       variable=self.html_export_var, command=self._on_html_export_toggle).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Output file
        ttk.Label(main_frame, text="Output file:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.output_entry = ttk.Entry(main_frame, width=40)
        self.output_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.browse_button = ttk.Button(main_frame, text="Browse...", command=self._browse_output)
        self.browse_button.grid(row=row, column=2, sticky=tk.W, pady=5, padx=(5, 0))
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        self.download_button = ttk.Button(button_frame, text="Download", command=self._start_download)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Close", command=self._close_window)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Status area
        ttk.Label(main_frame, text="Status:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        row += 1
        
        # Text widget with scrollbar for status/log
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(row, weight=1)
        
        self.status_text = tk.Text(text_frame, height=15, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self._log_status("Ready to download YouTube comments.")
    
    def _browse_output(self):
        """Open file dialog to select output file"""
        # Determine default extension based on HTML export checkbox
        if self.html_export_var.get():
            default_ext = ".html"
            filetypes = [("HTML files", "*.html"), ("All files", "*.*")]
        else:
            default_ext = ".json"
            filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        
        filename = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=default_ext,
            filetypes=filetypes
        )
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)
    
    def _on_html_export_toggle(self):
        """Handle HTML export checkbox toggle"""
        # Update the output file extension if one is already selected
        current_output = self.output_entry.get().strip()
        if current_output:
            if self.html_export_var.get():
                # Switch to .html
                if current_output.endswith('.json'):
                    new_output = current_output[:-5] + '.html'
                    self.output_entry.delete(0, tk.END)
                    self.output_entry.insert(0, new_output)
            else:
                # Switch to .json
                if current_output.endswith('.html'):
                    new_output = current_output[:-5] + '.json'
                    self.output_entry.delete(0, tk.END)
                    self.output_entry.insert(0, new_output)
    
    def _extract_video_id(self, url_or_id):
        """
        Extract YouTube video ID from URL or return the ID itself
        
        Supports various YouTube URL formats:
        - Standard: youtube.com/watch?v=VIDEO_ID
        - Short: youtu.be/VIDEO_ID
        - Embed: youtube.com/embed/VIDEO_ID
        - Shorts: youtube.com/shorts/VIDEO_ID
        - With parameters: youtube.com/watch?v=VIDEO_ID&t=123s
        
        Args:
            url_or_id: YouTube URL or video ID
            
        Returns:
            Video ID if valid, None otherwise
        """
        url_or_id = url_or_id.strip()
        
        # Try to extract from various YouTube URL formats first
        # Pattern 1: Matches direct video paths (watch, shorts, embed, etc.)
        direct_path_pattern = (
            r'(?:youtube\.com\/watch\?v=|'  # Standard watch URL
            r'youtu\.be\/|'                  # Short URL
            r'youtube\.com\/embed\/|'        # Embed URL
            r'youtube\.com\/v\/|'            # Legacy v URL
            r'youtube\.com\/shorts\/)'       # Shorts URL
            r'([a-zA-Z0-9_-]{11})'          # Video ID (11 chars)
        )
        
        # Pattern 2: Matches v parameter in any YouTube URL
        v_param_pattern = r'youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})'
        
        for pattern in [direct_path_pattern, v_param_pattern]:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        # If it looks like just an ID (exactly 11 characters, alphanumeric with _ or -), return it
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
        
        return None
    
    def _log_status(self, message):
        """Add message to status text area"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.update_idletasks()
    
    def _filter_comments_by_author(self, all_comments, author_channel_id):
        """
        Filter comments to show only those by the video author
        Also include parent comments when the author replied to them
        
        Args:
            all_comments: List of all comment dictionaries
            author_channel_id: Channel ID of the video author
        
        Returns:
            List of filtered comments
        """
        if not author_channel_id:
            return all_comments
        
        # Build a map of comment IDs to comments for lookup
        comment_map = {c['cid']: c for c in all_comments}
        
        result = []
        result_cids = set()
        
        for comment in all_comments:
            # Check if this comment is by the video author
            comment_channel = comment.get('channel', '')
            
            # Match by channel ID
            is_author = comment_channel == author_channel_id
            
            if is_author:
                # Add the author's comment
                if comment['cid'] not in result_cids:
                    result.append(comment)
                    result_cids.add(comment['cid'])
                
                # If it's a reply, also include the parent comment for context
                if comment.get('reply'):
                    parent_cid = comment['cid'].rsplit('.', 1)[0]
                    parent = comment_map.get(parent_cid)
                    if parent and parent['cid'] not in result_cids:
                        # Insert parent before the reply
                        idx = result.index(comment)
                        result.insert(idx, parent)
                        result_cids.add(parent['cid'])
        
        return result
    
    def _validate_inputs(self):
        """Validate user inputs"""
        url_or_id = self.url_entry.get().strip()
        output_file = self.output_entry.get().strip()
        
        if not url_or_id:
            messagebox.showerror("Input Error", "Please enter a YouTube URL or ID")
            return False
        
        if not output_file:
            messagebox.showerror("Input Error", "Please specify an output file")
            return False
        
        # Validate limit if provided
        limit_text = self.limit_entry.get().strip()
        if limit_text:
            try:
                limit = int(limit_text)
                if limit <= 0:
                    messagebox.showerror("Input Error", "Limit must be a positive integer")
                    return False
            except ValueError:
                messagebox.showerror("Input Error", "Limit must be a valid integer")
                return False
        
        return True
    
    def _start_download(self):
        """Start the download process in a background thread"""
        if self.is_downloading:
            messagebox.showwarning("Download in Progress", "A download is already in progress")
            return
        
        if not self._validate_inputs():
            return
        
        # Disable download button
        self.download_button.config(state=tk.DISABLED)
        self.is_downloading = True
        
        # Clear status
        self.status_text.delete(1.0, tk.END)
        
        # Start download thread
        self.download_thread = threading.Thread(target=self._download_comments, daemon=True)
        self.download_thread.start()
    
    def _download_comments(self):
        """Download comments (runs in background thread)"""
        try:
            # Get inputs
            url_or_id = self.url_entry.get().strip()
            output_file = self.output_entry.get().strip()
            # Get sort_by from display variable
            sort_display = self.sort_display_var.get()
            sort_by = self.sort_options[sort_display]
            language = self.language_entry.get().strip() or None
            limit_text = self.limit_entry.get().strip()
            limit = int(limit_text) if limit_text else None
            filter_author = self.filter_author_var.get()
            html_export = self.html_export_var.get()
            
            # Determine if input is URL or ID
            is_url = url_or_id.startswith('http://') or url_or_id.startswith('https://')
            
            # Build full URL if needed
            if is_url:
                full_url = url_or_id
            else:
                full_url = f"https://www.youtube.com/watch?v={url_or_id}"
            
            # Create output directory if needed
            if os.sep in output_file:
                outdir = os.path.dirname(output_file)
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                    self._log_status(f"Created directory: {outdir}")
            
            self._log_status(f"Downloading YouTube comments for {url_or_id}...")
            self._log_status(f"Sort: {sort_display}")
            if language:
                self._log_status(f"Language: {language}")
            if limit:
                self._log_status(f"Limit: {limit}")
            if filter_author:
                self._log_status(f"Filter: Video Author only")
            if html_export:
                self._log_status(f"Export format: HTML (dark mode)")
            else:
                self._log_status(f"Export format: JSON")
            self._log_status(f"Output: {output_file}")
            self._log_status("")
            
            # Create downloader
            downloader = YoutubeCommentDownloader()
            
            # Get video author channel ID if filtering is enabled
            author_channel_id = None
            if filter_author:
                self._log_status("Extracting video author information...")
                author_channel_id = downloader.get_video_author_channel_id(full_url)
                if author_channel_id:
                    self._log_status(f"Video author channel ID: {author_channel_id}")
                else:
                    self._log_status("Warning: Could not extract video author channel ID. Filter may not work.")
                self._log_status("")
            
            # Get comment generator
            if is_url:
                generator = downloader.get_comments_from_url(url_or_id, sort_by, language)
            else:
                generator = downloader.get_comments(url_or_id, sort_by, language)
            
            # Download comments to list (needed for filtering and HTML export)
            all_comments = []
            count = 0
            start_time = time.time()
            
            self._log_status("Downloading comments...")
            for comment in generator:
                all_comments.append(comment)
                count += 1
                if limit and count >= limit:
                    break
                if count % 10 == 0:
                    self.root.after(0, self._log_status, f"Downloaded {count} comment(s)...")
            
            if count > 0:
                self.root.after(0, self._log_status, f"Downloaded {count} comment(s)...")
            
            # Apply author filter if specified
            filtered_comments = all_comments
            if filter_author and author_channel_id:
                self._log_status("")
                self._log_status("Applying video author filter...")
                filtered_comments = self._filter_comments_by_author(all_comments, author_channel_id)
                self.root.after(0, self._log_status, 
                              f"Filtered to {len(filtered_comments)} comment(s) by video author")
            
            # Write output
            if html_export:
                # Generate HTML (always dark mode)
                self._log_status("")
                self._log_status("Generating HTML output (dark mode)...")
                filter_label = "Video Author" if filter_author and author_channel_id else None
                generate_html_output(filtered_comments, output_file, filter_label)
            else:
                # Write JSON (raw, not pretty-printed)
                self._log_status("")
                self._log_status("Writing JSON output...")
                fp = None
                try:
                    fp = io.open(output_file, 'w', encoding='utf8')
                    # Write raw JSON array
                    fp.write('[')
                    for i, comment in enumerate(filtered_comments):
                        if i > 0:
                            fp.write(',')
                        comment_str = to_json(comment, indent=None)
                        fp.write(comment_str)
                    fp.write(']')
                finally:
                    if fp:
                        fp.close()
            
            elapsed = time.time() - start_time
            if len(filtered_comments) > 0:
                self.root.after(0, self._log_status, "")
                self.root.after(0, self._log_status, f"[{elapsed:.2f} seconds] Done!")
                self.root.after(0, self._log_status, f"Total comments in output: {len(filtered_comments)}")
                self.root.after(0, messagebox.showinfo, "Download Complete", 
                               f"Successfully saved {len(filtered_comments)} comments to {output_file}")
            else:
                self.root.after(0, self._log_status, "No comments available!")
                self.root.after(0, messagebox.showwarning, "No Comments", "No comments were found")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, self._log_status, "")
            self.root.after(0, self._log_status, error_msg)
            self.root.after(0, messagebox.showerror, "Download Error", error_msg)
        
        finally:
            # Re-enable download button
            self.root.after(0, self.download_button.config, {"state": tk.NORMAL})
            self.is_downloading = False
    
    def _close_window(self):
        """Close the window"""
        if self.is_downloading:
            if not messagebox.askyesno("Download in Progress", 
                                      "A download is in progress. Are you sure you want to exit?"):
                return
        self.root.quit()
        self.root.destroy()


def main():
    """Main entry point for the GUI"""
    root = tk.Tk()
    app = YouTubeCommentDownloaderGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
