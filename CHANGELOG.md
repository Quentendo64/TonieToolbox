# Changelog

All notable changes to TonieToolbox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Download-option with rip

## [0.5.0a1] - 2025-05-07

### Added

- Initial release of version 0.5.0a1

- gh-2 - Allow BasicAuth & Client-Cert Authentication for TeddyCloud

- gh-3 - --include-artwork is not working for upload only

- Added Client-Certificate Authentication for TeddyCloud Upload Module

- gh-5 - Change Workflow for --upload in --recursive mode

- gh-6 - Adjust the conversion processing and check for valid existing .TAF

- gh-7 - Prevent duplicates in tonies.custom.json

- gh-10 - Add the correct runtime to tonies.custom.json

### Fixed

- gh-4 - Copying artwork fails if src/dst is mounted as NFS

- gh-9 - --create-custom-json code not reached

## [0.4.2] - 2025-04-21

### Fixed

- Github Docker Push Workflow

## [0.4.1] - 2025-04-21

### Added

- Added docker setup

### Fixed

- Python requirements (mutagen)

## [0.4.0] - 2025-04-21

### Added

- Added `--create-custom-json` for creating tonies.custom.json
- Added `--log-file` file logging for better support options.
- Added more debug & trace logging. More logging, more good.

## [0.3.0] - 2025-04-20

### Added

- Added a Legal Notice
- Added `--upload` Implementation of the TeddyCloud Upload Module
- Added `--include-artwork` option to automatically upload cover artwork alongside Tonie files

## [0.2.3] - 2025-04-20

### Added

- Using media tags for .TAF naming --use-media-tags | --use-media-tags --name-template "{artist} - {album} - {title}"

## [0.2.2] - 2025-04-20

### Added

- dynamic opus header / comments creation

## [0.2.1] - 2025-04-20

### Added

- short versions (aliases) for all the command-line arguments

## [0.2.0] - 2025-04-20

### Added

- Recursive Folder Processing - Using --recursive | --recursive --output-to-source

### Fixed

- dependency manager: Using opusenc after apt install
- .lst encoding problem

## [0.1.8] - 2025-04-20

### Changed

- consolidate all tonietoolbox files to ~/.tonietoolbox
- prioritize libs from tonietoolbox instead of system-wide installed

## [0.1.7] - 2025-04-20

### Added

- version handler try to install updates automatically after user confirmation

### Fixed

- dependency manager checks previous downloaded versions now

### Changed

- version handler need user confirmation when update is available

## [0.1.6] - 2025-04-20

### Fixed

- Version Handler and cache invalidation
- Github Workflow Relesenotes extraction

## [0.1.5] - 2025-04-20

### Added

- Version Handler *WIP

## [0.1.4] - 2025-04-20

### Added

- Auto Github Release based on tags.

## [0.1.3] - 2025-04-20

### Added

- Added HOWTO.md for beginners.

### Changed

- Changed default timestamp behaviour to act like TeddyCloud/Teddybench. (Deduct)

## [0.1.2] - 2025-04-20

### Changed

- Upgrade dependencies: ffmpeg shared to full.

## [0.1.1] - 2025-04-20

### Added

- Added --auto-download argument for dependency_manager.

## [0.1.0] - 2025-04-20

### Added

- Initial release
- Audio file conversion to Tonie format
- Support for FFmpeg and opusenc dependencies
- Command line interface with various options
- Automatic dependency download with --auto-download flag
