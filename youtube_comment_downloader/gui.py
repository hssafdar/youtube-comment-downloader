#!/usr/bin/env python
"""
Tkinter GUI for YouTube Comment Downloader
"""

import io
import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT

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
        ttk.Combobox(sort_frame, textvariable=self.sort_var, values=[SORT_BY_POPULAR, SORT_BY_RECENT], 
                     state="readonly", width=15).pack(side=tk.LEFT)
        ttk.Label(sort_frame, text="  (0=Popular, 1=Recent)").pack(side=tk.LEFT)
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
        
        # Pretty output
        self.pretty_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Pretty output (indented JSON)", 
                       variable=self.pretty_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
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
        filename = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)
    
    def _log_status(self, message):
        """Add message to status text area"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.update_idletasks()
    
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
            sort_by = self.sort_var.get()
            language = self.language_entry.get().strip() or None
            limit_text = self.limit_entry.get().strip()
            limit = int(limit_text) if limit_text else None
            pretty = self.pretty_var.get()
            
            # Determine if input is URL or ID
            is_url = url_or_id.startswith('http://') or url_or_id.startswith('https://')
            
            # Create output directory if needed
            if os.sep in output_file:
                outdir = os.path.dirname(output_file)
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                    self._log_status(f"Created directory: {outdir}")
            
            self._log_status(f"Downloading YouTube comments for {url_or_id}...")
            self._log_status(f"Sort: {'Popular' if sort_by == SORT_BY_POPULAR else 'Recent'}")
            if language:
                self._log_status(f"Language: {language}")
            if limit:
                self._log_status(f"Limit: {limit}")
            self._log_status(f"Output: {output_file}")
            self._log_status("")
            
            # Create downloader
            downloader = YoutubeCommentDownloader()
            
            # Get comment generator
            if is_url:
                generator = downloader.get_comments_from_url(url_or_id, sort_by, language)
            else:
                generator = downloader.get_comments(url_or_id, sort_by, language)
            
            # Download and write comments
            fp = None
            count = 0
            start_time = time.time()
            comment = next(generator, None)
            
            while comment:
                if not fp:
                    fp = io.open(output_file, 'w', encoding='utf8')
                if pretty and count == 0:
                    fp.write('{\n' + ' ' * INDENT + '"comments": [\n')
                
                comment_str = to_json(comment, indent=INDENT if pretty else None)
                comment = None if limit and count >= limit else next(generator, None)
                comment_str = comment_str + ',' if pretty and comment is not None else comment_str
                print(comment_str.decode('utf-8') if isinstance(comment_str, bytes) else comment_str, file=fp)
                
                count += 1
                if count % 10 == 0 or comment is None:  # Update status every 10 comments or at end
                    self.root.after(0, self._log_status, f"Downloaded {count} comment(s)...")
            
            if pretty and fp:
                fp.write(' ' * INDENT + ']\n}')
            if fp:
                fp.close()
            
            elapsed = time.time() - start_time
            if count > 0:
                self.root.after(0, self._log_status, "")
                self.root.after(0, self._log_status, f"[{elapsed:.2f} seconds] Done!")
                self.root.after(0, self._log_status, f"Total comments downloaded: {count}")
                self.root.after(0, messagebox.showinfo, "Download Complete", 
                               f"Successfully downloaded {count} comments to {output_file}")
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
