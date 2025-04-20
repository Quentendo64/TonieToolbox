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

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tonietoolbox")
CACHE_FILE = os.path.join(CACHE_DIR, "version_cache.json")
CACHE_EXPIRY = 86400  # 24 hours in seconds


def get_pypi_version():
    """
    Get the latest version of TonieToolbox from PyPI.
    
    Returns:
        tuple: (latest_version, None) on success, (current_version, error_message) on failure
    """
    logger = get_logger("version_handler")
    
    try:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    cache_data = json.load(f)
                    
                if time.time() - cache_data.get("timestamp", 0) < CACHE_EXPIRY:
                    logger.debug("Using cached version info: %s", cache_data["version"])
                    return cache_data["version"], None
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug("Cache file corrupt, will fetch from PyPI: %s", e)
        
        logger.debug("Fetching latest version from PyPI")
        with request.urlopen("https://pypi.org/pypi/TonieToolbox/json", timeout=2) as response:
            pypi_data = json.loads(response.read().decode("utf-8"))
            latest_version = pypi_data["info"]["version"]
            
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR, exist_ok=True)
                
            with open(CACHE_FILE, "w") as f:
                json.dump({
                    "version": latest_version,
                    "timestamp": time.time()
                }, f)
                
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
    v1_parts = [int(x) for x in v1.split('.')]
    v2_parts = [int(x) for x in v2.split('.')]
    
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = v1_parts[i] if i < len(v1_parts) else 0
        v2_part = v2_parts[i] if i < len(v2_parts) else 0
        
        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1
            
    return 0


def check_for_updates(quiet=False):
    """
    Check if the current version of TonieToolbox is the latest.
    
    Args:
        quiet: If True, will not log any information messages
        
    Returns:
        tuple: (is_latest, latest_version, message)
            is_latest: boolean indicating if the current version is the latest
            latest_version: string with the latest version
            message: string message about the update status or error
    """
    logger = get_logger("version_handler")
    current_version = __version__
    
    latest_version, error = get_pypi_version()
    
    if error:
        return True, current_version, error
        
    is_latest = compare_versions(current_version, latest_version) >= 0
    
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