# YT-DLP GUI

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

**A modern, feature-rich YouTube video downloader with a beautiful dark-themed GUI**

</div>

---

## ✨ Features

### 🎬 Download Options
- **Video + Audio** - Download complete videos with audio
- **Video Only** - Download video streams without audio
- **Audio Only** - Extract audio in MP3, M4A, OPUS, or FLAC formats
- **Quality Selection** - Choose from 4K, 1080p, 720p, 480p, 360p
- **Clip Extraction** - Download specific portions of videos

### 🖥️ Dual Interface
- **Normal Mode** - Simple, user-friendly interface for quick downloads
- **Advanced Mode** - Full access to all yt-dlp features:
  - Format & codec selection
  - Clip extraction with time ranges
  - Subtitle downloading & embedding
  - Custom output templates
  - Network & proxy settings
  - Cookie authentication

### 📋 Queue System
- Add multiple videos to download queue
- Batch import URLs from text files
- Pause, resume, and prioritize downloads
- Context menu for quick actions
- Queue persistence across sessions

### 📝 Logging
- Real-time log viewer
- Color-coded log levels
- Log filtering and export
- Debug information for troubleshooting

### 🎨 Modern UI
- Beautiful dark theme (light theme also available)
- Video preview with thumbnails
- Progress indicators
- Keyboard shortcuts

---

## 📦 Installation

### Option 1: Download Release (Recommended)
1. Download the latest release from [Releases](../../releases)
2. Extract the ZIP file
3. Run `yt-dlp-gui.exe`

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/yt-dlp-gui.git
cd yt-dlp-gui

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

---

## 🔧 Requirements

- **yt-dlp** - The core download engine
  - Place `yt-dlp.exe` in the application folder, or
  - Install via pip: `pip install yt-dlp`
  
- **FFmpeg** (Optional but recommended) - For video/audio merging
  - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - Place `ffmpeg.exe` in the `bin/` folder, or
  - Add to system PATH

---

## 🚀 Usage

### Quick Start
1. Launch the application
2. Paste a YouTube URL
3. Click **Fetch** to load video info
4. Select format and quality
5. Click **Download**

### Batch Downloads
1. Import URLs from a text file (File → Import URLs)
2. Or add videos one by one to the queue
3. Click **Start** in the queue panel

### Clip Extraction
1. Switch to **Advanced Mode**
2. Go to the **Clip** tab
3. Enable clip extraction
4. Enter start and end times (HH:MM:SS)
5. Download

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | Toggle Advanced/Normal Mode |
| `Ctrl+L` | Toggle Log Panel |
| `Ctrl+I` | Import URLs |
| `Ctrl+R` | Start Queue |
| `Ctrl+Q` | Exit |

---

## 📁 Project Structure

```
yt-dlp-gui/
├── src/
│   ├── main.py              # Application entry point
│   ├── ui/                  # User interface components
│   │   ├── main_window.py   # Main window
│   │   ├── normal_mode.py   # Simple interface
│   │   ├── advanced_mode.py # Full-featured interface
│   │   ├── queue_panel.py   # Download queue
│   │   ├── log_panel.py     # Log viewer
│   │   └── styles.py        # Themes
│   ├── core/                # Core functionality
│   │   ├── ytdlp_wrapper.py # yt-dlp integration
│   │   ├── downloader.py    # Download manager
│   │   ├── queue_manager.py # Queue handling
│   │   └── config.py        # Settings
│   └── utils/               # Utilities
│       ├── logger.py        # Logging system
│       └── helpers.py       # Helper functions
├── bin/                     # Executables (yt-dlp, ffmpeg)
├── config/                  # User settings
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 🛠️ Building from Source

### Create Executable
```bash
pip install pyinstaller
pyinstaller --name="yt-dlp-gui" --windowed --onedir src/main.py
```

The executable will be created in the `dist/yt-dlp-gui/` folder.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful download engine
- [PySide6](https://www.qt.io/qt-for-python) - Qt for Python
- [FFmpeg](https://ffmpeg.org/) - Media processing

---

## 📞 Support

If you encounter any issues:
1. Check the log panel for error details
2. Ensure yt-dlp is up to date (`yt-dlp -U`)
3. Open an issue with:
   - Error message from logs
   - Video URL (if not private)
   - Your yt-dlp version

---

<div align="center">

**Made with ❤️ for the open-source community**

⭐ Star this repo if you find it useful!

</div>
