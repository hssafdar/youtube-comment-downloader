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
from .pdf_export import generate_pdf_output
from .user_database import UserDatabase

# Constants
DEFAULT_COMMENT_LIMIT = 1000  # Default limit for comment downloads


class UserDatabaseDialog:
    """Dialog for managing users in the database"""
    
    def __init__(self, parent, user_db, export_folder=None, main_gui=None):
        self.user_db = user_db
        self.export_folder = export_folder
        self.main_gui = main_gui  # Reference to main GUI for checking download state
        self.result = None
        self.user_frames = []
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("User Database Manager")
        self.dialog.geometry("750x550")
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
        
        # Create a canvas with scrollbar for user list
        list_container = ttk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(list_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=canvas.yview)
        self.user_list_frame = ttk.Frame(canvas)
        
        self.user_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.user_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store canvas reference for mouse wheel binding
        self.canvas = canvas
        
        # Bind mouse wheel
        canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        canvas.bind_all("<Button-4>", self._on_mousewheel)
        canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="Add User...", command=self._add_user_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
    
    def _refresh_list(self):
        """Refresh the user list with profile pictures and folder buttons"""
        # Clear existing frames
        for frame in self.user_frames:
            frame.destroy()
        self.user_frames.clear()
        
        users = self.user_db.get_all_users()
        self.users = users
        
        if not users:
            no_users_label = ttk.Label(self.user_list_frame, text="(No users in database)", 
                                      font=('TkDefaultFont', 10))
            no_users_label.pack(pady=20)
            self.user_frames.append(no_users_label)
        else:
            for idx, user in enumerate(users):
                self._create_user_entry(user, idx)
    
    def _create_user_entry(self, user, idx):
        """
        Create a simplified user entry with bigger display name and Download Posts button
        
        Args:
            user: User dictionary
            idx: Index in the list
        """
        # Create frame for this user with padding and border effect
        user_frame = ttk.Frame(self.user_list_frame, relief=tk.RAISED, borderwidth=1)
        user_frame.pack(fill=tk.X, padx=5, pady=5)
        self.user_frames.append(user_frame)
        
        # Create inner frame with padding
        inner_frame = ttk.Frame(user_frame, padding="10")
        inner_frame.pack(fill=tk.X)
        
        # User info (display name and handle) - no profile picture
        info_frame = ttk.Frame(inner_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        display_name = user.get('display_name', 'Unknown')
        username = user.get('username', display_name)
        
        # Bigger display name (12pt bold)
        name_label = ttk.Label(info_frame, text=display_name, 
                              font=('TkDefaultFont', 12, 'bold'))
        name_label.pack(anchor=tk.W)
        
        handle_label = ttk.Label(info_frame, text=f"@{username}", 
                               font=('TkDefaultFont', 9), foreground='gray')
        handle_label.pack(anchor=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(inner_frame)
        buttons_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Folder button
        folder_exists = False
        if self.export_folder:
            folder_exists = self.user_db.user_folder_exists(self.export_folder, username)
        
        folder_btn = ttk.Button(buttons_frame, text="📁", width=4,
                               command=lambda u=user: self._open_user_folder(u))
        folder_btn.pack(side=tk.LEFT, padx=2)
        
        if not folder_exists:
            folder_btn.config(state=tk.DISABLED)
        
        # Download Posts button
        download_posts_btn = ttk.Button(buttons_frame, text="Download Posts", width=14,
                                       command=lambda u=user: self._download_user_posts(u))
        download_posts_btn.pack(side=tk.LEFT, padx=2)
        
        # Disable if main GUI is downloading
        if self.main_gui and self.main_gui.is_downloading:
            download_posts_btn.config(state=tk.DISABLED)
        
        # Select button
        select_btn = ttk.Button(buttons_frame, text="Select", width=8,
                               command=lambda u=user: self._select_user_by_data(u))
        select_btn.pack(side=tk.LEFT, padx=2)
        
        # Delete button
        delete_btn = ttk.Button(buttons_frame, text="Delete", width=8,
                               command=lambda u=user: self._delete_user_by_data(u))
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Bind right-click to show context menu
        for widget in [user_frame, inner_frame, info_frame, name_label, handle_label]:
            widget.bind("<Button-3>", lambda e, u=user: self._show_context_menu(e, u))
            # Also bind Button-2 for macOS
            widget.bind("<Button-2>", lambda e, u=user: self._show_context_menu(e, u))
    
    def _open_user_folder(self, user):
        """Open the user's folder in file explorer"""
        if not self.export_folder:
            return
        
        from .file_utils import sanitize_filename, open_folder
        username = user.get('username', user.get('display_name', ''))
        user_folder = os.path.join(self.export_folder, sanitize_filename(username))
        
        if os.path.isdir(user_folder):
            open_folder(user_folder)
    
    def _show_context_menu(self, event, user):
        """Show right-click context menu"""
        menu = tk.Menu(self.dialog, tearoff=0)
        menu.add_command(label="Open Channel", command=lambda: self._open_channel_url(user))
        menu.tk_popup(event.x_root, event.y_root)
    
    def _open_channel_url(self, user):
        """Open the user's YouTube channel URL in browser"""
        import webbrowser
        channel_url = user.get('channel_url', f"https://www.youtube.com/channel/{user['user_id']}")
        webbrowser.open(channel_url)
    
    def _download_user_posts(self, user):
        """Download all posts from a user's community tab"""
        if self.main_gui and self.main_gui.is_downloading:
            messagebox.showwarning("Download in Progress", 
                                  "Please wait for the current download to complete.",
                                  parent=self.dialog)
            return
        
        if not self.export_folder:
            messagebox.showerror("No Export Folder", 
                               "Please set an export folder in the main window first.",
                               parent=self.dialog)
            return
        
        # Start download in background thread
        import threading
        thread = threading.Thread(target=self._download_posts_worker, args=(user,), daemon=True)
        thread.start()
    
    def _download_posts_worker(self, user):
        """Worker thread for downloading posts"""
        try:
            from .post_downloader import YoutubePostDownloader
            from .file_utils import sanitize_filename
            from datetime import datetime
            
            channel_id = user['user_id']
            username = user.get('username', user.get('display_name', 'Unknown'))
            
            # Show progress dialog
            self.dialog.after(0, lambda: messagebox.showinfo(
                "Downloading Posts",
                f"Downloading posts from {user['display_name']}...\n\nThis may take a moment.",
                parent=self.dialog
            ))
            
            # Create downloader
            downloader = YoutubePostDownloader()
            
            # Fetch posts from community tab
            posts = downloader.get_channel_posts(channel_id)
            
            if not posts:
                self.dialog.after(0, lambda: messagebox.showinfo(
                    "No Posts Found",
                    f"No posts found for {user['display_name']}.",
                    parent=self.dialog
                ))
                return
            
            # Create output folder structure
            safe_username = sanitize_filename(username)
            user_folder = os.path.join(self.export_folder, safe_username)
            posts_folder = os.path.join(user_folder, 'posts')
            assets_folder = os.path.join(posts_folder, 'assets')
            os.makedirs(assets_folder, exist_ok=True)
            
            # Download each post
            posts_saved = 0
            for post in posts:
                try:
                    # Download images
                    local_images = []
                    for img_url in post.get('images', []):
                        try:
                            import requests
                            from urllib.parse import urlparse
                            
                            # Validate URL - ensure it's from trusted YouTube/Google domains
                            parsed = urlparse(img_url)
                            allowed_domains = ['ytimg.com', 'ggpht.com', 'googleusercontent.com', 'youtube.com']
                            # Use endswith to check domain suffix (prevents evil-ytimg.com attacks)
                            if not any(parsed.netloc.endswith(domain) or parsed.netloc == domain for domain in allowed_domains):
                                continue
                            
                            response = requests.get(img_url, timeout=30)
                            response.raise_for_status()
                            
                            # Determine extension
                            ext = '.jpg'
                            if 'content-type' in response.headers:
                                content_type = response.headers['content-type']
                                if 'png' in content_type:
                                    ext = '.png'
                                elif 'webp' in content_type:
                                    ext = '.webp'
                            
                            img_filename = f"post_{post['post_id']}_{len(local_images)}{ext}"
                            img_path = os.path.join(assets_folder, img_filename)
                            
                            with open(img_path, 'wb') as f:
                                f.write(response.content)
                            
                            local_images.append(img_filename)
                        except Exception:
                            continue
                    
                    # Generate HTML for post
                    post_content = post.get('content', 'No content')
                    post_date = post.get('published_time', '')
                    
                    # Use current date for filename (post dates are relative like "2 days ago")
                    date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    # Truncate title
                    title_preview = post_content[:50].replace('\n', ' ') if post_content else 'Post'
                    safe_title = sanitize_filename(title_preview)
                    post_filename = f"{date_str} - {safe_title}.html"
                    post_path = os.path.join(posts_folder, post_filename)
                    
                    # Generate HTML
                    html_content = self._generate_post_html(post, local_images, username)
                    
                    with open(post_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    posts_saved += 1
                except Exception:
                    continue
            
            # Show completion message
            self.dialog.after(0, lambda: messagebox.showinfo(
                "Download Complete",
                f"Successfully downloaded {posts_saved} post(s) from {user['display_name']}.",
                parent=self.dialog
            ))
            
            # Open posts folder
            from .file_utils import open_folder
            self.dialog.after(0, lambda: open_folder(posts_folder))
            
        except Exception as e:
            self.dialog.after(0, lambda: messagebox.showerror(
                "Download Error",
                f"Error downloading posts: {str(e)}",
                parent=self.dialog
            ))
    
    def _generate_post_html(self, post, local_images, channel_name):
        """Generate HTML for a single post"""
        import html as html_module
        
        content = html_module.escape(post.get('content', ''))
        published = html_module.escape(post.get('published_time', ''))
        
        images_html = ''
        for img_filename in local_images:
            images_html += f'<img class="image" src="assets/{img_filename}" alt="Post image">\n'
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Post by {html_module.escape(channel_name)}</title>
    <style>
        body {{ background: #0f0f0f; color: #f1f1f1; font-family: Roboto, sans-serif; padding: 20px; }}
        .post {{ max-width: 800px; margin: auto; background: #212121; padding: 20px; border-radius: 12px; }}
        .content {{ white-space: pre-wrap; margin-bottom: 20px; line-height: 1.6; }}
        .image {{ max-width: 100%; border-radius: 8px; margin: 10px 0; display: block; }}
        .meta {{ color: #aaa; font-size: 12px; margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="post">
        <div class="meta">{published}</div>
        <div class="content">{content}</div>
        {images_html}
    </div>
</body>
</html>"""
    
    def _select_user_by_data(self, user):
        """Select a user by data"""
        self.result = user
        self.dialog.destroy()
    
    def _delete_user_by_data(self, user):
        """Delete a user by data"""
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete user '{user['display_name']}'?",
                              parent=self.dialog):
            self.user_db.delete_user(user['user_id'])
            self._refresh_list()
    
    def _add_user_dialog(self):
        """Show dialog to add user by URL"""
        add_dialog = tk.Toplevel(self.dialog)
        add_dialog.title("Add User")
        add_dialog.geometry("500x180")
        add_dialog.transient(self.dialog)
        add_dialog.grab_set()
        
        # Center the dialog
        add_dialog.update_idletasks()
        x = (add_dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (add_dialog.winfo_screenheight() // 2) - (180 // 2)
        add_dialog.geometry(f"500x180+{x}+{y}")
        
        frame = ttk.Frame(add_dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(frame, text="Enter YouTube channel URL:").pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text="(e.g., youtube.com/@username or youtube.com/channel/UC...)", 
                 font=('TkDefaultFont', 8)).pack(anchor=tk.W, pady=(0, 10))
        
        # URL entry
        url_entry = ttk.Entry(frame, width=60)
        url_entry.pack(fill=tk.X, pady=(0, 10))
        url_entry.focus()
        
        # Status label
        status_label = ttk.Label(frame, text="", foreground="blue")
        status_label.pack(pady=(5, 10))
        
        def do_add():
            url = url_entry.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter a URL", parent=add_dialog)
                return
            
            status_label.config(text="Fetching user info...", foreground="blue")
            add_dialog.update()
            
            # Fetch user info in a thread to avoid blocking UI
            def fetch_and_add():
                user_info = self.user_db.fetch_user_from_url(url)
                
                if user_info:
                    # Add to database
                    success = self.user_db.add_user(
                        user_id=user_info['user_id'],
                        username=user_info.get('username', user_info['display_name']),
                        display_name=user_info['display_name'],
                        profile_pic_url=user_info.get('profile_pic_url'),
                        channel_url=user_info.get('channel_url')
                    )
                    
                    if success:
                        add_dialog.after(0, lambda: status_label.config(
                            text=f"✓ Added: {user_info['display_name']}", foreground="green"))
                        add_dialog.after(1000, add_dialog.destroy)
                        add_dialog.after(1000, self._refresh_list)
                    else:
                        add_dialog.after(0, lambda: status_label.config(
                            text="Error: Could not add user to database", foreground="red"))
                else:
                    add_dialog.after(0, lambda: status_label.config(
                        text="Error: Could not fetch user info from URL", foreground="red"))
            
            import threading
            thread = threading.Thread(target=fetch_and_add, daemon=True)
            thread.start()
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="Cancel", command=add_dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Add", command=do_add).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        url_entry.bind('<Return>', lambda e: do_add())



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
        self.cancel_requested = False
        
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
        self.limit_entry.insert(0, str(DEFAULT_COMMENT_LIMIT))  # Default limit
        ttk.Label(main_frame, text="(number of comments)").grid(row=row, column=2, sticky=tk.W, pady=5)
        row += 1
        
        # Export format dropdown
        ttk.Label(main_frame, text="Export Format:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.export_format_var = tk.StringVar(value=self.config.get('last_format', 'Dark HTML'))
        format_combo = ttk.Combobox(main_frame, textvariable=self.export_format_var,
                                    values=["Dark HTML", "JSON", "PDF"],
                                    state="readonly", width=18)
        format_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Include Raw TXT checkbox
        self.include_raw_txt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Include Raw TXT", 
                       variable=self.include_raw_txt_var).grid(row=row, column=1, sticky=tk.W, pady=5)
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
        
        self.stop_button = ttk.Button(button_frame, text="Cancel", command=self._cancel_download, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.close_button = ttk.Button(button_frame, text="Close", command=self._close_window)
        self.close_button.pack(side=tk.LEFT, padx=5)
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
        export_folder = self.folder_entry.get().strip()
        dialog = UserDatabaseDialog(self.root, self.user_db, export_folder, main_gui=self)
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
    
    def _extract_post_id(self, url_or_id):
        """
        Extract YouTube post ID from URL
        
        Supports post URL format:
        - https://www.youtube.com/post/UgkxKAIenznpuQyqwQkt0_aAnz5SQoK5rwAY
        
        Args:
            url_or_id: YouTube URL
            
        Returns:
            Post ID if valid post URL, None otherwise
        """
        url_or_id = url_or_id.strip()
        
        # Check if it's a post URL
        post_pattern = r'youtube\.com\/post\/([A-Za-z0-9_-]+)'
        match = re.search(post_pattern, url_or_id)
        
        if match:
            return match.group(1)
        
        return None
    
    def _is_post_url(self, url):
        """Check if URL is a community post"""
        return '/post/' in url
    
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
        
        # Check if user entered a post URL
        url_or_id = self.url_entry.get().strip()
        if self._is_post_url(url_or_id):
            messagebox.showerror(
                "Post URLs Not Supported",
                "Post URLs are not supported for comment downloads.\n\n"
                "To download a creator's posts, use the 'Download Posts' button "
                "in the User Database Manager (Manage... button)."
            )
            return
        
        # Reset cancel flag
        self.cancel_requested = False
        
        # Disable download button, enable cancel button
        self.download_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_downloading = True
        
        # Clear status
        self.status_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        # Start download thread
        self.download_thread = threading.Thread(target=self._download_comments, daemon=True)
        self.download_thread.start()
    
    def _cancel_download(self):
        """Cancel the current download"""
        if not self.is_downloading:
            return
        
        self.cancel_requested = True
        self._log_status("")
        self._log_status("Cancelling download...")
        self.stop_button.config(state=tk.DISABLED)
    
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
            include_raw_txt = self.include_raw_txt_var.get()
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
            
            # Handle video only (posts are no longer supported here)
            video_id = self._extract_video_id(url_or_id)
            if not video_id:
                raise Exception("Invalid YouTube URL or video ID")
            
            full_url = f"https://www.youtube.com/watch?v={video_id}"
            content_id = video_id
            
            self._log_status(f"Downloading YouTube comments for video: {video_id}")
            
            self._log_status(f"Sort: {sort_display}")
            if language:
                self._log_status(f"Language: {language}")
            if limit:
                self._log_status(f"Limit: {limit}")
            
            # Map export format to extension
            format_map = {
                "Dark HTML": "html",
                "JSON": "json",
                "PDF": "pdf"
            }
            file_extension = format_map.get(export_format, "html")
            
            self._log_status(f"Export format: {export_format}")
            self._log_status("")
            
            # Create video downloader
            downloader = YoutubeCommentDownloader()
            
            # Get video metadata
            self._log_status("Fetching video metadata...")
            metadata = downloader.get_video_metadata(full_url)
            
            if not metadata:
                raise Exception("Could not extract video metadata")
            
            content_title = metadata.get('title', 'Unknown Video')
            channel_name = metadata.get('channel_name', 'Unknown Creator')
            channel_id = metadata.get('channel_id', '')
            
            self._log_status(f"Video: {content_title}")
            self._log_status(f"Channel: {channel_name}")
            
            # Auto-add content author to database
            if channel_id and channel_name:
                channel_thumbnail = metadata.get('channel_thumbnail', '')
                self.user_db.add_user(
                    user_id=channel_id,
                    username=channel_name,
                    display_name=channel_name,
                    profile_pic_url=channel_thumbnail,
                    channel_url=f"https://www.youtube.com/channel/{channel_id}"
                )
                self._log_status(f"Added '{channel_name}' to user database")
            
            # Set filter user if filtering by content author
            if filter_mode == "video_author":
                filter_user_id = channel_id
                filter_user_name = channel_name
            
            if filter_user_name:
                self._log_status(f"Filter: {filter_user_name} only")
            
            self._log_status("")
            
            # Get comment generator (videos only now)
            generator = downloader.get_comments(content_id, sort_by, language)
            
            # Download comments to list
            all_comments = []
            count = 0
            start_time = time.time()
            
            # Estimate total if available
            total_estimate = metadata.get('comment_count', 0)
            
            self._log_status("Downloading comments...")
            for comment in generator:
                # Check for cancellation
                # Note: finally block will run even on early return
                if self.cancel_requested:
                    self._log_status("Download cancelled by user")
                    return
                
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
            
            # Check for cancellation after download
            if self.cancel_requested:
                self._log_status("Download cancelled by user")
                return
            
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
            
            # Check for cancellation before saving
            if self.cancel_requested:
                self._log_status("Download cancelled by user")
                return
            
            # Create export path using file_utils (video only)
            output_path, output_folder = create_export_path(
                base_folder=export_folder,
                creator_name=channel_name,
                video_title=content_title,
                export_format=file_extension,
                is_filtered=is_filtered,
                is_post=False
            )
            
            self._log_status("")
            self._log_status(f"Saving to: {output_path}")
            
            # Check for cancellation before writing files
            if self.cancel_requested:
                self._log_status("Download cancelled by user")
                return
            
            # Write output based on format (videos only, no post metadata)
            if export_format == "Dark HTML":
                filter_label = filter_user_name if is_filtered else None
                generate_html_output(filtered_comments, output_path, filter_label, None)
            elif export_format == "JSON":
                filter_label = filter_user_name if is_filtered else None
                generate_json_output(filtered_comments, output_path, filter_label, None)
            elif export_format == "PDF":
                try:
                    filter_label = filter_user_name if is_filtered else None
                    generate_pdf_output(filtered_comments, output_path, filter_label, None)
                except ImportError as e:
                    self.root.after(0, self._log_status, "")
                    self.root.after(0, self._log_status, f"PDF export error: {str(e)}")
                    self.root.after(0, messagebox.showerror, "PDF Export Error", 
                                   "PDF export requires reportlab. Install it with: pip install reportlab")
                    return
            
            # If include_raw_txt is checked, also export to TXT in Raw folder
            if include_raw_txt:
                # Raw folder should be inside the videos folder
                raw_folder = os.path.join(output_folder, 'Raw')
                os.makedirs(raw_folder, exist_ok=True)
                
                # Create TXT filename
                safe_title = os.path.basename(output_path).rsplit('.', 1)[0]  # Remove extension
                txt_filename = f"{safe_title}.txt"
                txt_path = os.path.join(raw_folder, txt_filename)
                
                self._log_status(f"Also saving TXT to: {txt_path}")
                filter_label = filter_user_name if is_filtered else None
                generate_txt_output(filtered_comments, txt_path, filter_label, None)
            
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
            # Re-enable download button and disable cancel button
            self.root.after(0, self.download_button.config, {"state": tk.NORMAL})
            self.root.after(0, self.stop_button.config, {"state": tk.DISABLED})
            self.root.after(0, self.progress_var.set, 0)
            self.is_downloading = False
            self.cancel_requested = False
    
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
    # Fix Mac app name in dock
    try:
        import platform
        if platform.system() == 'Darwin':
            try:
                # Try different pyobjc imports
                try:
                    from Foundation import NSBundle
                except ImportError:
                    from AppKit import NSBundle
                
                bundle = NSBundle.mainBundle()
                if bundle:
                    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                    if info:
                        info['CFBundleName'] = 'YouTube Comment Downloader'
            except ImportError:
                # pyobjc not installed, skip Mac-specific naming
                pass
    except Exception:
        # Ignore any errors in Mac app naming
        pass
    
    root = tk.Tk()
    app = YouTubeCommentDownloaderGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
