#!/usr/bin/env python3
"""
Version bump utility for TonieToolbox.

Usage:
  python bump_version.py [major|minor|patch]
"""

import re
import sys
import os.path

VERSION_FILE = "TonieToolbox/__init__.py"

def read_version():
    """Read current version from __init__.py"""
    with open(VERSION_FILE, 'r') as f:
        content = f.read()
    
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
    if not match:
        raise ValueError(f"Could not find __version__ in {VERSION_FILE}")
    
    return match.group(1)

def write_version(new_version):
    """Write new version to __init__.py"""
    with open(VERSION_FILE, 'r') as f:
        content = f.read()
    
    content = re.sub(
        r"__version__\s*=\s*['\"]([^'\"]+)['\"]",
        f"__version__ = '{new_version}'",
        content
    )
    
    with open(VERSION_FILE, 'w') as f:
        f.write(content)

def bump_version(current_version, bump_type):
    """Bump version according to semantic versioning rules."""
    major, minor, patch = current_version.split('.')
    
    if bump_type == 'major':
        return f"{int(major) + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{int(minor) + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{int(patch) + 1}"
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    current_version = read_version()
    new_version = bump_version(current_version, bump_type)
    
    write_version(new_version)
    print(f"Version bumped from {current_version} to {new_version}")

if __name__ == "__main__":
    main()