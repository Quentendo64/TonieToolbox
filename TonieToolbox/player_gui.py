#!/usr/bin/env python3
"""
GUI Player Module for TonieToolbox

This module provides a minimal tkinter-based GUI for playing TAF (Tonie Audio Format) files.
It wraps the existing TAFPlayer functionality in a user-friendly graphical interface.
"""

import os
import sys
import time
import threading
from typing import Optional, Dict, Any
from pathlib import Path

from .logger import get_logger
from .player import TAFPlayer, TAFPlayerError
from .constants import ICON_BASE64
from . import __version__
from .tonie_analysis import split_to_opus_files, extract_to_mp3_files, extract_full_audio_to_mp3

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    import base64
    import io
    TKINTER_AVAILABLE = True
except ImportError as e:
    TKINTER_AVAILABLE = False
    TKINTER_ERROR = str(e)


logger = get_logger(__name__)


class TAFPlayerGUI:
    """
    A minimal GUI player for TAF files using tkinter.
    
    This player provides a simple graphical interface with basic playback controls,
    progress tracking, and file information display.
    """
    
    def __init__(self):
        """Initialize the GUI player."""
        self.root = tk.Tk()
        self.root.title("🎵 TonieToolbox - TAF Player")        
        optimal_width = 1024
        optimal_height = 1500
        
        self.root.geometry(f"{optimal_width}x{optimal_height}")
        self.root.resizable(True, True)
        self.root.minsize(1024, 768)
        self._center_window(optimal_width, optimal_height)
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        self.colors = {
            'bg_dark': '#2b2b2b',
            'bg_medium': '#3c3c3c', 
            'bg_light': '#4a4a4a',
            'accent': '#ff6b35',
            'accent_hover': '#ff8c5a',
            'text_light': '#ffffff',
            'text_medium': '#cccccc',
            'success': '#4ade80',
            'warning': '#fbbf24',
            'error': '#f87171'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])    
        self._set_window_icon()
        self._configure_styles()
        self.player: Optional[TAFPlayer] = None
        self.current_file: Optional[Path] = None
        self.is_playing = False
        self.is_paused = False
        self.update_thread: Optional[threading.Thread] = None
        self.stop_updates = threading.Event()
        self.progress_var = tk.DoubleVar()
        self.current_time_var = tk.StringVar(value="00:00")
        self.total_time_var = tk.StringVar(value="00:00")
        self.file_name_var = tk.StringVar(value="No file loaded")
        self.status_var = tk.StringVar(value="🔄 Ready to load TAF file")
        self.selected_input_file: Optional[str] = None
        self._create_widgets()
        self._setup_layout()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info("TAF Player GUI initialized")
    
    def _center_window(self, width: int, height: int):
        """Center the window on the screen."""
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2            
            x = max(0, x)
            y = max(0, y)
            self.root.geometry(f"{width}x{height}+{x}+{y}")            
            logger.debug(f"Window centered at {x},{y} with size {width}x{height}")
            
        except Exception as e:
            logger.debug(f"Could not center window: {e}")
    
    def _configure_styles(self):
        """Configure modern dark theme styles for ttk widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', 
                       background=self.colors['bg_dark'],
                       borderwidth=0)        
        style.configure('Dark.TLabelframe', 
                       background=self.colors['bg_medium'],
                       borderwidth=2,
                       relief='raised')
        style.configure('Dark.TLabelframe.Label',
                       background=self.colors['bg_medium'],
                       foreground=self.colors['text_light'],
                       font=('Arial', 11, 'bold'))    
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['text_light'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10),
                       font=('Arial', 10, 'bold'))
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent'])])
        style.configure('Large.TButton',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_light'],
                       borderwidth=1,
                       relief='raised',
                       focuscolor='none',
                       padding=(25, 15),
                       font=('Arial', 12, 'bold'))
        style.map('Large.TButton',
                 background=[('active', self.colors['accent']),
                           ('pressed', self.colors['bg_medium']),
                           ('disabled', '#666666')])        
        style.configure('Title.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_light'],
                       font=('Arial', 14, 'bold'))
        style.configure('Text.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_light'])
        style.configure('Info.TLabel',
                       background=self.colors['bg_medium'],
                       foreground='#ffffff',
                       font=('Arial', 10))
        style.configure('Time.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['accent'],
                       font=('Consolas', 11, 'bold'))
        style.configure('Status.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['success'],
                       font=('Arial', 9))    
        style.configure('Title.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_light'],
                       font=('Arial', 32, 'bold'))        
        style.configure('Modern.Horizontal.TScale',
                       background=self.colors['bg_medium'],
                       troughcolor=self.colors['bg_light'],
                       borderwidth=0,
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])     
        style.configure('Dark.TNotebook',
                       background=self.colors['bg_dark'],
                       borderwidth=0)
        style.configure('Dark.TNotebook.Tab',
                       background=self.colors['bg_medium'],
                       foreground=self.colors['text_medium'],
                       padding=(20, 10),
                       font=('Arial', 10, 'bold'))
        style.map('Dark.TNotebook.Tab',
                 background=[('selected', self.colors['bg_light']),
                           ('active', self.colors['accent'])],
                 foreground=[('selected', self.colors['text_light']),
                           ('active', self.colors['text_light'])])
        style.configure('Dark.TRadiobutton',
                       background=self.colors['bg_medium'],
                       foreground=self.colors['text_medium'],
                       font=('Arial', 10),
                       focuscolor='none')
        style.map('Dark.TRadiobutton',
                 background=[('active', self.colors['bg_light'])],
                 foreground=[('active', self.colors['text_light'])])        
        style.configure('Dark.TEntry',
                       background='#2d2d2d',
                       foreground='#ffffff',
                       borderwidth=2,
                       relief='solid',
                       insertcolor='#ffffff',
                       selectbackground=self.colors['accent'],
                       selectforeground='#ffffff')
        style.map('Dark.TEntry',
                 focuscolor=[('focus', self.colors['accent'])],
                 bordercolor=[('focus', self.colors['accent'])])
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_light'],
                       borderwidth=0,
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])
    
    def _set_window_icon(self):
        """Set the window icon using the base64 encoded icon from constants."""
        try:
            icon_data = base64.b64decode(ICON_BASE64)
            logger.debug(f"Decoded icon data: {len(icon_data)} bytes")        
            is_ico = icon_data.startswith(b'\x00\x00\x01\x00')
            success = False
            if is_ico and not success:
                success = self._try_ico_to_png_icon(icon_data)
            if not success:
                success = self._try_photoimage_icon()
            if not success and is_ico:
                success = self._try_iconbitmap_icon(icon_data)
            if success:
                logger.info("Successfully set window icon")
            else:
                logger.debug("Could not set window icon - using system default")
                
        except Exception as e:
            logger.debug(f"Failed to set window icon: {e}")
    
    def _try_photoimage_icon(self):
        """Try setting icon using PhotoImage (for PNG/GIF formats)."""
        try:
            icon_image = tk.PhotoImage(data=ICON_BASE64)
            self.root.iconphoto(True, icon_image)
            logger.debug("Icon set using PhotoImage method")
            return True
        except tk.TclError as e:
            logger.debug(f"PhotoImage method failed: {e}")
            return False
    
    def _try_iconbitmap_icon(self, icon_data):
        """Try setting icon using iconbitmap with temporary file."""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.ico', delete=False) as tmp_file:
                tmp_file.write(icon_data)
                tmp_file.flush()
                self.root.iconbitmap(tmp_file.name)
                logger.debug("Icon set using iconbitmap method")
                os.unlink(tmp_file.name)
                return True
        except Exception as e:
            logger.debug(f"iconbitmap method failed: {e}")
            return False
    
    def _try_ico_to_png_icon(self, icon_data):
        """Try extracting PNG from ICO and setting as PhotoImage."""
        try:
            png_start = icon_data.find(b'\x89PNG\r\n\x1a\n')
            if png_start > 0:
                png_data = icon_data[png_start:]
                png_end = png_data.find(b'IEND') + 8
                if png_end > 8:
                    png_data = png_data[:png_end]
                    png_b64 = base64.b64encode(png_data).decode('ascii')
                    icon_image = tk.PhotoImage(data=png_b64)
                    self.root.iconphoto(True, icon_image)
                    logger.debug("Icon set using PNG extraction from ICO")
                    return True
        except Exception as e:
            logger.debug(f"ICO to PNG extraction failed: {e}")
        return False
    
    def _create_widgets(self):
        """Create all GUI widgets with modern styling and tabbed interface."""
        self.main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20")
        self.header_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.title_label = ttk.Label(
            self.header_frame, 
            text="🎵 TonieToolbox TAF Player",
            style='Text.TLabel'
        )
        
        self.notebook = ttk.Notebook(self.main_frame, style='Dark.TNotebook')
        
        self._create_player_tab()
        self._create_tools_tab()
        self._create_about_tab()
    
    def _create_player_tab(self):
        """Create the main player tab with all playback controls."""
        self.player_tab = ttk.Frame(self.notebook, style='Dark.TFrame', padding="15")
        
        self.file_frame = ttk.LabelFrame(
            self.player_tab, 
            text="📁 Audio File",
            style='Dark.TLabelframe',
            padding="20"
        )    
        self.file_display_frame = ttk.Frame(self.file_frame, style='Dark.TFrame')
        self.file_icon_label = ttk.Label(
            self.file_display_frame,
            text="🎵",
            style='Text.TLabel'
        )
        self.file_label = ttk.Label(
            self.file_display_frame,
            textvariable=self.file_name_var,
            style='Text.TLabel'
        )    
        self.load_button = ttk.Button(
            self.file_frame,
            text="📂 Load TAF File",
            command=self._load_file,
            style='Accent.TButton'
        )
        self.details_frame = ttk.Frame(self.file_frame, style='Dark.TFrame')
        self.details_text = tk.Text(
            self.details_frame,
            height=10,
            width=90,
            state=tk.DISABLED,
            wrap=tk.WORD,
            bg=self.colors['bg_light'],
            fg=self.colors['text_medium'],
            font=('Consolas', 10),
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=10
        )
        self.details_scrollbar = ttk.Scrollbar(
            self.details_frame,
            orient=tk.VERTICAL,
            command=self.details_text.yview
        )
        self.details_text.config(yscrollcommand=self.details_scrollbar.set)    
        self.controls_frame = ttk.LabelFrame(
            self.player_tab,
            text="🎮 Player Controls",
            style='Dark.TLabelframe',
            padding="20"
        )
        self.button_frame = ttk.Frame(self.controls_frame, style='Dark.TFrame')
        self.play_button = ttk.Button(
            self.button_frame,
            text="▶️ Play",
            command=self._toggle_play,
            state=tk.DISABLED,
            style='Large.TButton'
        )
        self.stop_button = ttk.Button(
            self.button_frame,
            text="⏹️ Stop",
            command=self._stop_playback,
            state=tk.DISABLED,
            style='Large.TButton'
        )        
        self.chapter_frame = ttk.Frame(self.controls_frame, style='Dark.TFrame')
        self.prev_chapter_button = ttk.Button(
            self.chapter_frame,
            text="⏮️ Previous",
            command=self._prev_chapter,
            state=tk.DISABLED,
            style='Accent.TButton'
        )
        self.next_chapter_button = ttk.Button(
            self.chapter_frame,
            text="⏭️ Next",
            command=self._next_chapter,
            state=tk.DISABLED,
            style='Accent.TButton'
        )
        self.progress_section = ttk.Frame(self.controls_frame, style='Dark.TFrame')
        self.time_frame = ttk.Frame(self.progress_section, style='Dark.TFrame')
        self.current_time_label = ttk.Label(
            self.time_frame,
            textvariable=self.current_time_var,
            style='Time.TLabel'
        )
        self.time_separator = ttk.Label(
            self.time_frame,
            text=" / ",
            style='Time.TLabel'
        )
        self.total_time_label = ttk.Label(
            self.time_frame,
            textvariable=self.total_time_var,
            style='Time.TLabel'
        )        
        self.progress_bar = ttk.Scale(
            self.progress_section,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            command=self._on_seek,
            style='Modern.Horizontal.TScale',
            length=800
        )
        self.status_frame = ttk.Frame(self.player_tab, style='Dark.TFrame')
        self.status_icon = ttk.Label(
            self.status_frame,
            text="ℹ️",
            style='Status.TLabel'
        )
        self.status_label = ttk.Label(
            self.status_frame,
            textvariable=self.status_var,
            style='Status.TLabel'
        )
        self.notebook.add(self.player_tab, text='🎵  Player')
    
    def _create_about_tab(self):
        """Create the About tab with TonieToolbox information."""
        self.about_tab = ttk.Frame(self.notebook, style='Dark.TFrame', padding="15")
        self.notebook.add(self.about_tab, text='ℹ️  About')
        self.about_container = ttk.Frame(self.about_tab, style='Dark.TFrame')
        self.about_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        self.about_title = ttk.Label(
            self.about_container,
            text="TonieToolbox",
            style='Title.TLabel',
            font=('Arial', 32, 'bold')
        )
        self.logo_frame = ttk.Frame(self.about_container, style='Dark.TFrame')
        try:
            icon_data = base64.b64decode(ICON_BASE64)
            logo_image = None
            try:
                logo_image = tk.PhotoImage(data=ICON_BASE64)
                logo_image = logo_image.subsample(2, 2)
            except tk.TclError:
                png_start = icon_data.find(b'\x89PNG\r\n\x1a\n')
                if png_start > 0:
                    png_data = icon_data[png_start:]
                    png_end = png_data.find(b'IEND') + 8
                    if png_end > 8:
                        png_data = png_data[:png_end]
                        png_b64 = base64.b64encode(png_data).decode('ascii')
                        logo_image = tk.PhotoImage(data=png_b64)
                        logo_image = logo_image.subsample(2, 2)
            
            if logo_image:
                self.logo_label = ttk.Label(
                    self.logo_frame,
                    image=logo_image,
                    style='Text.TLabel'
                )
                self.logo_label.image = logo_image
            else:
                self.logo_label = ttk.Label(
                    self.logo_frame,
                    text="🦜",
                    style='Text.TLabel',
                    font=('Arial', 48)
                )
                
        except Exception as e:
            logger.debug(f"Failed to load logo: {e}")
            self.logo_label = ttk.Label(
                self.logo_frame,
                text="🦜",
                style='Text.TLabel',
                font=('Arial', 48)
            )
        
        self.version_frame = ttk.Frame(self.about_container, style='Dark.TFrame')
        self.version_label = ttk.Label(
            self.version_frame,
            text=f"📋 Version: {__version__}",
            style='Text.TLabel',
            font=('Arial', 14)
        )
        self.author_frame = ttk.Frame(self.about_container, style='Dark.TFrame')
        self.author_label = ttk.Label(
            self.author_frame,
            text="👨‍💻 Author: Quentendo64",
            style='Text.TLabel',
            font=('Arial', 14)
        )
        self.desc_frame = ttk.Frame(self.about_container, style='Dark.TFrame')
        description_text = (
            "A comprehensive tool for working with Tonie audio files (TAF).\n"
            "Features audio playback, file analysis, and media conversion."
        )
        self.desc_label = ttk.Label(
            self.desc_frame,
            text=description_text,
            style='Text.TLabel',
            font=('Arial', 12),
            justify=tk.CENTER,
            wraplength=600
        )
        self.repo_frame = ttk.Frame(self.about_container, style='Dark.TFrame')
        self.repo_label = ttk.Label(
            self.repo_frame,
            text="🔗 Repository:",
            style='Text.TLabel',
            font=('Arial', 14)
        )
        self.repo_button = ttk.Button(
            self.repo_frame,
            text="🌐 GitHub Repository",
            command=self._open_repository,
            style='Accent.TButton'
        )
        self.pypi_button = ttk.Button(
            self.repo_frame,
            text="📦 PyPI Page",
            command=self._open_pypi,
            style='Accent.TButton'
        )
        self.license_frame = ttk.Frame(self.about_container, style='Dark.TFrame')
        self.license_label = ttk.Label(
            self.license_frame,
            text="📄 Licensed under GPL3 - see repository for details",
            style='Text.TLabel',
            font=('Arial', 10),
            foreground=self.colors['text_medium']
        )    
        self.attribution_frame = ttk.Frame(self.about_container, style='Dark.TFrame')
        self.attribution_label = ttk.Label(
            self.attribution_frame,
            text="Parrot Icon created by Freepik - Flaticon",
            style='Title.TLabel',
            font=('Arial', 8),
            foreground=self.colors['text_medium']
        )
        self.attribution_button = ttk.Button(
            self.attribution_frame,
            text="🎨 Icon Attribution",
            command=self._open_attribution_link,
            style='Accent.TButton'
        )
        self.about_title.pack(pady=(0, 20))
        self.logo_frame.pack(pady=(0, 30))
        self.logo_label.pack()
        
        self.version_frame.pack(pady=10, fill=tk.X)
        self.version_label.pack()
        
        self.author_frame.pack(pady=10, fill=tk.X)
        self.author_label.pack()
        
        self.desc_frame.pack(pady=20, fill=tk.X)
        self.desc_label.pack()
        
        self.repo_frame.pack(pady=20, fill=tk.X)
        self.repo_label.pack(pady=(0, 10))
        self.repo_button.pack(pady=10)
        self.pypi_button.pack(pady=10)    
        self.license_frame.pack(pady=30, fill=tk.X)
        self.license_label.pack()
        self.attribution_frame.pack(pady=20, fill=tk.X)
        self.attribution_label.pack(pady=(0, 5))
        self.attribution_button.pack()
    
    def _open_repository(self):
        """Open the TonieToolbox repository in web browser."""
        import webbrowser
        try:
            webbrowser.open('https://github.com/Quentendo64/TonieToolbox')
            self.status_var.set("🌐 Opening repository in browser...")
        except Exception as e:
            self.status_var.set(f"❌ Could not open browser: {str(e)}")
    def _open_pypi(self):
        """Open the PyPI page for TonieToolbox in web browser."""
        import webbrowser
        try:
            webbrowser.open('https://pypi.org/project/TonieToolbox/')
            self.status_var.set("🌐 Opening PyPI page in browser...")
        except Exception as e:
            self.status_var.set(f"❌ Could not open browser: {str(e)}")                
    
    def _open_attribution_link(self):
        """Open the Flaticon attribution page in web browser."""
        import webbrowser
        try:
            webbrowser.open('https://www.flaticon.com/free-animated-icons/parrot')
            self.status_var.set("🎨 Opening icon attribution page...")
        except Exception as e:
            self.status_var.set(f"❌ Could not open browser: {str(e)}")
    
    def _create_tools_tab(self):
        """Create the Tools tab with conversion and utility functions."""
        self.tools_tab = ttk.Frame(self.notebook, style='Dark.TFrame', padding="15")
        self.notebook.add(self.tools_tab, text='🔧  Tools')
        self.tools_container = ttk.Frame(self.tools_tab, style='Dark.TFrame')
        self.tools_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.tools_notebook = ttk.Notebook(self.tools_container, style='Dark.TNotebook')
        self.tools_notebook.pack(fill=tk.BOTH, expand=True)
        self._create_convert_tab()
        self._create_analyze_tab()
        if hasattr(self, 'selected_input_file') and self.selected_input_file:
            self._analyze_selected_file()
    
    def _create_convert_tab(self):
        """Create the Convert sub-tab with conversion options."""
        self.convert_tab = ttk.Frame(self.tools_notebook, style='Dark.TFrame', padding="20")
        self.tools_notebook.add(self.convert_tab, text='🔄  Convert')
        self.input_section = ttk.LabelFrame(
            self.convert_tab,
            text="📁 Input File",
            style='Dark.TLabelframe',
            padding="15"
        )
        self.input_section.pack(fill=tk.X, pady=(0, 15))
        self.input_file_frame = ttk.Frame(self.input_section, style='Dark.TFrame')
        self.input_file_frame.pack(fill=tk.X, pady=(0, 10))        
        self.input_file_var = tk.StringVar()        
        if self.current_file:
            self.input_file_var.set(self.current_file.name)
            self.selected_input_file = str(self.current_file)
        else:
            self.input_file_var.set("No file selected")
        self.input_file_label = ttk.Label(
            self.input_file_frame,
            textvariable=self.input_file_var,
            style='Info.TLabel'
        )
        self.input_file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)        
        self.browse_button = ttk.Button(
            self.input_file_frame,
            text="📂 Browse File",
            command=self._browse_input_file,
            style='Accent.TButton'
        )
        self.browse_button.pack(side=tk.RIGHT, padx=(10, 0))        
        self.convert_options = ttk.LabelFrame(
            self.convert_tab,
            text="⚙️ Conversion Options",
            style='Dark.TLabelframe',
            padding="15"
        )
        self.convert_options.pack(fill=tk.X, pady=(0, 15))    
        self.convert_type_frame = ttk.Frame(self.convert_options, style='Dark.TFrame')
        self.convert_type_frame.pack(fill=tk.X, pady=(0, 15))        
        ttk.Label(
            self.convert_type_frame,
            text="Convert to:",
            style='Text.TLabel'
        ).pack(side=tk.LEFT)
        
        self.convert_type_var = tk.StringVar(value="separate_mp3")        
        self.mp3_separate_radio = ttk.Radiobutton(
            self.convert_type_frame,
            text="🎵 Separate MP3 tracks",
            variable=self.convert_type_var,
            value="separate_mp3",
            style='Dark.TRadiobutton'
        )
        self.mp3_separate_radio.pack(anchor=tk.W, pady=2)        
        self.mp3_single_radio = ttk.Radiobutton(
            self.convert_type_frame,
            text="🎵 Single MP3 file",
            variable=self.convert_type_var,
            value="single_mp3",
            style='Dark.TRadiobutton'
        )
        self.mp3_single_radio.pack(anchor=tk.W, pady=2)        
        self.opus_radio = ttk.Radiobutton(
            self.convert_type_frame,
            text="🎶 Opus tracks",
            variable=self.convert_type_var,
            value="opus",
            style='Dark.TRadiobutton'
        )
        self.opus_radio.pack(anchor=tk.W, pady=2)
        self.output_dir_frame = ttk.Frame(self.convert_options, style='Dark.TFrame')
        self.output_dir_frame.pack(fill=tk.X, pady=(0, 15))        
        ttk.Label(
            self.output_dir_frame,
            text="Output directory:",
            style='Text.TLabel'
        ).pack(anchor=tk.W)
        
        self.output_dir_var = tk.StringVar()
        self.output_dir_var.set(os.path.join(os.getcwd(), "output"))        
        self.output_dir_display_frame = ttk.Frame(self.output_dir_frame, style='Dark.TFrame')
        self.output_dir_display_frame.pack(fill=tk.X, pady=(5, 0))        
        self.output_dir_label = ttk.Label(
            self.output_dir_display_frame,
            textvariable=self.output_dir_var,
            style='Info.TLabel'
        )
        self.output_dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)    
        self.output_browse_button = ttk.Button(
            self.output_dir_display_frame,
            text="📁 Browse Folder",
            command=self._browse_output_dir,
            style='Accent.TButton'
        )
        self.output_browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.convert_action_frame = ttk.Frame(self.convert_options, style='Dark.TFrame')
        self.convert_action_frame.pack(fill=tk.X)
        self.convert_button = ttk.Button(
            self.convert_action_frame,
            text="🔄 Start Conversion",
            command=self._start_conversion,
            style='Large.TButton'
        )
        self.convert_button.pack(pady=10)
        self.convert_progress = ttk.Progressbar(
            self.convert_action_frame,
            mode='indeterminate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.convert_progress.pack(fill=tk.X, pady=(10, 0))
        self.convert_status_var = tk.StringVar()
        self.convert_status_var.set("Ready to convert")
        self.convert_status_label = ttk.Label(
            self.convert_action_frame,
            textvariable=self.convert_status_var,
            style='Status.TLabel'
        )
        self.convert_status_label.pack(pady=(5, 0))
    
    def _create_analyze_tab(self):
        """Create the Analyze sub-tab with file analysis tools."""
        self.analyze_tab = ttk.Frame(self.tools_notebook, style='Dark.TFrame', padding="20")
        self.tools_notebook.add(self.analyze_tab, text='🔍  Analyze')
        self.analyze_info = ttk.LabelFrame(
            self.analyze_tab,
            text="📊 File Analysis",
            style='Dark.TLabelframe',
            padding="15"
        )
        self.analyze_info.pack(fill=tk.BOTH, expand=True)
        self.analyze_text = tk.Text(
            self.analyze_info,
            height=20,
            width=80,
            state=tk.DISABLED,
            wrap=tk.WORD,
            bg=self.colors['bg_light'],
            fg=self.colors['text_medium'],
            font=('Consolas', 10),
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=10
        )        
        self.analyze_scrollbar = ttk.Scrollbar(
            self.analyze_info,
            orient=tk.VERTICAL,
            command=self.analyze_text.yview
        )
        self.analyze_text.config(yscrollcommand=self.analyze_scrollbar.set)
        self.analyze_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.analyze_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._update_analyze_text("Select a TAF file to see detailed analysis information.")
    
    def _browse_input_file(self):
        """Browse for input TAF file."""
        file_path = filedialog.askopenfilename(
            title="Select TAF File for Conversion",
            filetypes=[("TAF files", "*.taf"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        
        if file_path:
            self.input_file_var.set(os.path.basename(file_path))
            self.selected_input_file = file_path
            self._analyze_selected_file()
    
    def _update_tools_input_file(self, file_path: str):
        """Update the Tools tab input file when a file is loaded in the Player tab."""
        if hasattr(self, 'input_file_var') and hasattr(self, 'selected_input_file'):
            self.input_file_var.set(os.path.basename(file_path))
            self.selected_input_file = file_path
            self._analyze_selected_file()
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        dir_path = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get()
        )
        
        if dir_path:
            self.output_dir_var.set(dir_path)
    
    def _start_conversion(self):
        """Start the conversion process in a separate thread."""
        if not hasattr(self, 'selected_input_file'):
            messagebox.showerror("Error", "Please select an input TAF file first.")
            return
        
        if not os.path.exists(self.selected_input_file):
            messagebox.showerror("Error", "Selected input file does not exist.")
            return
        output_dir = self.output_dir_var.get()
        os.makedirs(output_dir, exist_ok=True)
        self.convert_button.config(state=tk.DISABLED)
        self.convert_progress.start()
        self.convert_status_var.set("Converting...")
        threading.Thread(
            target=self._perform_conversion,
            daemon=True
        ).start()
    
    def _perform_conversion(self):
        """Perform the actual conversion."""
        try:
            convert_type = self.convert_type_var.get()
            input_file = self.selected_input_file
            output_dir = self.output_dir_var.get()
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            
            if convert_type == "separate_mp3":
                extract_to_mp3_files(input_file, output_dir)
                self.root.after(0, lambda: self.convert_status_var.set("✅ Converted to separate MP3 files"))
            elif convert_type == "single_mp3":
                output_file = os.path.join(output_dir, f"{base_name}.mp3")
                extract_full_audio_to_mp3(input_file, output_file)
                self.root.after(0, lambda: self.convert_status_var.set("✅ Converted to single MP3 file"))
            elif convert_type == "opus":
                split_to_opus_files(input_file, output_dir)
                self.root.after(0, lambda: self.convert_status_var.set("✅ Converted to Opus files"))
            
        except Exception as e:
            error_msg = f"❌ Conversion failed: {str(e)}"
            self.root.after(0, lambda: self.convert_status_var.set(error_msg))
            logger.error(f"Conversion error: {e}")
        
        finally:
            self.root.after(0, self._conversion_finished)
    
    def _conversion_finished(self):
        """Called when conversion is finished to update UI."""
        self.convert_button.config(state=tk.NORMAL)
        self.convert_progress.stop()
    
    def _analyze_selected_file(self):
        """Analyze the selected file and update the analyze tab."""
        if hasattr(self, 'selected_input_file'):
            try:
                from .tonie_analysis import check_tonie_file                
                file_info = check_tonie_file(self.selected_input_file)                
                analysis_text = f"""File Analysis: {os.path.basename(self.selected_input_file)}
{'='*60}

