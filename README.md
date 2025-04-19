# TonieToolbox
### WIP - Work in Progress
Happy Testing :-P

A Python tool for converting audio files to Tonie box compatible format (TAF - Tonie Audio Format).


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
- [Technical Details](#technical-details)
  - [TAF File Structure](#taf-tonie-audio-format-file-structure)
  - [File Analysis](#file-analysis)
  - [File Comparison](#file-comparison)
- [Related Projects](#related-projects)
- [Contributing](#contributing)

## Overview

TonieToolbox allows you to create custom audio content for Tonie boxes by converting various audio formats into the specific file format required by Tonie devices.

## Features

The tool provides several capabilities:

- Convert single or multiple audio files into a Tonie-compatible format
- Analyze and validate existing Tonie files
- Split Tonie files into individual opus tracks
- Compare two TAF files for debugging differences
- Support various input formats through FFmpeg conversion

## Requirements

- Python 3.6 or higher
- FFmpeg (for converting non-opus audio files).
- opus-tools (specifically `opusenc` for encoding to opus format)

Make sure FFmpeg and opus-tools are installed on your system and accessible in your PATH.
If the requirements are not found in PATH. TonieToolbox will download the missing requirements.

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

### Advanced Options

Run the following command to see all available options:

```
tonietoolbox --help
```

Output:
```
usage: TonieToolbox.py [-h] [--ts TIMESTAMP] [--ffmpeg FFMPEG] [--opusenc OPUSENC] 
                    [--bitrate BITRATE] [--cbr] [--append-tonie-tag TAG] 
                    [--no-tonie-header] [--info] [--split] [--recursive] [--compare FILE2]
                    [--detailed-compare] [--debug] [--trace] [--quiet] [--silent]
                    SOURCE [TARGET]

Create Tonie compatible file from Ogg opus file(s).

positional arguments:
  SOURCE                input file or directory or a file list (.lst)
  TARGET                the output file name (default: ---ID---)

optional arguments:
  -h, --help            show this help message and exit
  --ts TIMESTAMP        set custom timestamp / bitstream serial / reference .taf file
  --ffmpeg FFMPEG       specify location of ffmpeg
  --opusenc OPUSENC     specify location of opusenc
  --bitrate BITRATE     set encoding bitrate in kbps (default: 96)
  --cbr                 encode in cbr mode
  --append-tonie-tag TAG append [TAG] to filename (must be an 8-character hex value)
  --no-tonie-header     do not write Tonie header
  --info                Check and display info about Tonie file
  --split               Split Tonie file into opus tracks
  --compare FILE2       Compare input file with another .taf file for debugging
  --detailed-compare    Show detailed OGG page differences when comparing files

Logging Options:
  --debug               Enable debug logging
  --trace               Enable trace logging (very verbose)
  --quiet               Show only warnings and errors
  --silent              Show only errors
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
tonietoolbox input.mp3 --ts 1745078762  # UNIX Timestamp
tonietoolbox input.mp3 --ts 0x6803C9EA  # Bitstream time
tonietoolbox input.mp3 --ts ./reference.taf  # Reference TAF for extraction
```

#### Set custom bitrate:

```
tonietoolbox input.mp3 --bitrate 128
```

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