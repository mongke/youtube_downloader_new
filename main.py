import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import traceback
import os
import re

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("620x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.downloading = False
        self.log_visible = False
        self.log_lines = []

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 13, "bold"))
        style.configure("TRadiobutton", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("Accent.TButton", background="#89b4fa", foreground="#1e1e2e", font=("Segoe UI", 11, "bold"))
        style.map("Accent.TButton", background=[("active", "#74c7ec")])
        style.configure("TButton", background="#313244", foreground="#cdd6f4", font=("Segoe UI", 9))
        style.map("TButton", background=[("active", "#45475a")])
        style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4")
        style.configure("green.Horizontal.TProgressbar", troughcolor="#313244", background="#a6e3a1")

        main = ttk.Frame(root, padding=18)
        main.pack(fill="both", expand=True)

        # --- URL ---
        ttk.Label(main, text="YouTube Downloader", style="Header.TLabel").pack(anchor="w")
        ttk.Label(main, text="Paste a YouTube video URL to get started", foreground="#6c7086").pack(anchor="w", pady=(0, 10))

        url_frame = ttk.Frame(main)
        url_frame.pack(fill="x", pady=(0, 8))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Segoe UI", 10))
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Button(url_frame, text="Paste", command=self.paste_url).pack(side="left", padx=(6, 0))

        # --- Quality ---
        qual_frame = ttk.Frame(main)
        qual_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(qual_frame, text="Quality:").pack(side="left")
        self.quality_var = tk.StringVar(value="default")
        for val, label in [("default", "Default (720p)"), ("1080p", "1080p"), ("best", "Best")]:
            ttk.Radiobutton(qual_frame, text=label, variable=self.quality_var, value=val).pack(side="left", padx=(10, 0))

        # --- Format ---
        fmt_frame = ttk.Frame(main)
        fmt_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(fmt_frame, text="Format:").pack(side="left")
        self.format_var = tk.StringVar(value="video")
        ttk.Radiobutton(fmt_frame, text="Video (MP4)", variable=self.format_var, value="video").pack(side="left", padx=(10, 0))
        ttk.Radiobutton(fmt_frame, text="Audio (MP3)", variable=self.format_var, value="audio").pack(side="left", padx=(10, 0))

        # --- Output directory ---
        dir_frame = ttk.Frame(main)
        dir_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(dir_frame, text="Save to:").pack(side="left")
        self.dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, font=("Segoe UI", 10))
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)
        ttk.Button(dir_frame, text="Browse", command=self.browse_dir).pack(side="left", padx=(6, 0))

        # --- Download button ---
        self.download_btn = ttk.Button(main, text="Download", style="Accent.TButton", command=self.start_download)
        self.download_btn.pack(fill="x", ipady=6, pady=(0, 8))

        # --- Progress ---
        prog_frame = ttk.Frame(main)
        prog_frame.pack(fill="x", pady=(0, 2))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(prog_frame, variable=self.progress_var, maximum=100, style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(side="left", fill="x", expand=True)
        self.progress_label = ttk.Label(prog_frame, text="0%", width=6)
        self.progress_label.pack(side="left", padx=(6, 0))

        # --- Status ---
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main, textvariable=self.status_var, foreground="#a6adc8")
        self.status_label.pack(anchor="w", pady=(0, 4))

        # --- Show Details toggle ---
        self.details_btn = ttk.Button(main, text="Show Details ▼", command=self.toggle_log)
        self.details_btn.pack(anchor="w", pady=(0, 4))

        # --- Log area (hidden by default) ---
        self.log_frame = ttk.Frame(main)
        self.log_text = tk.Text(
            self.log_frame, height=8, bg="#181825", fg="#a6adc8",
            font=("Consolas", 9), wrap="word", state="disabled",
            relief="flat", borderwidth=0
        )
        log_scroll = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    def paste_url(self):
        try:
            self.url_var.set(self.root.clipboard_get())
        except tk.TclError:
            pass

    def browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)

    def toggle_log(self):
        if self.log_visible:
            self.log_frame.pack_forget()
            self.details_btn.configure(text="Show Details ▼")
            self.root.geometry("620x520")
        else:
            self.log_frame.pack(fill="both", expand=True, pady=(4, 0))
            self.details_btn.configure(text="Hide Details ▲")
            self.root.geometry("620x700")
        self.log_visible = not self.log_visible

    def append_log(self, text):
        self.log_lines.append(text)
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def set_status(self, msg, color="#a6adc8"):
        self.status_var.set(msg)
        self.status_label.configure(foreground=color)

    def set_progress(self, pct):
        self.progress_var.set(pct)
        self.progress_label.configure(text=f"{pct:.0f}%")

    def start_download(self):
        if self.downloading:
            return

        if yt_dlp is None:
            messagebox.showerror("Missing Dependency", "yt-dlp is not installed.\nRun: pip install yt-dlp")
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please paste a YouTube URL first.")
            return

        if not re.match(r"https?://(www\.)?(youtube\.com|youtu\.be)/", url):
            messagebox.showwarning("Invalid URL", "That doesn't look like a valid YouTube URL.\nExample: https://www.youtube.com/watch?v=...")
            return

        out_dir = self.dir_var.get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning("Invalid Directory", "Please choose a valid download directory.")
            return

        self.downloading = True
        self.download_btn.configure(state="disabled")
        self.log_lines.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.set_progress(0)
        self.set_status("Starting download...", "#89b4fa")

        thread = threading.Thread(target=self.run_download, args=(url, out_dir), daemon=True)
        thread.start()

    def run_download(self, url, out_dir):
        try:
            quality = self.quality_var.get()
            fmt = self.format_var.get()

            if fmt == "audio":
                format_str = "bestaudio/best"
                opts = {
                    "format": format_str,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                    "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
                    "progress_hooks": [self.progress_hook],
                    "logger": YtLogger(self),
                    "noplaylist": True,
                }
            else:
                format_map = {
                    "default": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                    "best": "bestvideo+bestaudio/best",
                }
                format_str = format_map[quality]
                opts = {
                    "format": format_str,
                    "merge_output_format": "mp4",
                    "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
                    "progress_hooks": [self.progress_hook],
                    "logger": YtLogger(self),
                    "noplaylist": True,
                }

            self.root.after(0, self.append_log, f"Format: {format_str}")
            self.root.after(0, self.append_log, f"Output: {out_dir}")

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            self.root.after(0, self.on_success)

        except Exception as e:
            tb = traceback.format_exc()
            friendly = self.friendly_error(e)
            self.root.after(0, self.on_error, friendly, tb)

    def progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = (downloaded / total) * 100
                speed = d.get("speed")
                eta = d.get("eta")
                speed_str = f" | {speed / 1024 / 1024:.1f} MB/s" if speed else ""
                eta_str = f" | ETA {eta}s" if eta else ""
                self.root.after(0, self.set_progress, pct)
                self.root.after(0, self.set_status, f"Downloading... {pct:.0f}%{speed_str}{eta_str}", "#89b4fa")
            else:
                mb = downloaded / 1024 / 1024
                self.root.after(0, self.set_status, f"Downloading... {mb:.1f} MB", "#89b4fa")
        elif d["status"] == "finished":
            self.root.after(0, self.set_progress, 100)
            self.root.after(0, self.set_status, "Processing...", "#f9e2af")
            self.root.after(0, self.append_log, f"Downloaded: {d.get('filename', '?')}")

    def on_success(self):
        self.downloading = False
        self.download_btn.configure(state="normal")
        self.set_status("Download complete!", "#a6e3a1")
        self.append_log("Done!")

    def on_error(self, friendly, tb):
        self.downloading = False
        self.download_btn.configure(state="normal")
        self.set_progress(0)
        self.set_status(f"Error: {friendly}", "#f38ba8")
        self.append_log(f"--- ERROR ---\n{tb}")
        if not self.log_visible:
            self.toggle_log()

    def friendly_error(self, e):
        msg = str(e).lower()
        if "urlopen" in msg or "connection" in msg or "network" in msg:
            return "Network connection failed. Check your internet."
        if "not a valid url" in msg or "unsupported url" in msg:
            return "This URL is not supported."
        if "video unavailable" in msg or "private" in msg:
            return "This video is unavailable or private."
        if "ffmpeg" in msg or "ffprobe" in msg:
            return "FFmpeg not found. Install FFmpeg to merge/convert media."
        if "age" in msg:
            return "Age-restricted video. Cannot download."
        return "Something went wrong. See details below."


class YtLogger:
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        if msg.startswith("[debug]"):
            return
        self.app.root.after(0, self.app.append_log, msg)

    def info(self, msg):
        self.app.root.after(0, self.app.append_log, msg)

    def warning(self, msg):
        self.app.root.after(0, self.app.append_log, f"WARN: {msg}")

    def error(self, msg):
        self.app.root.after(0, self.app.append_log, f"ERROR: {msg}")


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
