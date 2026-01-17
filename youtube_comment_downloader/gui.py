#!/usr/bin/env python
"""
Tkinter GUI for YouTube Comment Downloader
"""

import os
import re
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .config import Config
from .downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT
from .file_utils import create_export_path, open_folder
from .html_export import generate_html_output
from .json_export import generate_json_output
from .txt_export import generate_txt_output
from .user_database import UserDatabase


class UserDatabaseDialog:
    """Dialog for managing users in the database"""
    
    def __init__(self, parent, user_db):
        self.user_db = user_db
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("User Database Manager")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._refresh_list()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Manage users for filtering:").pack(anchor=tk.W, pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.user_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.user_listbox.yview)
        
        self.user_listbox.bind('<Double-Button-1>', lambda e: self._select_user())
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="Select", command=self._select_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self._delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _refresh_list(self):
        """Refresh the user list"""
        self.user_listbox.delete(0, tk.END)
        users = self.user_db.get_all_users()
        self.users = users
        
        if not users:
            self.user_listbox.insert(tk.END, "(No users in database)")
        else:
            for user in users:
                display = f"{user['display_name']} (@{user['username']})"
                self.user_listbox.insert(tk.END, display)
    
    def _select_user(self):
        """Select a user from the list"""
        selection = self.user_listbox.curselection()
        if selection and self.users:
            idx = selection[0]
            if idx < len(self.users):
                self.result = self.users[idx]
                self.dialog.destroy()
    
    def _delete_user(self):
        """Delete selected user"""
        selection = self.user_listbox.curselection()
        if selection and self.users:
            idx = selection[0]
            if idx < len(self.users):
                user = self.users[idx]
                if messagebox.askyesno("Confirm Delete", 
                                      f"Delete user '{user['display_name']}'?"):
                    self.user_db.delete_user(user['user_id'])
                    self._refresh_list()


class YouTubeCommentDownloaderGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Comment Downloader")
        
        # Set window size and center on screen
        window_width = 700
        window_height = 650
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.download_thread = None
        self.is_downloading = False
        
        # Initialize config and database
        self.config = Config()
        self.user_db = UserDatabase()
        
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
        
        # Export format dropdown
        ttk.Label(main_frame, text="Export Format:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.export_format_var = tk.StringVar(value=self.config.get('last_format', 'Dark HTML'))
        format_combo = ttk.Combobox(main_frame, textvariable=self.export_format_var,
                                    values=["Dark HTML", "TXT", "JSON"],
                                    state="readonly", width=18)
        format_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Filter by user dropdown
        ttk.Label(main_frame, text="Filter by User:").grid(row=row, column=0, sticky=tk.W, pady=5)
        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.filter_user_var = tk.StringVar(value="None")
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_user_var,
                                         state="readonly", width=18)
        self.filter_combo.pack(side=tk.LEFT)
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_selected)
        self._update_filter_dropdown()
        
        ttk.Button(filter_frame, text="Manage...", 
                  command=self._open_user_manager).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Export folder
        ttk.Label(main_frame, text="Export Folder:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.folder_entry = ttk.Entry(main_frame, width=40)
        self.folder_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.folder_entry.insert(0, self.config.get_export_folder())
        self.browse_button = ttk.Button(main_frame, text="Browse...", command=self._browse_folder)
        self.browse_button.grid(row=row, column=2, sticky=tk.W, pady=5, padx=(5, 0))
        row += 1
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
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
        
        self.status_text = tk.Text(text_frame, height=12, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self._log_status("Ready to download YouTube comments.")
        
        # Store selected user info
        self.selected_user = None
    
    def _update_filter_dropdown(self):
        """Update the filter dropdown with users from database"""
        # Get users from database
        users = self.user_db.get_dropdown_users()
        
        # Build dropdown options
        options = ["None", "Video Author"]
        for user in users:
            options.append(f"{user['display_name']}")
        options.append("More...")
        
        self.filter_combo['values'] = options
        
        # Store user mapping
        self.filter_user_map = {}
        for user in users:
            self.filter_user_map[user['display_name']] = user
    
    def _on_filter_selected(self, event=None):
        """Handle filter dropdown selection"""
        selected = self.filter_user_var.get()
        if selected == "More...":
            # Reset to previous value and open manager
            self.filter_user_var.set("None")
            self._open_user_manager()
    
    def _open_user_manager(self):
        """Open the user database manager dialog"""
        dialog = UserDatabaseDialog(self.root, self.user_db)
        self.root.wait_window(dialog.dialog)
        
        # Refresh the dropdown
        self._update_filter_dropdown()
        
        # If a user was selected in the dialog, set it as filter
        if dialog.result:
            self.filter_user_var.set(dialog.result['display_name'])
    
    def _browse_folder(self):
        """Open folder dialog to select export folder"""
        folder = filedialog.askdirectory(
            title="Select export folder",
            initialdir=self.folder_entry.get() or None
        )
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.config.set_export_folder(folder)
    
    def _browse_output(self):
        """Removed - using folder picker instead"""
        pass
    
    def _on_html_export_toggle(self):
        """Removed - using dropdown instead"""
        pass
    
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
    
    def _update_progress(self, current, total):
        """Update progress bar and status"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_var.set(percentage)
            status_msg = f"Downloading... {current}/{total:,} comments ({percentage:.0f}%)"
            self._log_status(status_msg)
        self.root.update_idletasks()
    
    def _filter_comments_by_user(self, all_comments, user_channel_id):
        """
        Filter comments to show only those by a specific user
        Also include parent comments when the user replied to them
        
        Args:
            all_comments: List of all comment dictionaries
            user_channel_id: Channel ID of the user to filter by
        
        Returns:
            List of filtered comments
        """
        if not user_channel_id:
            return all_comments
        
        # Build a map of comment IDs to comments for lookup
        comment_map = {c['cid']: c for c in all_comments}
        
        result = []
        result_cids = set()
        
        for comment in all_comments:
            # Check if this comment is by the target user
            comment_channel = comment.get('channel', '')
            
            # Match by channel ID
            is_target_user = comment_channel == user_channel_id
            
            if is_target_user:
                # Add the user's comment
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
        export_folder = self.folder_entry.get().strip()
        
        if not url_or_id:
            messagebox.showerror("Input Error", "Please enter a YouTube URL or ID")
            return False
        
        if not export_folder:
            messagebox.showerror("Input Error", "Please specify an export folder")
            return False
        
        if not os.path.isdir(export_folder):
            messagebox.showerror("Input Error", "Export folder does not exist")
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
        self.progress_var.set(0)
        
        # Start download thread
        self.download_thread = threading.Thread(target=self._download_comments, daemon=True)
        self.download_thread.start()
    
    def _download_comments(self):
        """Download comments (runs in background thread)"""
        output_folder = None
        try:
            # Get inputs
            url_or_id = self.url_entry.get().strip()
            export_folder = self.folder_entry.get().strip()
            sort_display = self.sort_display_var.get()
            sort_by = self.sort_options[sort_display]
            language = self.language_entry.get().strip() or None
            limit_text = self.limit_entry.get().strip()
            limit = int(limit_text) if limit_text else None
            export_format = self.export_format_var.get()
            filter_user_display = self.filter_user_var.get()
            
            # Determine filter mode
            filter_mode = None
            filter_user_id = None
            filter_user_name = None
            
            if filter_user_display == "Video Author":
                filter_mode = "video_author"
            elif filter_user_display != "None" and filter_user_display in self.filter_user_map:
                filter_mode = "database_user"
                user = self.filter_user_map[filter_user_display]
                filter_user_id = user['user_id']
                filter_user_name = user['display_name']
            
            # Determine if input is URL or ID
            video_id = self._extract_video_id(url_or_id)
            if not video_id:
                raise Exception("Invalid YouTube URL or video ID")
            
            full_url = f"https://www.youtube.com/watch?v={video_id}"
            
            self._log_status(f"Downloading YouTube comments for video: {video_id}")
            self._log_status(f"Sort: {sort_display}")
            if language:
                self._log_status(f"Language: {language}")
            if limit:
                self._log_status(f"Limit: {limit}")
            
            # Map export format to extension
            format_map = {
                "Dark HTML": "html",
                "TXT": "txt",
                "JSON": "json"
            }
            file_extension = format_map.get(export_format, "html")
            
            self._log_status(f"Export format: {export_format}")
            self._log_status("")
            
            # Create downloader
            downloader = YoutubeCommentDownloader()
            
            # Get video metadata
            self._log_status("Fetching video metadata...")
            metadata = downloader.get_video_metadata(full_url)
            
            if not metadata:
                raise Exception("Could not extract video metadata")
            
            video_title = metadata.get('title', 'Unknown Video')
            channel_name = metadata.get('channel_name', 'Unknown Creator')
            channel_id = metadata.get('channel_id', '')
            
            self._log_status(f"Video: {video_title}")
            self._log_status(f"Channel: {channel_name}")
            
            # Auto-add video author to database
            if channel_id and channel_name:
                self.user_db.add_user(
                    user_id=channel_id,
                    username=channel_name,
                    display_name=channel_name,
                    channel_url=f"https://www.youtube.com/channel/{channel_id}"
                )
                self._log_status(f"Added '{channel_name}' to user database")
            
            # Set filter user if filtering by video author
            if filter_mode == "video_author":
                filter_user_id = channel_id
                filter_user_name = channel_name
            
            if filter_user_name:
                self._log_status(f"Filter: {filter_user_name} only")
            
            self._log_status("")
            
            # Get comment generator
            generator = downloader.get_comments(video_id, sort_by, language)
            
            # Download comments to list
            all_comments = []
            count = 0
            start_time = time.time()
            
            # Estimate total if available
            total_estimate = metadata.get('comment_count', 0)
            
            self._log_status("Downloading comments...")
            for comment in generator:
                all_comments.append(comment)
                count += 1
                if limit and count >= limit:
                    break
                    
                # Update progress every 10 comments
                if count % 10 == 0:
                    if total_estimate and not limit:
                        self.root.after(0, self._update_progress, count, total_estimate)
                    elif limit:
                        self.root.after(0, self._update_progress, count, limit)
                    else:
                        self.root.after(0, self._log_status, f"Downloaded {count:,} comment(s)...")
            
            if count > 0:
                self.root.after(0, self._log_status, f"Downloaded {count:,} comment(s)...")
            
            # Apply filter if specified
            filtered_comments = all_comments
            is_filtered = False
            
            if filter_user_id:
                self._log_status("")
                self._log_status(f"Applying filter for {filter_user_name}...")
                filtered_comments = self._filter_comments_by_user(all_comments, filter_user_id)
                is_filtered = True
                self.root.after(0, self._log_status, 
                              f"Filtered to {len(filtered_comments):,} comment(s) by {filter_user_name}")
            
            if len(filtered_comments) == 0:
                self.root.after(0, self._log_status, "No comments available!")
                self.root.after(0, messagebox.showwarning, "No Comments", "No comments were found")
                return
            
            # Create export path using file_utils
            output_path, output_folder = create_export_path(
                base_folder=export_folder,
                creator_name=channel_name,
                video_title=video_title,
                export_format=file_extension,
                is_filtered=is_filtered
            )
            
            self._log_status("")
            self._log_status(f"Saving to: {output_path}")
            
            # Write output based on format
            if export_format == "Dark HTML":
                filter_label = filter_user_name if is_filtered else None
                generate_html_output(filtered_comments, output_path, filter_label)
            elif export_format == "TXT":
                filter_label = filter_user_name if is_filtered else None
                generate_txt_output(filtered_comments, output_path, filter_label)
            elif export_format == "JSON":
                filter_label = filter_user_name if is_filtered else None
                generate_json_output(filtered_comments, output_path, filter_label)
            
            elapsed = time.time() - start_time
            self.root.after(0, self._log_status, "")
            self.root.after(0, self._log_status, f"[{elapsed:.2f} seconds] Done!")
            self.root.after(0, self._log_status, f"Total comments in output: {len(filtered_comments):,}")
            
            # Save settings
            self.config.set('last_format', export_format)
            
            # Open folder after download
            if output_folder:
                self.root.after(0, lambda: open_folder(output_folder))
            
            self.root.after(0, messagebox.showinfo, "Download Complete", 
                           f"Successfully saved {len(filtered_comments):,} comments to:\n{output_path}")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, self._log_status, "")
            self.root.after(0, self._log_status, error_msg)
            self.root.after(0, messagebox.showerror, "Download Error", error_msg)
        
        finally:
            # Re-enable download button and reset progress
            self.root.after(0, self.download_button.config, {"state": tk.NORMAL})
            self.root.after(0, self.progress_var.set, 0)
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
