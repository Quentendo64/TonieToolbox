# 📚 TonieToolbox for Beginners

Welcome to TonieToolbox! This simple guide will help you create your own custom audio content for Tonie boxes - even if you're not tech-savvy.

## 📋 Table of Contents
- [Before You Begin](#before-you-begin)
- [Installing Python](#installing-python)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Installing TonieToolbox](#installing-tonietoolbox)
- [Quick Start Guide](#quick-start-guide)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## 🚀 Before You Begin

Here's what you'll need:
- A computer running Windows, macOS, or Linux
- Internet connection for installation
- Audio files you want to convert (MP3, FLAC, WAV, etc.)
- About 10-15 minutes of your time

## 💻 Installing Python

TonieToolbox is built with Python, so you'll need to install it first.

### Windows

1. **Download Python**:
   - Go to [python.org/downloads](https://python.org/downloads)
   - Click on the "Download Python" button (get version 3.10 or higher)
   
2. **Install Python**:
   - Open the downloaded file
   - ⚠️ **IMPORTANT**: Check the box that says "Add Python to PATH" ✓
   - Click "Install Now"
   - Wait for the installation to complete

3. **Verify Installation**:
   - Open Command Prompt (search for "cmd" in the Start menu)
   - Type `python --version` and press Enter
   - You should see something like "Python 3.10.x"

### macOS

1. **Download Python**:
   - Go to [python.org/downloads](https://python.org/downloads)
   - Download the macOS installer

2. **Install Python**:
   - Open the downloaded .pkg file
   - Follow the installation instructions
   - Complete the installation

3. **Verify Installation**:
   - Open Terminal (find it in Applications > Utilities > Terminal)
   - Type `python3 --version` and press Enter
   - You should see the Python version number

### Linux

Most Linux distributions come with Python pre-installed. To check:

1. Open Terminal
2. Type `python3 --version` and press Enter

If Python is not installed or you need a newer version:

- **Ubuntu/Debian**: Run `sudo apt update` then `sudo apt install python3 python3-pip`
- **Fedora**: Run `sudo dnf install python3 python3-pip`
- **Arch Linux**: Run `sudo pacman -S python python-pip`

## 📥 Installing TonieToolbox

Once Python is installed, you can install TonieToolbox using pip (Python's package installer):

1. **Open a terminal or command prompt**

2. **Install TonieToolbox**:
   ```
   pip install tonietoolbox
   ```
   
   If that doesn't work, try:
   ```
   pip3 install tonietoolbox
   ```

3. **Verify installation**:
   ```
   tonietoolbox --version
   ```
   You should see the version number of TonieToolbox

## 🎯 Quick Start Guide

Here are the most common ways to use TonieToolbox:

### Converting a Single Audio File

1. **Open a terminal or command prompt**

2. **Navigate to the folder containing your audio file**:
   - Windows: `cd C:\path\to\your\folder`
   - Mac/Linux: `cd /path/to/your/folder`

3. **Convert the file**:
   ```
   tonietoolbox yourfile.mp3
   ```

   This will create a file named `yourfile.taf` in the `output` folder.

### Converting Multiple Audio Files in One Folder

1. **Open a terminal or command prompt**

2. **Navigate to the folder containing your audio folder**:
   - Windows: `cd C:\path\to\your\folder`
   - Mac/Linux: `cd /path/to/your/folder`

3. **Convert all files in the folder**:
   ```
   tonietoolbox subfolder/
   ```

   This will combine all audio files in the folder and create a file named `subfolder.taf` in the `output` folder.

### Converting Multiple Audio Files from Different Locations

1. **Create a new text file** with the extension `.lst` (you can use Notepad or any text editor)

2. **Add the paths** to your audio files in the order you want them on your Tonie, one per line:
   ```
   C:\path\to\track1.mp3
   C:\path\to\track2.mp3
   C:\path\to\track3.mp3
   ```

3. **Save the file** as `playlist.lst`

4. **Convert using the list file**:
   ```
   tonietoolbox playlist.lst
   ```

   This will combine all the listed files into a single TAF file named `playlist.taf`.

## 🛠️ Common Tasks

### Naming Your Output File

To specify the name of your output file:

```
tonietoolbox input.mp3 my_tonie.taf
```

### Using Media Tags for Better Naming

If your audio files have proper tags (artist, album, title), you can use them for naming:

```
tonietoolbox input.mp3 --use-media-tags
```

### Setting a Custom Bit Rate

For higher quality audio (uses more space):

```
tonietoolbox input.mp3 --bitrate 128
```

For lower quality audio (saves space):

```
tonietoolbox input.mp3 --bitrate 64
```

The default is 96 kbps which works well for most content.

### Processing Folders Recursively

To convert multiple folders at once:

```
tonietoolbox --recursive "Music/Collection"
```

### Uploading to TeddyCloud

If you use TeddyCloud instead of the official Tonie cloud:

```
tonietoolbox input.mp3 --upload https://your-teddycloud-server.com
```

### Analyzing a Tonie File

To check if a Tonie file is valid:

```
tonietoolbox --info my_tonie.taf
```

### Splitting a Tonie File

To extract individual tracks from a Tonie file:

```
tonietoolbox --split my_tonie.taf
```

## ❓ Troubleshooting

### Missing FFmpeg or opus-tools

TonieToolbox requires FFmpeg and opus-tools to convert audio files. If you get an error about missing tools:

1. **Use auto-download feature** (easiest option):
   ```
   tonietoolbox input.mp3 --auto-download
   ```
   This will download the required tools automatically.

2. **Or install them manually**:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and [opus-tools.org](https://opus-codec.org/downloads/)
   - **macOS**: Use Homebrew: `brew install ffmpeg opus-tools`
   - **Linux**: Use your package manager, e.g., `sudo apt install ffmpeg opus-tools`

### Common Errors

#### "Command not found"

If you see `tonietoolbox: command not found`, try:
- Using `python -m TonieToolbox` instead
- Making sure Python's scripts folder is in your PATH
- Reinstalling with: `pip install --user tonietoolbox`

#### Audio Quality Issues

If your audio sounds bad:
- Try increasing the bitrate: `tonietoolbox input.mp3 --bitrate 128`
- Make sure your source audio is good quality

#### File Size Too Large

If your TAF file is too big for your Tonie:
- Use a lower bitrate: `tonietoolbox input.mp3 --bitrate 64`
- Shorten your audio files or split into multiple TAF files

### Getting Help

To see all available options:

```
tonietoolbox --help
```

For more detailed information, refer to the [README.md](README.md) file or visit the [GitHub repository](https://github.com/Quentendo64/TonieToolbox).

## 🎉 Congratulations!

You've now learned the basics of TonieToolbox! Enjoy creating custom content for your Tonie boxes.