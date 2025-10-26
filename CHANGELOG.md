# Changelog

All notable changes to TonieToolbox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
### Fixed
### Changed
### Removed

## [0.6.5] - 2025-10-25
### Added
- Implemented minimal GUI player using tkinter with --play-ui option
- Added Tools tab to GUI player for audio file conversion
- Added docker multiarchitecture build (amd64, arm64)
### Fixed
- Fixed FFmpeg output path handling for conversion functions
### Changed
- Improved Tools tab to automatically synchronize with Player tab when a file is loaded
- kde integration updated to use --play-ui for GUI player
### Removed

## [0.6.4] - 2025-10-25
### Added
- Added simple .taf player using --play
- Added initial KDE integration for context menu handling
### Fixed
- Fixed certificate path issue on Windows-Integration for TeddyCloud upload
### Changed
- Adjusted --show-tags to return all available tags (excluding artwork/picture tags)

## [0.6.1] - 2025-05-24


### Fixed
- Fixed --custom-json generation for v1 and v2 formats with correct handling header timestamp and hash

## [0.6.0rc2] - 2025-05-15


### Fixed
- Error when using --install-integration caused by a distracted developer who forgot to comment on something. Silly™ 

## [0.6.0rc1] - 2025-05-15

### Added

### Fixed
- Possible Integration of *WIP Integration for MacOS
### Changed

- README Structure, moved Technical Details to [TECHNICAL.md](TECHNICAL.md) 

### Removed

- Not ready: MacOS Integration
- Not ready: Compare from Windows Integration for .taf

## [0.6.0a5] - 2025-05-15

### Added

- Dynamic Pathing based on meta tags

### Fixed

- Fixes for context menu integration

## [0.6.0a4] - 2025-05-14

### Fixed

- Fixes for context menu integration

## [0.6.0a3] - 2025-05-13

### Fixed

- Fixes for context menu integration

## [0.6.0a2] - 2025-05-12

### Added

- Context menu integration for Windows using --install-integration / --uninstall-integration
- Advanced context menu configuration using --config-integration after installation

## [0.6.0a1] - 2025-05-12

### Added

- *WIP* Context menu integration for Windows
- *WIP* Context menu integration for Linux
- *WIP* Context menu integration for MacOS

### Changed

- Logging to subdirectory `~/.tonietoolbox/logs`

## [0.5.1] - 2025-05-12

### Fixed

- gh-17: Fixed issue with --show-tags not displaying correctly

### Changed

- Adjusted get_input_files() for better handling of file types

## [0.5.0] - 2025-05-11

### Added

- Added new handler for generating v1 tonies.custom.json

### Changed

- Default behaviour of --create-custom-json to create a v1 tonies.custom.json

- Updated README.md with new features and usage examples

### Fixed

- gh-12: --name-template not working as expected

## [0.5.0a2] - 2025-05-08

### Changed

- Updated README.md with new features and usage examples
- Updated HOWTO.md with new features and usage examples
- Updated version handler to check for new releases on GitHub
- Direct Upload to TeddyCloud now only works with .TAF files

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