File Path: {self.selected_input_file}
File Size: {os.path.getsize(self.selected_input_file):,} bytes

{file_info}

Analysis completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                self._update_analyze_text(analysis_text)
                
            except Exception as e:
                error_text = f"""Analysis Error
{'='*60}

Could not analyze file: {self.selected_input_file}
Error: {str(e)}

Please ensure the file is a valid TAF file.
"""
                self._update_analyze_text(error_text)
                logger.error(f"Analysis error: {e}")
    
    def _update_analyze_text(self, text):
        """Update the analyze text widget with new content."""
        self.analyze_text.config(state=tk.NORMAL)
        self.analyze_text.delete(1.0, tk.END)
        self.analyze_text.insert(1.0, text)
        self.analyze_text.config(state=tk.DISABLED)
    
    def _setup_layout(self):
        """Setup the modern layout with tabbed interface."""
        self.main_frame.pack(fill=tk.BOTH, expand=True)    
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        #self.title_label.pack()
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        self._layout_player_tab()
    
    def _layout_player_tab(self):
        """Layout widgets within the player tab."""
        self.file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.file_display_frame.pack(fill=tk.X, pady=(0, 15))
        self.file_icon_label.pack(side=tk.LEFT, padx=(0, 10))
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.load_button.pack(pady=(0, 15))
        self.details_frame.pack(fill=tk.BOTH, expand=True)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.controls_frame.pack(fill=tk.X, pady=(0, 15))
        self.button_frame.pack(pady=(0, 20))
        self.play_button.pack(side=tk.LEFT, padx=(0, 15))
        self.stop_button.pack(side=tk.LEFT)
        # Hide chapter buttons - feature not is implemented yet
        # self.chapter_frame.pack(pady=(0, 20))
        # self.prev_chapter_button.pack(side=tk.LEFT, padx=(0, 15))
        # self.next_chapter_button.pack(side=tk.LEFT)
        self.progress_section.pack(fill=tk.X)
        self.time_frame.pack(pady=(0, 10))
        self.current_time_label.pack(side=tk.LEFT)
        self.time_separator.pack(side=tk.LEFT)
        self.total_time_label.pack(side=tk.LEFT)
        self.progress_bar.pack(fill=tk.X, padx=40)
        self.status_frame.pack(fill=tk.X, pady=(20, 0), padx=10)
        self.status_icon.pack(side=tk.LEFT, padx=(0, 5))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _load_file(self):
        """Load a TAF file using file dialog."""
        file_path = filedialog.askopenfilename(
            title="Select TAF File",
            filetypes=[("TAF files", "*.taf"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        
        if file_path:
            self.load_taf_file(file_path)
    
    def load_taf_file(self, file_path: str):
        """
        Load a TAF file for playback.
        
        Args:
            file_path: Path to the TAF file to load
        """
        try:
            self.status_var.set("📂 Loading TAF file...")
            self.root.update()            
            if self.player:
                self._stop_playback()
                self.player.cleanup()
            self.player = TAFPlayer()
            self.player.load(file_path)
            
            self.current_file = Path(file_path)
            self.file_name_var.set(self.current_file.name)
            self._update_file_info()
            self.play_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            if self.player.taf_info and self.player.taf_info.get('chapters'):
                self.prev_chapter_button.config(state=tk.NORMAL)
                self.next_chapter_button.config(state=tk.NORMAL)
            if self.player.total_duration > 0:
                self.total_time_var.set(self._format_time(self.player.total_duration))
                self.progress_bar.config(to=self.player.total_duration)
            
            self.status_var.set(f"✅ Successfully loaded: {self.current_file.name}")
            logger.info(f"Successfully loaded TAF file: {file_path}")        
            self._update_tools_input_file(file_path)
            
        except TAFPlayerError as e:
            messagebox.showerror("❌ Loading Error", f"Failed to load TAF file:\n\n{e}")
            self.status_var.set("❌ Error loading file")
            logger.error(f"Failed to load TAF file: {e}")
        except Exception as e:
            messagebox.showerror("❌ Unexpected Error", f"An unexpected error occurred:\n\n{e}")
            self.status_var.set("❌ Unexpected error")
            logger.error(f"Unexpected error loading TAF file: {e}")
    
    def _update_file_info(self):
        """Update the file information display with enhanced formatting."""
        if not self.player or not self.player.taf_info:
            return
        
        info = self.player.taf_info    
        info_lines = []
        info_lines.append("📋 FILE INFORMATION")
        info_lines.append("─" * 50)
        
        if 'sha1_hash' in info and info['sha1_hash']:
            info_lines.append(f"🔐 SHA1 Hash: {info['sha1_hash']}")
        
        if 'sample_rate' in info:
            info_lines.append(f"🎵 Sample Rate: {info['sample_rate']:,} Hz")
        
        if 'channels' in info:
            channel_text = "Stereo" if info['channels'] == 2 else f"{info['channels']} Channels"
            info_lines.append(f"🔊 Audio: {channel_text}")
        
        if 'bitrate' in info:
            info_lines.append(f"📊 Bitrate: {info['bitrate']} kbps")
        
        if self.player.total_duration > 0:
            info_lines.append(f"⏱️  Duration: {self._format_time(self.player.total_duration)}")
        
        if 'file_size' in info:
            file_size_mb = info['file_size'] / (1024 * 1024)
            info_lines.append(f"💾 File Size: {file_size_mb:.2f} MB")        
        if 'chapters' in info and info['chapters']:
            info_lines.append("")
            info_lines.append("📚 CHAPTERS")
            info_lines.append("─" * 50)
            info_lines.append(f"Total Chapters: {len(info['chapters'])}")
            info_lines.append("")
            
            for i, chapter in enumerate(info['chapters'][:8]):
                start_time = self._format_time(chapter.get('start', 0))
                title = chapter.get('title', f'Chapter {i+1}')
                info_lines.append(f"  {i+1:2d}. {title:<30} [{start_time}]")
            
            if len(info['chapters']) > 8:
                remaining = len(info['chapters']) - 8
                info_lines.append(f"  ... and {remaining} more chapter{'s' if remaining > 1 else ''}")
        else:
            info_lines.append("")
            info_lines.append("📚 CHAPTERS")
            info_lines.append("─" * 50)
            info_lines.append("No chapter information available")
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, '\n'.join(info_lines))
        self.details_text.config(state=tk.DISABLED)
    
    def _toggle_play(self):
        """Toggle play/pause."""
        if not self.player:
            return
        
        try:
            if not self.is_playing:
                current_pos = self.progress_var.get()
                self.player.play(start_time=current_pos)
                self.is_playing = True
                self.is_paused = False
                self.play_button.config(text="⏸️ Pause")
                self.status_var.set("▶️ Playing audio...")            
                self._start_update_thread()
                
            elif self.is_playing and not self.is_paused:
                self.player.pause()
                self.is_paused = True
                self.play_button.config(text="▶️ Resume")
                self.status_var.set("⏸️ Playback paused")
                
            elif self.is_paused:
                self.player.resume()
                self.is_paused = False
                self.play_button.config(text="⏸️ Pause")
                self.status_var.set("▶️ Playing audio...")
                
        except TAFPlayerError as e:
            messagebox.showerror("🚫 Playback Error", f"Unable to control playback:\n\n{e}")
            self.status_var.set("❌ Playback error occurred")
            logger.error(f"Playback error: {e}")
    
    def _stop_playback(self):
        """Stop playback."""
        if not self.player:
            return
        
        try:
            self.player.stop()
            self.is_playing = False
            self.is_paused = False
            self.play_button.config(text="▶️ Play")
            self.status_var.set("⏹️ Playback stopped")
            self._stop_update_thread()
            self.progress_var.set(0)
            self.current_time_var.set("00:00")
            
        except TAFPlayerError as e:
            logger.error(f"Stop error: {e}")
    
    def _on_seek(self, value):
        """Handle seek bar changes."""
        if not self.player or not self.is_playing:
            return
        
        try:
            seek_time = float(value)
            self.player.seek(seek_time)
        except (TAFPlayerError, ValueError) as e:
            logger.error(f"Seek error: {e}")
    
    def _prev_chapter(self):
        """Go to previous chapter."""
        # Implementation would depend on chapter navigation support in TAFPlayer
        pass
    
    def _next_chapter(self):
        """Go to next chapter."""
        # Implementation would depend on chapter navigation support in TAFPlayer
        pass
    
    def _start_update_thread(self):
        """Start the progress update thread."""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.stop_updates.clear()
        self.update_thread = threading.Thread(target=self._update_progress, daemon=True)
        self.update_thread.start()
    
    def _stop_update_thread(self):
        """Stop the progress update thread."""
        self.stop_updates.set()
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
    
    def _update_progress(self):
        """Update progress bar and time display (runs in separate thread)."""
        while not self.stop_updates.is_set() and self.is_playing:
            try:
                if self.player:
                    status = self.player.get_status()
                    current_time = status.get('current_position', 0)
                    self.root.after(0, self._update_progress_gui, current_time)
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Progress update error: {e}")
                break
    
    def _update_progress_gui(self, current_time: float):
        """Update GUI progress elements (called from main thread)."""
        self.progress_var.set(current_time)
        self.current_time_var.set(self._format_time(current_time))        
        if self.player and current_time >= self.player.total_duration:
            self._stop_playback()
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS or HH:MM:SS format."""
        if seconds < 0:
            return "00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _on_close(self):
        """Handle window close event."""
        try:
            self._stop_playback()
            self._stop_update_thread()
            
            if self.player:
                self.player.cleanup()
                
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            self.root.destroy()
    
    def run(self, taf_file_path: Optional[str] = None):
        """
        Start the GUI player.
        
        Args:
            taf_file_path: Optional path to a TAF file to load on startup
        """
        if taf_file_path:
            self.root.after(100, lambda: self.load_taf_file(taf_file_path))
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("GUI player interrupted by user")
        except Exception as e:
            logger.error(f"GUI player error: {e}")
            raise


def gui_player(taf_file_path: Optional[str] = None) -> None:
    """
    Start the GUI TAF player.
    
    Args:
        taf_file_path: Optional path to the TAF file to play. If None, user can load via dialog.
    """

    if not TKINTER_AVAILABLE:
        print("Error: GUI player requires tkinter, which is not available on this system.")
        print(f"Tkinter error: {TKINTER_ERROR}")
        print("\nTo use the GUI player, you need to install tkinter support:")
        print("  - On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  - On Fedora/RHEL: sudo dnf install tkinter")
        print("  - On Arch Linux: sudo pacman -S tk")
        print("  - On macOS: tkinter should be included with Python")
        print("  - On Windows: tkinter should be included with Python")
        print("\nAlternatively, use the command-line player with: --play")
        return
    
    try:
        logger.info(f"Starting GUI player for: {taf_file_path}")
        if not os.path.exists(taf_file_path):
            print(f"Error: TAF file not found: {taf_file_path}")
            return
        player_gui = TAFPlayerGUI()
        player_gui.run(taf_file_path)
        
    except Exception as e:
        logger.error(f"Failed to start GUI player: {e}")
        print(f"Error starting GUI player: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        gui_player(sys.argv[1])
    else:
        player_gui = TAFPlayerGUI()
        player_gui.run()