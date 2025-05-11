# Contributing to TonieToolbox 🎵📦

Thank you for your interest in contributing to TonieToolbox! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Branching Strategy](#branching-strategy)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Project Structure](#project-structure)

## Code of Conduct

Please be respectful and inclusive when contributing to TonieToolbox. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** to your local machine

   ```bash
   git clone https://github.com/YourUsername/TonieToolbox.git
   cd TonieToolbox
   ```

3. **Set up the upstream remote**

   ```bash
   git remote add upstream https://github.com/Quentendo64/TonieToolbox.git
   ```

4. **Install development dependencies**

   ```bash
   pip install -e ".[test]"
   ```

## Development Environment

### Requirements

- Python 3.6 or higher
- FFmpeg (for audio conversion)
- opus-tools (specifically `opusenc` for Opus encoding)
- Git

### Recommended tools

- Visual Studio Code with Python extensions
- Docker for containerized development

### Virtual Environment

It's recommended to use a virtual environment for development:

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -e ".[test]"
```

## Branching Strategy

- `main` - Main production branch
- `develop` - Main develop branch
- `feature/*` - For new features
- `bugfix/*` - For bug fixes
- `release/*` - For release preparations

When working on a new feature or fix:

1. Create a new branch from `develop`:

   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, commit them, and push to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

## Commit Messages

Please follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:

```text
Add support for custom artwork templates

This change allows users to define custom artwork templates when uploading 
to TeddyCloud, providing more flexibility in how cover art is presented.

Fixes #123
```

## Pull Request Process

1. **Update your branch** with the latest changes from `main`

   ```bash
   git checkout feature/your-feature-name
   git fetch upstream
   git merge upstream/main
   ```

2. **Resolve any conflicts** that may arise

3. **Run tests** to make sure everything works

   ```bash
   pytest
   ```

4. **Push your changes** to your fork

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** through the GitHub website

6. **Fill in the pull request template** with a description of your changes

7. **Wait for review** - maintainers will review your PR and may request changes

## Testing

We use pytest for testing. Please add tests for new features and ensure all tests pass:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=TonieToolbox
```

## Documentation

- Update documentation for any new features or changes
- Include docstrings in your code
- Update the README.md if necessary
- Consider updating HOWTO.md for user-facing changes

## Release Process

TonieToolbox follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

When preparing a release:

1. Update version number in `TonieToolbox/__init__.py`
2. Update CHANGELOG.md with the new version and its changes
3. Create a pull request with these changes
4. Once merged, tag the release in git
5. A GitHub Action will build and publish the package to PyPI

## Project Structure

```text
TonieToolbox/
├── TonieToolbox/         # Main package directory
│   ├── __init__.py       # Package initialization, version
│   ├── __main__.py       # Command-line entry point
│   ├── artwork.py        # Artwork handling
│   ├── audio_conversion.py  # Audio conversion logic
│   ├── constants.py      # Shared constants
│   ├── dependency_manager.py  # External tool dependencies
│   ├── filename_generator.py  # Filename generation logic
│   ├── logger.py         # Logging configuration
│   ├── media_tags.py     # Media tag extraction
│   ├── ogg_page.py       # OGG page handling
│   ├── opus_packet.py    # OPUS packet handling
│   ├── recursive_processor.py  # Folder recursion logic
│   ├── tags.py           # Tag handling
│   ├── teddycloud.py     # TeddyCloud client
│   ├── tonie_analysis.py # TAF file analysis
│   ├── tonie_file.py     # TAF file operations
│   ├── tonie_header.proto # Protocol buffer definition
│   ├── tonie_header_pb2.py # Generated protobuf code
│   ├── tonies_json.py    # TeddyCloud JSON handling
│   └── version_handler.py # Version checking
├── tests/               # Test directory
├── CHANGELOG.md         # Version history
├── CONTRIBUTING.md      # This file
├── docker-compose.yml   # Docker configuration
├── Dockerfile           # Docker build definition
├── HOWTO.md             # Beginner's guide
├── LICENSE.md           # License information
├── MANIFEST.in          # Package manifest
├── pyproject.toml       # Project metadata and dependencies
├── README.md            # Main documentation
├── setup.py             # Package setup script
└── TonieToolbox.py      # Convenience entry point
```

## Thank You!

Your contributions to TonieToolbox are greatly appreciated. By following these guidelines, you help make the development process smoother for everyone involved.

Happy coding! 🎵📦