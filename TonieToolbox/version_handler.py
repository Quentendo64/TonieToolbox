"""
Version handler to check if the latest version of TonieToolbox is being used.
"""

import json
import logging
import os
import time
from urllib import request
from urllib.error import URLError

from . import __version__
from .logger import get_logger

# Cache filename for version information
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tonietoolbox")
CACHE_FILE = os.path.join(CACHE_DIR, "version_cache.json")
CACHE_EXPIRY = 86400  # 24 hours in seconds


def get_pypi_version(force_refresh=False):
    """
    Get the latest version of TonieToolbox from PyPI.
    
    Args:
        force_refresh: If True, ignore the cache and fetch directly from PyPI
        
    Returns:
        tuple: (latest_version, None) on success, (current_version, error_message) on failure
    """
    logger = get_logger("version_handler")
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


def compare_versions(v1, v2):
    """
    Compare two version strings.
    
    Args:
        v1: First version string
        v2: Second version string
        
    Returns:
        int: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    logger = get_logger("version_handler")
    logger.debug("Comparing versions: '%s' vs '%s'", v1, v2)
    
    try:
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        logger.debug("Version parts: %s vs %s", v1_parts, v2_parts)
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_part = v1_parts[i] if i < len(v1_parts) else 0
            v2_part = v2_parts[i] if i < len(v2_parts) else 0
            
            logger.debug("Comparing part %d: %d vs %d", i, v1_part, v2_part)
            
            if v1_part < v2_part:
                logger.debug("Result: '%s' is OLDER than '%s'", v1, v2)
                return -1
            elif v1_part > v2_part:
                logger.debug("Result: '%s' is NEWER than '%s'", v1, v2)
                return 1
        
        logger.debug("Result: versions are EQUAL")
        return 0
    except Exception as e:
        logger.debug("Error comparing versions '%s' and '%s': %s", v1, v2, e)
        # On error, assume versions are equal
        return 0


def check_for_updates(quiet=False, force_refresh=False):
    """
    Check if the current version of TonieToolbox is the latest.
    
    Args:
        quiet: If True, will not log any information messages
        force_refresh: If True, bypass cache and check PyPI directly
        
    Returns:
        tuple: (is_latest, latest_version, message)
            is_latest: boolean indicating if the current version is the latest
            latest_version: string with the latest version
            message: string message about the update status or error
    """
    logger = get_logger("version_handler")
    current_version = __version__
    
    logger.debug("Starting update check (quiet=%s, force_refresh=%s)", quiet, force_refresh)
    latest_version, error = get_pypi_version(force_refresh)
    
    if error:
        logger.debug("Error occurred during update check: %s", error)
        return True, current_version, error
        
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
            logger.info("Consider upgrading with: pip install --upgrade TonieToolbox")
    
    return is_latest, latest_version, message


def clear_version_cache():
    """
    Clear the version cache file to force a refresh on next check.
    
    Returns:
        bool: True if cache was cleared, False otherwise
    """
    logger = get_logger("version_handler")
    
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