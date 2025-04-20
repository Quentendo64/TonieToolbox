#!/usr/bin/env python3
"""
Version bump utility for TonieToolbox.

Usage:
  python bump_version.py [major|minor|patch] [--git] [--manual-changelog]

Options:
  --git               Perform Git operations (commit, tag, and optionally push)
  --manual-changelog  Skip automatic CHANGELOG.md update and allow manual editing
"""

import re
import sys
import os.path
import subprocess
import datetime
import time
from pathlib import Path

VERSION_FILE = "TonieToolbox/__init__.py"
CHANGELOG_FILE = "CHANGELOG.md"

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

def update_changelog(new_version, manual_edit=False):
    """Update CHANGELOG.md with the new version"""
    if not os.path.exists(CHANGELOG_FILE):
        print(f"Warning: {CHANGELOG_FILE} not found, skipping changelog update")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")
    new_version_header = f"## [{new_version}] - {today}"
    
    if manual_edit:
        with open(CHANGELOG_FILE, 'r') as f:
            content = f.read()
        if f"## [{new_version}]" in content:
            print(f"\nVersion {new_version} already exists in {CHANGELOG_FILE}.")
        else:
            print(f"\nPlease update {CHANGELOG_FILE} manually.")
            print(f"Add the following section where appropriate:")
            print(f"\n{new_version_header}\n")
            print("### Added")
            print("- ")
            print("\n### Changed")
            print("- ")
            print("\n### Fixed")
            print("- ")
            print("\n### Removed")
            print("- ")
        try:
            if sys.platform == 'win32':
                os.startfile(CHANGELOG_FILE)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, CHANGELOG_FILE])
        except Exception as e:
            print(f"Could not open editor: {e}")
        
        print("\nWaiting for you to complete the changelog edits...")
        input("Press Enter when you have finished editing the changelog...")
        print("Checking if the new version is in the changelog...")
        with open(CHANGELOG_FILE, 'r') as f:
            updated_content = f.read()
        
        if f"## [{new_version}]" not in updated_content and not f"## [{new_version}] -" in updated_content:
            print(f"\nWARNING: Version {new_version} was not found in the changelog.")
            proceed = input("Do you want to continue anyway? (y/n): ").lower().strip() == 'y'
            if not proceed:
                print("Version bump aborted.")
                sys.exit(1)
        
        return
    
    with open(CHANGELOG_FILE, 'r') as f:
        content = f.read()
    if "## [Unreleased]" in content:
        content = content.replace(
            "## [Unreleased]",
            "## [Unreleased]\n- Add Unreleased changes here\n\n" + new_version_header
        )
    else:
        content_lines = content.split('\n')
        header_end = 0
        for i, line in enumerate(content_lines):
            if line.startswith('##'):
                header_end = i
                break
        
        if header_end > 0:
            content = '\n'.join(content_lines[:header_end]) + '\n\n' + new_version_header + '\n' + '\n'.join(content_lines[header_end:])
        else:
            content = content + '\n\n' + new_version_header + '\n'
    
    with open(CHANGELOG_FILE, 'w') as f:
        f.write(content)

def run_git_commands(new_version):
    """Run Git commands to commit and tag the new version"""
    print("Running Git commands...")
    print("Checking for uncommitted changes...")
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if status.stdout:
        print("Uncommitted changes found. Please commit or stash them before running this script.")
        sys.exit(1)   

    print("Committing version bump...")
    commit_msg = f"Bump version to {new_version}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    
    print("Creating a Git tag...")
    tag_name = f"v{new_version}"
    tag_msg = f"Version {new_version}"
    subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_msg], check=True)
    

    push = input("Do you want to push the changes and tags to remote? (y/n): ").lower().strip() == 'y'
    if push:
        print("Pushing to remote...")
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)
        print("Changes and tags pushed successfully.")
    else:
        print("\nChanges committed and tagged locally. To push them later, run:")
        print(f"  git push && git push --tags")

def main():
    # Parse arguments
    use_git = "--git" in sys.argv
    if use_git:
        sys.argv.remove("--git")
    
    manual_changelog = "--manual-changelog" in sys.argv
    if manual_changelog:
        sys.argv.remove("--manual-changelog")
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print("Usage: python bump_version.py [major|minor|patch] [--git] [--manual-changelog]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    current_version = read_version()
    new_version = bump_version(current_version, bump_type)
    
    # Update the version file
    write_version(new_version)
    print(f"Version bumped from {current_version} to {new_version} in {VERSION_FILE}")
    
    # Update the changelog
    update_changelog(new_version, manual_edit=manual_changelog)
    print(f"Updated {CHANGELOG_FILE} with new version {new_version}")
    
    # If manual changelog editing was used, give time for the user to save the file
    if manual_changelog:
        time.sleep(1)  # Brief pause to ensure file is saved
    
    # Optionally run Git commands
    if use_git:
        try:
            run_git_commands(new_version)
        except subprocess.CalledProcessError as e:
            print(f"Error executing Git commands: {e}")
            sys.exit(1)
    else:
        print("\nTo complete the release with Git, run:")
        print(f"  git add {VERSION_FILE} {CHANGELOG_FILE}")
        print(f"  git commit -m \"Bump version to {new_version}\"")
        print(f"  git tag -a v{new_version} -m \"Version {new_version}\"")
        print(f"  git push && git push --tags")

if __name__ == "__main__":
    main()