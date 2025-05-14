#!/usr/bin/python3
"""
Version handler to check if the latest version of TonieToolbox is being used.
"""

import json
import os
import time
from packaging import version
from urllib import request
from urllib.error import URLError

from . import __version__
from .logger import get_logger

# Cache filename for version information
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tonietoolbox")
CACHE_FILE = os.path.join(CACHE_DIR, "version_cache.json")
CACHE_EXPIRY = 86400  # 24 hours in seconds

logger = get_logger(__name__)

def get_pypi_version(force_refresh: bool = False) -> tuple[str, str | None]:
    """
    Get the latest version of TonieToolbox from PyPI.
    
    Args:
        force_refresh (bool): If True, ignore the cache and fetch directly from PyPI
    Returns:
        tuple[str, str | None]: (latest_version, None) on success, (current_version, error_message) on failure
    """
    logger.debug("Checking for latest version (force_refresh=%s)", force_refresh)
    logger.debug("Current version: %s", __version__)
    
    try:
        # Check if we have a recent cache and should use it
        if not force_refresh and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    cache_data = json.load(f)
                    
                cached_version = cache_data.get("version")
                cache_timestamp = cache_data.get("timestamp", 0)
                cache_age = time.time() - cache_timestamp
                
                logger.debug("Cache info: version=%s, age=%d seconds (expires after %d)", 
                            cached_version, cache_age, CACHE_EXPIRY)
                
                if cache_age < CACHE_EXPIRY:
                    logger.debug("Using cached version info: %s", cached_version)
                    return cached_version, None
                else:
                    logger.debug("Cache expired (%d seconds old), refreshing from PyPI", cache_age)
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug("Cache file corrupt, will fetch from PyPI: %s", e)
        else:
            if force_refresh:
                logger.debug("Forced refresh requested, bypassing cache")
            else:
                logger.debug("No cache found, fetching from PyPI")
        
        # Fetch from PyPI
        logger.debug("Fetching latest version from PyPI")
        with request.urlopen("https://pypi.org/pypi/TonieToolbox/json", timeout=2) as response:
            pypi_data = json.loads(response.read().decode("utf-8"))
            latest_version = pypi_data["info"]["version"]
            
            # Update cache
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR, exist_ok=True)
                
            with open(CACHE_FILE, "w") as f:
                cache_data = {
                    "version": latest_version,
                    "timestamp": time.time()
                }
                json.dump(cache_data, f)
                logger.debug("Updated cache: %s", cache_data)
                
            logger.debug("Latest version from PyPI: %s", latest_version)
            return latest_version, None
            
    except (URLError, json.JSONDecodeError) as e:
        logger.debug("Failed to fetch version from PyPI: %s", e)
        return __version__, f"Failed to check for updates: {str(e)}"
    except Exception as e:
        logger.debug("Unexpected error checking for updates: %s", e)
        return __version__, f"Unexpected error checking for updates: {str(e)}"


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings according to PEP 440.
    
    Args:
        v1 (str): First version string
        v2 (str): Second version string
    Returns:
        int: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    logger.debug("Comparing versions: '%s' vs '%s'", v1, v2)
    
    try:   
        # Strip leading 'v' if present
        v1_clean = v1[1:] if v1.startswith('v') else v1
        v2_clean = v2[1:] if v2.startswith('v') else v2
        
        parsed_v1 = version.parse(v1_clean)
        parsed_v2 = version.parse(v2_clean)
        
        logger.debug("Parsed versions: %s vs %s", parsed_v1, parsed_v2)
        
        if parsed_v1 < parsed_v2:
            logger.debug("Result: '%s' is OLDER than '%s'", v1, v2)
            return -1
        elif parsed_v1 > parsed_v2:
            logger.debug("Result: '%s' is NEWER than '%s'", v1, v2)
            return 1
        else:
            logger.debug("Result: versions are EQUAL")
            return 0
    except Exception as e:
        logger.debug("Error comparing versions '%s' and '%s': %s", v1, v2, e)
        # On error, fall back to simple string comparison to avoid crashes
        logger.debug("Falling back to string comparison")
        if v1 == v2:
            return 0
        elif v1 < v2:
            return -1
        else:
            return 1


