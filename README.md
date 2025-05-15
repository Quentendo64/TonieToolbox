# TonieToolbox 🎵📦

[![Publish to DockerHub](https://github.com/Quentendo64/TonieToolbox/actions/workflows/publish-to-docker.yml/badge.svg)](https://github.com/Quentendo64/TonieToolbox/actions)
[![Publish to PyPI](https://github.com/Quentendo64/TonieToolbox/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/Quentendo64/TonieToolbox/actions)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/tonietoolbox.svg)](https://badge.fury.io/py/tonietoolbox)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/docker/pulls/quentendo64/tonietoolbox)](https://hub.docker.com/r/quentendo64/tonietoolbox)

A Toolkit for converting various audio formats into the Tonie-compatible TAF format (Tonie Audio Format) and interacting with [TeddyCloud powered by RevvoX](https://github.com/toniebox-reverse-engineering/teddycloud)

## 🚀 Get Started

→ [HOWTO Guide for Beginners](HOWTO.md)  
→ [Contributing Guidelines](CONTRIBUTING.md)

## 🎯 New Features (v0.6.0)

The latest release of TonieToolbox includes exciting new capabilities:

- **Enhanced Media Tag Support**: Better handling of complex audio libraries with advanced metadata extraction and usage of tags in your upload path (--path) or as output directory with the new argument --output-to-template eg. "C:\Music\\{albumartist}\\{album}"
- **Windows Context Menu Integration**: Right-click to convert audio files directly from File Explorer. Use --config-integration to configure the upload functions. If not needed just use --install-integration


## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Install from PyPI (Recommended)](#install-from-pypi-recommended)
  - [Install from Source](#install-from-source)
  - [Using Docker](#using-docker)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Docker Usage](#docker-usage)
  - [Advanced Options](#advanced-options)
  - [Common Usage Examples](#common-usage-examples)
  - [Media Tags](#media-tags)
  - [TeddyCloud Upload](#teddycloud-upload)
  - [Real-World Use Cases](#real-world-use-cases)
- [Technical Details](#technical-details)
  - [TAF File Structure](#taf-tonie-audio-format-file-structure)
  - [File Analysis](#file-analysis)
  - [File Comparison](#file-comparison)
- [Related Projects](#related-projects)
- [Contributing](#contributing)
- [Legal Notice](#legal-notice)
- [Support](#support)

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

***Make sure FFmpeg and opus-tools are installed on your system and accessible in your PATH.***  
If the requirements are not found in PATH, TonieToolbox will download the missing requirements with --auto-download.

## Installation

### Install from PyPI (Recommended)

```shell
pip install tonietoolbox
```

This will install TonieToolbox and its dependencies, making the `tonietoolbox` command available in your terminal.

### Install from Source

```shell
# Clone the repository
git clone https://github.com/Quentendo64/TonieToolbox.git
cd TonieToolbox

# Install dependencies
pip install protobuf
```

### Using Docker

TonieToolbox is available as a Docker image, which comes with all dependencies pre-installed.

#### Pull the Docker Image

```shell
# From Docker Hub
docker pull quentendo64/tonietoolbox:latest

# From GitHub Packages
docker pull ghcr.io/quentendo64/tonietoolbox:latest
```

#### Build the Docker Image Locally

```shell
docker build -t tonietoolbox .
```

Or using docker-compose:

```shell
docker-compose build
```

## Usage

### Basic Usage

**Convert a single audio file to Tonie format:**

If installed via pip:

```shell
tonietoolbox input.mp3
```

If installed from source:

```shell
python TonieToolbox.py input.mp3
```

This will create a file named `input.taf` in the `.\output` directory.

**Specify output filename:**

```shell
tonietoolbox input.mp3 my_tonie.taf
```

This will create a file named `my_tonie.taf` in the `.\output` directory.

**Convert multiple files:**

You can specify a directory to convert all audio files within it:

```shell
tonietoolbox input_directory/
```

Or use a list file (.lst) containing paths to multiple audio files:

```shell
tonietoolbox playlist.lst
```

**Process folders recursively:**

To process an entire folder structure with multiple audio folders:

```shell
tonietoolbox --recursive "Music/Albums"
```

This will scan all subfolders, identify those containing audio files, and create a TAF file for each folder.

By default, all generated TAF files are saved in the `.\output` directory. If you want to save each TAF file in its source directory instead:

```shell
tonietoolbox --recursive --output-to-source "Music/Albums"
```

### Docker Usage

Using TonieToolbox with Docker simplifies the setup process as all dependencies (FFmpeg and opus-tools) are pre-installed.

**Convert a single audio file to Tonie format:**

**On Windows PowerShell/Unix/macOS:**

```bash
docker run --rm -v "$(pwd)/input:/tonietoolbox/input" -v "$(pwd)/output:/tonietoolbox/output" quentendo64/tonietoolbox input/my-audio-file.mp3
```

**On Windows (CMD):**

```cmd
docker run --rm -v "%cd%\input:/tonietoolbox/input" -v "%cd%\output:/tonietoolbox/output" quentendo64/tonietoolbox input/my-audio-file.mp3
```

**Or using docker-compose:**

```shell
docker-compose run --rm tonietoolbox input/my-audio-file.mp3
```

**Process folders recursively:**

```bash
docker run --rm -v "$(pwd)/input:/tonietoolbox/input" -v "$(pwd)/output:/tonietoolbox/output" quentendo64/tonietoolbox --recursive input/folder
```

**Advanced options with Docker:**

```bash
docker run --rm -v "$(pwd)/input:/tonietoolbox/input" -v "$(pwd)/output:/tonietoolbox/output" quentendo64/tonietoolbox --recursive --use-media-tags --name-template "{album} - {artist}" --bitrate 128 input/folder
```

**Upload to TeddyCloud with Docker:**

```bash
docker run --rm -v "$(pwd)/input:/tonietoolbox/input" -v "$(pwd)/output:/tonietoolbox/output" quentendo64/tonietoolbox input/my-audio-file.mp3 --upload https://teddycloud.example.com --include-artwork
```

### Advanced Options

Run the following command to see all available options:

```shell
tonietoolbox -h
```

Output:

```shell
usage: TonieToolbox.py [-h] [-v] [--upload URL] [--include-artwork] [--get-tags URL] 
                    [--ignore-ssl-verify] [--special-folder FOLDER] [--path PATH]
                    [--connection-timeout SECONDS] [--read-timeout SECONDS] 
                    [--max-retries RETRIES] [--retry-delay SECONDS]
                    [--create-custom-json] [--version-2] [--username USERNAME]
                    [--password PASSWORD] [--client-cert CERT_FILE] 
                    [--client-key KEY_FILE] [-t TIMESTAMP] [-f FFMPEG] 
                    [-o OPUSENC] [-b BITRATE] [-c] [-a TAG] [-n] [-i] [-s] [-r] [-O]
                    [-fc] [--no-mono-conversion] [-A] [-k] [-u] [-C FILE2] [-D]
                    [--config-integration] [--install-integration] 
                    [--uninstall-integration] [-m] [--name-template TEMPLATE]
                    [--output-to-template PATH_TEMPLATE] [--show-tags]
                    [-S] [-F] [-X] [-d] [-T] [-q] [-Q] [--log-file]
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
  --path PATH           Path where to write the file on TeddyCloud server (supports templates like "/{albumartist}/{album}")
  --connection-timeout SECONDS
                        Connection timeout in seconds (default: 10)
  --read-timeout SECONDS
                        Read timeout in seconds (default: 300)
  --max-retries RETRIES
                        Maximum number of retry attempts (default: 3)
  --retry-delay SECONDS
                        Delay between retry attempts in seconds (default: 5)
  --create-custom-json  Fetch and update custom Tonies JSON data
  --version-2           Use version 2 of the Tonies JSON format (default: version 1)
  --username USERNAME   Username for basic authentication
  --password PASSWORD   Password for basic authentication
  --client-cert CERT_FILE
                        Path to client certificate file for certificate-based authentication
  --client-key KEY_FILE
                        Path to client private key file for certificate-based authentication

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program version and exit
  -t, --timestamp TIMESTAMP
                        set custom timestamp / bitstream serial
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
  -fc, --force-creation
                        Force creation of Tonie file even if it already exists
  --no-mono-conversion  Do not convert mono audio to stereo (default: convert mono to stereo)
  -A, --auto-download   Automatically download FFmpeg and opusenc if needed
  -k, --keep-temp       Keep temporary opus files in a temp folder for testing
  -u, --use-legacy-tags Use legacy hardcoded tags instead of dynamic TonieToolbox tags
  -C, --compare FILE2   Compare input file with another .taf file for debugging
  -D, --detailed-compare
                        Show detailed OGG page differences when comparing files
  --config-integration  Configure context menu integration
  --install-integration
                        Integrate with the system (e.g., create context menu entries)
  --uninstall-integration
                        Uninstall context menu integration

Media Tag Options:
  -m, --use-media-tags  Use media tags from audio files for naming
  --name-template TEMPLATE
                        Template for naming files using media tags. Example: "{album} - {artist}"
  --output-to-template PATH_TEMPLATE
                        Template for output path using media tags. Example: "C:\Music\{albumartist}\{album}"
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
  --log-file            Save logs to a timestamped file in .tonietoolbox folder
```

### Common Usage Examples

#### Analyze a Tonie file

```shell
tonietoolbox --info my_tonie.taf
```

#### Split a Tonie file into individual opus tracks

```shell
tonietoolbox --split my_tonie.taf 
```

#### Compare TAF files

Compare two TAF files for debugging purposes:

```shell
tonietoolbox file1.taf --compare file2.taf
```

For detailed comparison including OGG page differences:

```shell
tonietoolbox file1.taf --compare file2.taf --detailed-compare
```

#### Custom timestamp options

```shell
tonietoolbox input.mp3 --timestamp 1745078762  # UNIX Timestamp
tonietoolbox input.mp3 --timestamp 0x6803C9EA  # Bitstream time
tonietoolbox input.mp3 --timestamp ./reference.taf  # Reference TAF for extraction
```

#### Set custom bitrate

```shell
tonietoolbox input.mp3 --bitrate 128
```

#### Constant bitrate encoding

For more predictable file sizes and consistent quality, use constant bitrate (CBR) encoding:

```shell
# Encode with constant bitrate at 96 kbps (default)
tonietoolbox input.mp3 --cbr

# Encode with constant bitrate at 128 kbps
tonietoolbox input.mp3 --cbr --bitrate 128
```

#### Append Tonie tag

You can append a hexadecimal tag to the filename, which is useful for organizing Tonie files:

```shell
# Add an 8-character hex tag to filename
tonietoolbox input.mp3 --append-tonie-tag 7F8A6B2E

# The output will be named "input-7F8A6B2E.taf"
```

#### Process a complex folder structure

Process an audiobook series with multiple folders:

```shell
tonietoolbox --recursive "C:\Hörspiele\Die drei Fragezeichen\Folgen"
```

Process a music collection with nested album folders and save TAF files alongside the source directories:

```shell
tonietoolbox --recursive --output-to-source "C:\Hörspiele\" 
```

#### Automatic dependency download

If FFmpeg or opusenc are not found in your PATH, TonieToolbox can automatically download them:

```shell
# Automatically download dependencies when needed
tonietoolbox input.mp3 --auto-download

# Specify custom FFmpeg or opusenc locations
tonietoolbox input.mp3 --ffmpeg "C:\path\to\ffmpeg.exe" --opusenc "C:\path\to\opusenc.exe"
```

#### Keep temporary files

When troubleshooting or debugging, you can keep the temporary opus files:

```shell
# Keep temporary opus files in the temp folder
tonietoolbox input.mp3 --keep-temp

```

#### Working with list files

Create a text file (.lst) with paths to audio files for batch processing:

```text
# Contents of playlist.lst:
C:\Music\song1.mp3
"C:\Music\song2.flac"
C:\Music\song3.wav
"C:\Music Path With Spaces\song2.flac"
```

```shell
# Process the list file
tonietoolbox playlist.lst my_playlist.taf
```

#### TeddyCloud advanced options

Customize your TeddyCloud uploads with connection options:

```shell
# Upload with custom timeouts and retry parameters
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --connection-timeout 20 --read-timeout 600 --max-retries 5 --retry-delay 10

# Disable progress bar during upload
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --show-progress=False

# Upload to a special folder in TeddyCloud
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --special-folder library
```

#### Get available tags from TeddyCloud

To see which tags you can use with your TeddyCloud server:

```shell
tonietoolbox --get-tags https://teddycloud.example.com
```

#### Version checking and updates

TonieToolbox can check for newer versions and notify you when there are updates available:

```shell
# Skip checking for updates if you're offline or want faster startup
tonietoolbox input.mp3 --skip-update-check

# Force refresh of version information from PyPI
tonietoolbox input.mp3 --force-refresh-cache

# Clear cached version information
tonietoolbox --clear-version-cache
```

#### Legacy tag options

Use legacy hardcoded tags instead of dynamic TonieToolbox tags:

```shell
tonietoolbox input.mp3 --use-legacy-tags
```

#### Create custom JSON data

When uploading to TeddyCloud, you can also update the custom Tonies JSON data with information about the uploaded file:

```shell
tonietoolbox input.mp3 --upload https://teddycloud.example.com --create-custom-json
```

This will fetch and update the custom Tonies JSON data in the TeddyCloud server with information from your audio files.

#### Logging and Troubleshooting

Control the verbosity of console output with different logging levels:

```shell
# Enable detailed debug information (useful for troubleshooting)
tonietoolbox input.mp3 --debug

# Enable extremely verbose trace logging (developer level)
tonietoolbox input.mp3 --trace

# Reduce output to show only warnings and errors
tonietoolbox input.mp3 --quiet

# Show only critical errors (minimal output)
tonietoolbox input.mp3 --silent
```

You can combine logging options with other commands:

```shell
# Debug mode while splitting a TAF file
tonietoolbox --split my_tonie.taf --debug

# Quiet mode while batch processing
tonietoolbox --recursive "Music/Collection/" --quiet
```

#### Force creation of TAF files

If a valid TAF file already exists, TonieToolbox will skip recreating it by default. To force creation even if the file exists:

```shell
# Force creation of a TAF file even if it already exists
tonietoolbox input.mp3 --force-creation
```

This is useful when you want to update the content or encoding settings of an existing TAF file.

#### Windows Context Menu Integration

TonieToolbox can integrate with Windows Explorer, allowing you to right-click on audio files or folders to convert them:

```shell
# Install context menu integration (one-time setup)
tonietoolbox --install-integration

# Configure context menu options
tonietoolbox --config-integration

# Remove context menu integration
tonietoolbox --uninstall-integration
```

After installation, you can right-click on any audio file or folder in Windows Explorer and select "Convert to Tonie Format". 

When changing the configuration via `--config-integration`. Apply them to the integration by simply execute `tonietoolbox --install-integration` again.

#### Log File Generation

Save detailed logs to a timestamped file for troubleshooting complex operations:

```shell
# Enable log file generation
tonietoolbox input.mp3 --log-file

# Combine with debug logging for maximum detail
tonietoolbox --recursive input_directory/ --log-file --debug
```

Log files are saved in the `.tonietoolbox\logs` folder in your user directory.

#### Enhanced Media Tag Templates

Create custom directory structures based on media tags:

```shell
# Create output based on a path template
tonietoolbox input.mp3 --use-media-tags --output-to-template "C:\Music\{albumartist}\{album}"

# Use with recursive processing
tonietoolbox --recursive "Music/Collection/" --use-media-tags --output-to-template "Organized/{genre}/{year} - {album}"
```

This creates a directory structure based on the audio files' metadata and places the converted TAF files accordingly.

#### TeddyCloud Authentication Options

> **Note:** Authentication is based on the Features available when using [TeddyCloudStarter](https://github.com/Quentendo64/TeddyCloudStarter).

TonieToolbox supports multiple authentication methods for secure TeddyCloud connections:

```shell
# Basic authentication with username and password
tonietoolbox input.mp3 --upload https://teddycloud.example.com --username admin --password secret

# Certificate-based authentication
tonietoolbox input.mp3 --upload https://teddycloud.example.com --client-cert certificate.crt --client-key private.key
```

#### Custom JSON Format Versioning

Choose between different versions of the Tonies JSON format:

```shell
# Use version 2 of the Tonies JSON format (enhanced metadata)
tonietoolbox input.mp3 --upload https://teddycloud.example.com --create-custom-json --version-2
```

### Media Tags

TonieToolbox can read metadata tags from audio files (such as ID3 tags in MP3 files, Vorbis comments in FLAC/OGG files, etc.) and use them to create more meaningful filenames or display information about your audio collection.

#### View available tags in audio files

To see what tags are available in your audio files:

```shell
tonietoolbox --show-tags input.mp3
```

This will display all readable tags from the file, which can be useful for creating naming templates.

#### Use media tags for file naming

To use the metadata from audio files when generating output filenames:

```shell
tonietoolbox input.mp3 --use-media-tags
```

For single files, this will use a default template of "{title} - {artist}" for the output filename.

#### Custom naming templates

You can specify custom templates for generating filenames based on the audio metadata:

```shell
tonietoolbox input.mp3 --use-media-tags --name-template "{artist} - {album} - {title}"
```

#### Recursive processing with media tags

When processing folders recursively, media tags can provide more consistent naming:

```shell
tonietoolbox --recursive --use-media-tags "Music/Collection/"
```

This will attempt to use the album information from the audio files for naming the output files:

```shell
tonietoolbox --recursive --use-media-tags --name-template "{date} - {album} ({artist})" "Music/Collection/"
```

### TeddyCloud Upload

TonieToolbox can upload files directly to a TeddyCloud server, which is an alternative to the official Tonie cloud for managing custom Tonies.

#### Upload a Tonie file to TeddyCloud

```shell
tonietoolbox --upload https://teddycloud.example.com my_tonie.taf
```

This will upload the specified Tonie file to the TeddyCloud server.

#### Upload a newly created Tonie file

You can combine conversion and upload in a single command:

```shell
tonietoolbox input.mp3 --upload https://teddycloud.example.com
```

This will convert the input file to TAF format and then upload it to the TeddyCloud server.

#### Upload with custom path

```shell
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --path "/custom_audio"
# The path must already exist in the TeddyCloud Library.
```

#### Upload with artwork

> **Note:** This function will only work if the `/custom_img` folder is mounted in the TeddyCloud Library. For an easy start and to handle this automatically (and much more), use [TeddyCloudStarter](https://github.com/Quentendo64/TeddyCloudStarter).

TonieToolbox can automatically find and upload cover artwork alongside your Tonie files:

```shell
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --include-artwork
```

This will:

1. Look for cover images (like "cover.jpg", "artwork.png", etc.) in the source directory
2. If no cover image is found, attempt to extract embedded artwork from the audio files
3. Upload the artwork to the "/custom_img" directory on the TeddyCloud server
4. The artwork will be uploaded with the same filename as the Tonie file for easier association

#### Recursive processing with uploads

```shell
tonietoolbox --recursive "Music/Albums" --upload https://teddycloud.example.com --include-artwork
```

This will process all folders recursively, create TAF files, and upload both the TAF files and their cover artwork to the TeddyCloud server.

#### Upload with SSL certificate verification disabled

```shell
tonietoolbox my_tonie.taf --upload https://teddycloud.example.com --ignore-ssl-verify
```

Use this option if the TeddyCloud server uses a self-signed certificate.

## Real-World Use Cases

### Converting an Audiobook Series

To convert an entire audiobook series with proper metadata and upload to TeddyCloud:

```shell
tonietoolbox --recursive --use-media-tags --name-template "{year} - {albumartist} - {album}" --bitrate 128 --upload https://teddycloud.example.com --include-artwork "C:\Hörspiele\Die Drei Fragezeichen"
```

This command will:

1. Recursively process the Die Drei Fragezeichen audioplays directory
2. Use a naming template based on source metadata
3. Encode at 128 kbps
4. Upload both audio files and cover art to TeddyCloud

### Creating Children's Story Collections

For a custom children's story collection with chapters:

```shell
tonietoolbox story_collection.lst kids_stories.taf --bitrate 96 --cbr --auto-download --use-media-tags --name-template "{title} Stories" --debug
```

This command:

1. Processes a list of story audio files
2. Names the output based on metadata
3. Uses constant bitrate encoding for consistent quality
4. Automatically downloads dependencies if needed
5. Shows detailed debug information during the process

### Advanced Media Tag Usage

For complex media tag processing:

```shell
# First check available tags
tonietoolbox --show-tags "C:\Music\Classical\Bach"

# Then use a sophisticated naming template
tonietoolbox "C:\Music\Classical\Bach" --use-media-tags --name-template "{composer} - {opus} in {key} ({conductor}, {orchestra})"
```

The first command shows what tags are available, allowing you to create precise naming templates for classical music collections.

## Technical Details
[Moved to TECHNICAL.md](TECHNICAL.md)

## Related Projects

This project is inspired by and builds upon the work of other Tonie-related open source projects:

- [opus2tonie](https://github.com/bailli/opus2tonie) - A command line utility to convert opus files to the Tonie audio format
- [teddycloud](https://github.com/toniebox-reverse-engineering/teddycloud) - Self-hosted alternative to the Tonie cloud / Boxine cloud for managing custom content
- [TeddyCloudStarter](https://github.com/Quentendo64/TeddyCloudStarter) - A Wizard for Docker-based deployment of [teddycloud](https://github.com/toniebox-reverse-engineering/teddycloud)


## Legal Notice

This project is an independent, community-driven effort created for educational and personal use purposes.

- tonies®, toniebox®, and Hörfigur® are registered trademarks of [tonies GmbH](https://tonies.com).
- This project is not affiliated with, endorsed by, or connected to tonies GmbH in any way.
- TonieToolbox is provided "as is" without warranty of any kind, either express or implied.
- Users are responsible for ensuring their usage complies with all applicable copyright and intellectual property laws.
- This tool is intended for personal use with legally owned content only.

By using TonieToolbox, you acknowledge that the authors of this software take no responsibility for any potential misuse or any damages that might result from the use of this software.

## Support

If you need help, have questions, or want to report a bug, please use the following channels:

- [GitHub Issues](https://github.com/Quentendo64/TonieToolbox/issues) for bug reports and feature requests
- [GitHub Discussions](https://github.com/Quentendo64/TonieToolbox/discussions) for general questions and community support
- [HOWTO Guide](HOWTO.md) for common usage instructions

## Attribution
[Parrot Icon created by Freepik - Flaticon](https://www.flaticon.com/free-animated-icons/parrot)