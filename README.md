# TonieToolbox
### WIP - Work in Progress
Happy Testing :-P

A Python tool for converting audio files to Tonie box compatible format (TAF - Tonie Audio Format).

# Beginners Guide
- [HOWTO](HOWTO.md)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Install from PyPI (Recommended)](#install-from-pypi-recommended)
  - [Install from Source](#install-from-source)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Advanced Options](#advanced-options)
  - [Common Usage Examples](#common-usage-examples)
  - [Media Tags](#media-tags)
  - [TeddyCloud Upload](#teddycloud-upload)
- [Technical Details](#technical-details)
  - [TAF File Structure](#taf-tonie-audio-format-file-structure)
  - [File Analysis](#file-analysis)
  - [File Comparison](#file-comparison)
- [Related Projects](#related-projects)
- [Contributing](#contributing)
- [Legal Notice](#legal-notice)

## Overview

TonieToolbox allows you to create custom audio content for Tonie boxes by converting various audio formats into the specific file format required by Tonie devices.

## Features

The tool provides several capabilities:

- Convert single or multiple audio files into a Tonie-compatible format
- Process complex folder structures recursively to handle entire audio collections
- Analyze and validate existing Tonie files
- Split Tonie files into individual opus tracks
- Compare two TAF files for debugging differences
- Support various input formats through FFmpeg conversion
- Extract and use audio media tags (ID3, Vorbis Comments, etc.) for better file naming
- Upload Tonie files directly to a TeddyCloud server
- Automatically upload cover artwork alongside Tonie files

## Requirements

- Python 3.6 or higher
- FFmpeg (for converting non-opus audio files)
- opus-tools (specifically `opusenc` for encoding to opus format)
- mutagen (for reading audio file metadata, auto-installed when needed)

Make sure FFmpeg and opus-tools are installed on your system and accessible in your PATH.
If the requirements are not found in PATH. TonieToolbox will download the missing requirements with --auto-download.

## Installation

### Install from PyPI (Recommended)

```
pip install tonietoolbox
```

This will install TonieToolbox and its dependencies, making the `tonietoolbox` command available in your terminal.

### Install from Source

```
# Clone the repository
git clone https://github.com/Quentendo64/TonieToolbox.git
cd TonieToolbox

# Install dependencies
pip install protobuf
```

## Usage

### Basic Usage

**Convert a single audio file to Tonie format:**

If installed via pip:
```
tonietoolbox input.mp3
```

If installed from source:
```
python TonieToolbox.py input.mp3
```

This will create a file named `input.taf` in the `.\output` directory.

**Specify output filename:**

```
tonietoolbox input.mp3 my_tonie.taf
```

This will create a file named `my_tonie.taf` in the `.\output` directory.

**Convert multiple files:**

You can specify a directory to convert all audio files within it:

```
tonietoolbox input_directory/
```

Or use a list file (.lst) containing paths to multiple audio files:

```
tonietoolbox playlist.lst
```

**Process folders recursively:**

To process an entire folder structure with multiple audio folders:

```
tonietoolbox --recursive "Music/Albums"
```

This will scan all subfolders, identify those containing audio files, and create a TAF file for each folder.

By default, all generated TAF files are saved in the `.\output` directory. If you want to save each TAF file in its source directory instead:

```
tonietoolbox --recursive --output-to-source "Music/Albums"
```

### Advanced Options

Run the following command to see all available options:

```
tonietoolbox -h
```

Output:
```
usage: TonieToolbox.py [-h] [-v] [--upload URL] [--include-artwork] [--get-tags URL] 
                    [--ignore-ssl-verify] [--special-folder FOLDER] [--path PATH]
                    [--show-progress] [--connection-timeout SECONDS]
                    [--read-timeout SECONDS] [--max-retries RETRIES]
                    [--retry-delay SECONDS] [-t TIMESTAMP] [-f FFMPEG] [-o OPUSENC]
                    [-b BITRATE] [-c] [-a TAG] [-n] [-i] [-s] [-r] [-O]
                    [-A] [-k] [-C FILE2] [-D] [-m] [--name-template TEMPLATE]
                    [--show-tags] [-d] [-T] [-q] [-Q]
                    SOURCE [TARGET]

Create Tonie compatible file from Ogg opus file(s).

positional arguments:
  SOURCE                input file or directory or a file list (.lst)
  TARGET                the output file name (default: ---ID---)

TeddyCloud Options:
  --upload URL          Upload to TeddyCloud instance (e.g., https://teddycloud.example.com). Supports .taf, .jpg, .jpeg, .png files.
  --include-artwork     Upload cover artwork image alongside the Tonie file when using --upload
  --get-tags URL        Get available tags from TeddyCloud instance
  --ignore-ssl-verify   Ignore SSL certificate verification (for self-signed certificates)
  --special-folder FOLDER
                        Special folder to upload to (currently only "library" is supported)
  --path PATH           Path where to write the file on TeddyCloud server
  --show-progress       Show progress bar during file upload (default: enabled)
  --connection-timeout SECONDS
                        Connection timeout in seconds (default: 10)
  --read-timeout SECONDS
                        Read timeout in seconds (default: 300)
  --max-retries RETRIES
                        Maximum number of retry attempts (default: 3)
  --retry-delay SECONDS
                        Delay between retry attempts in seconds (default: 5)

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program version and exit
  -t, --timestamp TIMESTAMP
                        set custom timestamp / bitstream serial / reference .taf file
  -f, --ffmpeg FFMPEG   specify location of ffmpeg
  -o, --opusenc OPUSENC specify location of opusenc
  -b, --bitrate BITRATE set encoding bitrate in kbps (default: 96)
  -c, --cbr             encode in cbr mode
  -a, --append-tonie-tag TAG
                        append [TAG] to filename (must be an 8-character hex value)
  -n, --no-tonie-header do not write Tonie header
  -i, --info            Check and display info about Tonie file
  -s, --split           Split Tonie file into opus tracks
  -r, --recursive       Process folders recursively
  -O, --output-to-source
                        Save output files in the source directory instead of output directory
  -A, --auto-download   Automatically download FFmpeg and opusenc if needed
  -k, --keep-temp       Keep temporary opus files in a temp folder for testing
  -C, --compare FILE2   Compare input file with another .taf file for debugging
  -D, --detailed-compare
                        Show detailed OGG page differences when comparing files

Media Tag Options:
  -m, --use-media-tags  Use media tags from audio files for naming
  --name-template TEMPLATE
                        Template for naming files using media tags. Example: "{album} - {artist}"
  --show-tags           Show available media tags from input files

Version Check Options:
  -S, --skip-update-check
                        Skip checking for updates
  -F, --force-refresh-cache
                        Force refresh of update information from PyPI
  -X, --clear-version-cache
                        Clear cached version information

Logging Options:
  -d, --debug           Enable debug logging
  -T, --trace           Enable trace logging (very verbose)
  -q, --quiet           Show only warnings and errors
  -Q, --silent          Show only errors
```

### Common Usage Examples

#### Analyze a Tonie file:

```
tonietoolbox --info my_tonie.taf
```

#### Split a Tonie file into individual opus tracks:

```
tonietoolbox --split my_tonie.taf 
```

#### Compare TAF files:

Compare two TAF files for debugging purposes:

```
tonietoolbox file1.taf --compare file2.taf
```

For detailed comparison including OGG page differences:

```
tonietoolbox file1.taf --compare file2.taf --detailed-compare
```

#### Custom timestamp options:

```
tonietoolbox input.mp3 --timestamp 1745078762  # UNIX Timestamp
tonietoolbox input.mp3 --timestamp 0x6803C9EA  # Bitstream time
tonietoolbox input.mp3 --timestamp ./reference.taf  # Reference TAF for extraction
```

#### Set custom bitrate:

```
tonietoolbox input.mp3 --bitrate 128
```

#### Process a complex folder structure:

Process an audiobook series with multiple folders:

```
tonietoolbox --recursive "\Hörspiele\Die drei Fragezeichen\Folgen"
```

Process a music collection with nested album folders and save TAF files alongside the source directories:

```
tonietoolbox --recursive --output-to-source "\Hörspiele\"
```

### Media Tags

TonieToolbox can read metadata tags from audio files (such as ID3 tags in MP3 files, Vorbis comments in FLAC/OGG files, etc.) and use them to create more meaningful filenames or display information about your audio collection.

#### View available tags in audio files:

To see what tags are available in your audio files:

```
tonietoolbox --show-tags input.mp3
```

This will display all readable tags from the file, which can be useful for creating naming templates.

#### Use media tags for file naming:

To use the metadata from audio files when generating output filenames:

```
tonietoolbox input.mp3 --use-media-tags
```

For single files, this will use a default template of "{title} - {artist}" for the output filename.

#### Custom naming templates:

You can specify custom templates for generating filenames based on the audio metadata:

```
tonietoolbox input.mp3 --use-media-tags --name-template "{artist} - {album} - {title}"
```

#### Recursive processing with media tags:

When processing folders recursively, media tags can provide more consistent naming:

```
tonietoolbox --recursive --use-media-tags "Music/Collection/"
```

This will attempt to use the album information from the audio files for naming the output files:

```
tonietoolbox --recursive --use-media-tags --name-template "{date} - {album} ({artist})" "Music/Collection/"
```

### TeddyCloud Upload

TonieToolbox can upload files directly to a TeddyCloud server, which is an alternative to the official Tonie cloud for managing custom Tonies.

#### Upload a Tonie file to TeddyCloud:

```
tonietoolbox --upload https://teddycloud.example.com my_tonie.taf
```

This will upload the specified Tonie file to the TeddyCloud server.

#### Upload a newly created Tonie file:

You can combine conversion and upload in a single command:

```
tonietoolbox input.mp3 --upload https://teddycloud.example.com
```

This will convert the input file to TAF format and then upload it to the TeddyCloud server.

#### Upload with custom path:

```
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --path "/custom_audio"
The path needs to be existing in the TeddyCloud Library.
```

#### Upload with artwork:

TonieToolbox can automatically find and upload cover artwork alongside your Tonie files:

```
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --include-artwork
```

This will:
1. Look for cover images (like "cover.jpg", "artwork.png", etc.) in the source directory
2. If no cover image is found, attempt to extract embedded artwork from the audio files
3. Upload the artwork to the "/custom_img" directory on the TeddyCloud server
4. The artwork will be uploaded with the same filename as the Tonie file for easier association

#### Recursive processing with uploads:

```
tonietoolbox --recursive "Music/Albums" --upload https://teddycloud.example.com --include-artwork
```

This will process all folders recursively, create TAF files, and upload both the TAF files and their cover artwork to the TeddyCloud server.

#### Upload with SSL certificate verification disabled:

```
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --ignore-ssl-verify
```

Use this option if the TeddyCloud server uses a self-signed certificate.

## Technical Details

### TAF (Tonie Audio Format) File Structure

The Tonie Audio Format (TAF) consists of several parts:

#### 1. Tonie Header (0x1000 bytes)

Located at the beginning of the file, structured as:

- A 4-byte big-endian integer specifying the header length
- A Protocol Buffer encoded header (defined in `tonie_header.proto`)
- Padding to fill the entire 4096 bytes (0x1000)

The Protocol Buffer structure contains:
```protobuf
message TonieHeader {
  bytes dataHash = 1;      // SHA1 hash of the audio data
  uint32 dataLength = 2;   // Length of the audio data in bytes
  uint32 timestamp = 3;    // Unix timestamp (also used as bitstream serial number)
  repeated uint32 chapterPages = 4 [packed=true];  // Page numbers for chapter starts
  bytes padding = 5;       // Padding to fill up the header
}
```

#### 2. Audio Data

The audio data consists of:
- Opus encoded audio in Ogg container format
- Every page after the header has a fixed size of 4096 bytes (0x1000)
- First page contains the Opus identification header
- Second page contains the Opus comments/tags
- Remaining pages contain the actual audio data
- All pages use the same bitstream serial number (timestamp from header)

#### 3. Special Requirements

For optimal compatibility with Tonie boxes:
- Audio must be stereo (2 channels)
- Sample rate must be 48 kHz
- Pages must be aligned to 4096 byte boundaries
- Bitrate of 96 kbps VBR is recommended

### File Analysis

When using the `--info` flag, TonieToolbox checks and displays detailed information about a .TAF (Tonie Audio File):

- SHA1 hash validation
- Timestamp/bitstream serial consistency
- Opus data length verification
- Opus header validation (version, channels, sample rate)
- Page alignment and size validation
- Total runtime
- Track listing with durations

### File Comparison

When using the `--compare` flag, TonieToolbox provides a detailed comparison of two .TAF files:

- File size comparison
- Header size verification
- Timestamp comparison
- Data length validation
- SHA1 hash verification
- Chapter page structure analysis
- OGG page-by-page comparison (with `--detailed-compare` flag)

This is particularly useful for debugging when creating TAF files with different tools or parameters.

## Related Projects

This project is inspired by and builds upon the work of other Tonie-related open source projects:

- [opus2tonie](https://github.com/bailli/opus2tonie) - A command line utility to convert opus files to the Tonie audio format
- [teddycloud](https://github.com/toniebox-reverse-engineering/teddycloud) - Self-hosted alternative to the Tonie cloud for managing custom Tonies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Legal Notice

This project is an independent, community-driven effort created for educational and personal use purposes.

- tonies®, toniebox®, Hörfigur® are registered trademarks of [tonies GmbH](https://tonies.com).
- This project is not affiliated with, endorsed by, or connected to tonies GmbH in any way.
- TonieToolbox is provided "as is" without warranty of any kind, either express or implied.
- Users are responsible for ensuring their usage complies with all applicable copyright and intellectual property laws.
- This tool is intended for personal use with legally owned content only.

By using TonieToolbox, you acknowledge that the authors of this software take no responsibility for any potential misuse or any damages that might result from the use of this software.