def check_for_updates(quiet: bool = False, force_refresh: bool = False) -> tuple[bool, str, str, bool]:
    """
    Check if the current version of TonieToolbox is the latest.
    
    Args:
        quiet (bool): If True, will not log any information messages and skip user confirmation
        force_refresh (bool): If True, bypass cache and check PyPI directly
    Returns:
        tuple[bool, str, str, bool]: (is_latest, latest_version, message, update_confirmed)
            is_latest: boolean indicating if the current version is the latest
            latest_version: string with the latest version
            message: string message about the update status or error
            update_confirmed: boolean indicating if the user confirmed the update
    """
    current_version = __version__
    update_confirmed = False
    
    logger.debug("Starting update check (quiet=%s, force_refresh=%s)", 
                quiet, force_refresh)
    latest_version, error = get_pypi_version(force_refresh)
    
    if error:
        logger.debug("Error occurred during update check: %s", error)
        return True, current_version, error, update_confirmed
        
    compare_result = compare_versions(current_version, latest_version)
    is_latest = compare_result >= 0  # current >= latest
    
    logger.debug("Version comparison result: %d (is_latest=%s)", compare_result, is_latest)
    
    if is_latest:
        message = f"You are using the latest version of TonieToolbox ({current_version})"
        if not quiet:
            logger.debug(message)
    else:
        message = f"Update available! Current version: {current_version}, Latest version: {latest_version}"
        if not quiet:
            logger.info(message)
            
            # Show confirmation prompt if not in quiet mode
            try:
                response = input(f"Do you want to upgrade to TonieToolbox {latest_version}? [y/N]: ").lower().strip()
                update_confirmed = response == 'y' or response == 'yes'
                
                if update_confirmed:
                    logger.info("Update confirmed. Attempting to install update...")
                    if install_update():
                        logger.info(f"Successfully updated to TonieToolbox {latest_version}")
                        import sys
                        logger.info("Exiting program. Please restart TonieToolbox to use the new version.")
                        sys.exit(0)
                    else:
                        logger.error("Failed to install update automatically")
                        logger.error("Please update manually using: pip install --upgrade TonieToolbox")
                        import sys
                        sys.exit(1)
                else:
                    logger.info("Update skipped by user.")
            except (EOFError, KeyboardInterrupt):
                logger.debug("User input interrupted")
                update_confirmed = False
    
    return is_latest, latest_version, message, update_confirmed


def install_update() -> bool:
    """
    Try to install the update using pip, pip3, or pipx.
    
    Returns:
        bool: True if the update was successfully installed, False otherwise
    """
    import subprocess
    import sys
    
    package_name = "TonieToolbox"
    commands = [
        [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
        ["pip", "install", "--upgrade", package_name],
        ["pip3", "install", "--upgrade", package_name],
        ["pipx", "upgrade", package_name]
    ]
    
    for cmd in commands:
        try:
            logger.info(f"Attempting to install update using: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                logger.debug("Update command succeeded")
                logger.debug(f"Output: {result.stdout}")
                return True
            else:
                logger.debug(f"Command failed with returncode {result.returncode}")
                logger.debug(f"stdout: {result.stdout}")
                logger.debug(f"stderr: {result.stderr}")
        except Exception as e:
            logger.debug(f"Exception while running {cmd[0]}: {str(e)}")
    
    return False


def clear_version_cache() -> bool:
    """
    Clear the version cache file to force a refresh on next check.
    
    Returns:
        bool: True if cache was cleared, False otherwise
    """
    
    try:
        if os.path.exists(CACHE_FILE):
            logger.debug("Removing version cache file: %s", CACHE_FILE)
            os.remove(CACHE_FILE)
            return True
        else:
            logger.debug("No cache file to remove")
            return False
    except Exception as e:
        logger.debug("Error clearing cache: %s", e)
        return False