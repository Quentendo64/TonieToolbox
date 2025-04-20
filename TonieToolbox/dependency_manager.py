"""
Dependency management for the TonieToolbox package.

This module handles the download and management of external dependencies
required by the TonieToolbox package, such as FFmpeg and opus-tools.
"""

import os
import sys
import platform
import subprocess
import shutil
import zipfile
import tarfile
import urllib.request
from pathlib import Path

from .logger import get_logger
logger = get_logger('dependency_manager')

DEPENDENCIES = {
    'ffmpeg': {
        'windows': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
            'bin_path': 'bin/ffmpeg.exe',
            'extract_dir': 'ffmpeg'
        },
        'linux': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz',
            'bin_path': 'ffmpeg',
            'extract_dir': 'ffmpeg'
        },
        'darwin': {
            'url': 'https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip',
            'bin_path': 'ffmpeg',
            'extract_dir': 'ffmpeg'
        }
    },
    'opusenc': {
        'windows': {
            'url': 'https://archive.mozilla.org/pub/opus/win32/opus-tools-0.2-opus-1.3.zip',
            'bin_path': 'opusenc.exe',
            'extract_dir': 'opusenc'
        },
        'linux': {
            'package': 'opus-tools'
        },
        'darwin': {
            'package': 'opus-tools'
        }
    }
}

def get_system():
    """Get the current operating system."""
    system = platform.system().lower()
    logger.debug("Detected operating system: %s", system)
    return system

def get_user_data_dir():
    """Get the user data directory for storing downloaded dependencies."""
    system = get_system()
    
    if system == 'windows':
        base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif system == 'darwin':
        base_dir = os.path.expanduser('~/Library/Application Support')
    else:  # linux or other unix-like
        base_dir = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    
    app_dir = os.path.join(base_dir, 'TonieToolbox')
    logger.debug("Using application data directory: %s", app_dir)
    
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def download_file(url, destination):
    """
    Download a file from a URL to the specified destination.
    
    Args:
        url (str): The URL of the file to download
        destination (str): The path to save the file to
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        logger.info("Downloading %s to %s", url, destination)
        headers = {'User-Agent': 'TonieToolbox-dependency-downloader/1.0'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response, open(destination, 'wb') as out_file:
            file_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            
            logger.debug("File size: %d bytes", file_size)
            
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                
                downloaded += len(buffer)
                out_file.write(buffer)
                
                if file_size > 0:
                    percent = downloaded * 100 / file_size
                    logger.debug("Download progress: %.1f%%", percent)
        
        logger.info("Download completed successfully")
        return True
    except Exception as e:
        logger.error("Failed to download %s: %s", url, e)
        return False

def extract_archive(archive_path, extract_dir):
    """
    Extract an archive file to the specified directory.
    
    Args:
        archive_path (str): Path to the archive file
        extract_dir (str): Directory to extract to
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    try:
        logger.info("Extracting %s to %s", archive_path, extract_dir)
        os.makedirs(extract_dir, exist_ok=True)
        
        if archive_path.endswith('.zip'):
            logger.debug("Extracting ZIP archive")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                logger.trace("Extracted files: %s", zip_ref.namelist())
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            logger.debug("Extracting TAR.GZ archive")
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_dir)
                logger.trace("Extracted files: %s", tar_ref.getnames())
        elif archive_path.endswith(('.tar.xz', '.txz')):
            logger.debug("Extracting TAR.XZ archive")
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                tar_ref.extractall(extract_dir)
                logger.trace("Extracted files: %s", tar_ref.getnames())
        elif archive_path.endswith('.tar'):
            logger.debug("Extracting TAR archive")
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_dir)
                logger.trace("Extracted files: %s", tar_ref.getnames())
        else:
            logger.error("Unsupported archive format: %s", archive_path)
            return False
            
        logger.info("Archive extracted successfully")
        return True
    except Exception as e:
        logger.error("Failed to extract %s: %s", archive_path, e)
        return False

def find_binary_in_extracted_dir(extract_dir, binary_path):
    """
    Find a binary file in the extracted directory structure.
    
    Args:
        extract_dir (str): Directory where the archive was extracted
        binary_path (str): Path or name of the binary to find
        
    Returns:
        str: Full path to the binary if found, None otherwise
    """
    logger.debug("Looking for binary %s in %s", binary_path, extract_dir)
    
    direct_path = os.path.join(extract_dir, binary_path)
    if os.path.exists(direct_path):
        logger.debug("Found binary at direct path: %s", direct_path)
        return direct_path
    
    logger.debug("Searching for binary in directory tree")
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f == os.path.basename(binary_path) or f == binary_path:
                full_path = os.path.join(root, f)
                logger.debug("Found binary at: %s", full_path)
                return full_path
    
    logger.warning("Binary %s not found in %s", binary_path, extract_dir)
    return None

def check_binary_in_path(binary_name):
    """
    Check if a binary is available in PATH.
    
    Args:
        binary_name (str): Name of the binary to check
        
    Returns:
        str: Path to the binary if found, None otherwise
    """
    logger.debug("Checking if %s is available in PATH", binary_name)
    try:
        path = shutil.which(binary_name)
        if path:
            logger.debug("Found %s at %s, verifying it works", binary_name, path)
            
            if binary_name == 'opusenc':
                # Try with --version flag first
                cmd = [path, '--version']
                result = subprocess.run(cmd, 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE, 
                                        timeout=5)
                
                # If --version fails, try without arguments (opusenc shows help/version when run without args)
                if result.returncode != 0:
                    logger.debug("opusenc --version failed, trying without arguments")
                    result = subprocess.run([path], 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE, 
                                            timeout=5)
            else:
                # For other binaries like ffmpeg
                cmd = [path, '-version']
                result = subprocess.run(cmd, 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE, 
                                        timeout=5)
            
            if result.returncode == 0:
                logger.debug("%s is available and working", binary_name)
                return path
            else:
                logger.warning("%s found but returned error code %d", binary_name, result.returncode)
        else:
            logger.debug("%s not found in PATH", binary_name)
    except Exception as e:
        logger.warning("Error checking %s: %s", binary_name, e)
        
    return None

def install_package(package_name):
    """
    Attempt to install a package using the system's package manager.
    
    Args:
        package_name (str): Name of the package to install
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    system = get_system()
    logger.info("Attempting to install %s on %s", package_name, system)
    
    try:
        if system == 'linux':
            # Try apt-get (Debian/Ubuntu)
            if shutil.which('apt-get'):
                logger.info("Installing %s using apt-get", package_name)
                subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', package_name], check=True)
                return True
            # Try yum (CentOS/RHEL)
            elif shutil.which('yum'):
                logger.info("Installing %s using yum", package_name)
                subprocess.run(['sudo', 'yum', 'install', '-y', package_name], check=True)
                return True
                
        elif system == 'darwin':
            # Try Homebrew
            if shutil.which('brew'):
                logger.info("Installing %s using homebrew", package_name)
                subprocess.run(['brew', 'install', package_name], check=True)
                return True
                
        logger.warning("Could not automatically install %s. Please install it manually.", package_name)
        return False
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install %s: %s", package_name, e)
        return False

def ensure_dependency(dependency_name, auto_download=False):
    """
    Ensure that a dependency is available, downloading it if necessary.
    
    Args:
        dependency_name (str): Name of the dependency ('ffmpeg' or 'opusenc')
        auto_download (bool): Whether to automatically download or install the dependency if not found
        
    Returns:
        str: Path to the binary if available, None otherwise
    """
    logger.info("Ensuring dependency: %s", dependency_name)
    system = get_system()
    
    if system not in ['windows', 'linux', 'darwin']:
        logger.error("Unsupported operating system: %s", system)
        return None
        
    if dependency_name not in DEPENDENCIES:
        logger.error("Unknown dependency: %s", dependency_name)
        return None
    
    # First check if it's already in PATH
    bin_name = dependency_name if dependency_name != 'opusenc' else 'opusenc'
    path_binary = check_binary_in_path(bin_name)
    if path_binary:
        logger.info("Found %s in PATH: %s", dependency_name, path_binary)
        return path_binary
    
    # Set up paths to check for previously downloaded versions
    user_data_dir = get_user_data_dir()
    dependency_info = DEPENDENCIES[dependency_name].get(system, {})
    extract_dir_name = dependency_info.get('extract_dir', dependency_name)
    binary_path = dependency_info.get('bin_path', bin_name)
    extract_dir = os.path.join(user_data_dir, extract_dir_name)
    
    # Check if we already downloaded and extracted it previously
    logger.debug("Checking for previously downloaded %s in %s", dependency_name, extract_dir)
    if os.path.exists(extract_dir):
        existing_binary = find_binary_in_extracted_dir(extract_dir, binary_path)
        if existing_binary and os.path.exists(existing_binary):
            # Verify that the binary works
            logger.info("Found previously downloaded %s: %s", dependency_name, existing_binary)
            try:
                if os.access(existing_binary, os.X_OK) or system == 'windows':
                    if system in ['linux', 'darwin']:
                        logger.debug("Ensuring executable permissions on %s", existing_binary)
                        os.chmod(existing_binary, 0o755)
                    
                    # Quick check to verify binary works
                    if dependency_name == 'opusenc':
                        cmd = [existing_binary, '--version']
                        try:
                            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                            if result.returncode == 0:
                                logger.info("Using previously downloaded %s: %s", dependency_name, existing_binary)
                                return existing_binary
                        except:
                            # If --version fails, try without arguments
                            try:
                                result = subprocess.run([existing_binary], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                                if result.returncode == 0:
                                    logger.info("Using previously downloaded %s: %s", dependency_name, existing_binary)
                                    return existing_binary
                            except:
                                pass
                    else:
                        cmd = [existing_binary, '-version']
                        try:
                            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                            if result.returncode == 0:
                                logger.info("Using previously downloaded %s: %s", dependency_name, existing_binary)
                                return existing_binary
                        except:
                            pass
                            
                    logger.warning("Previously downloaded %s exists but failed verification", dependency_name)
            except Exception as e:
                logger.warning("Error verifying downloaded binary: %s", e)
    
    # If auto_download is not enabled, don't try to install or download
    if not auto_download:
        logger.warning("%s not found in PATH and auto-download is disabled. Use --auto-download to enable automatic installation.", dependency_name)
        return None
        
    # If not in PATH, check if we should install via package manager
    if 'package' in dependency_info:
        package_name = dependency_info['package']
        logger.info("%s not found. Attempting to install %s package...", dependency_name, package_name)
        if install_package(package_name):
            path_binary = check_binary_in_path(bin_name)
            if path_binary:
                logger.info("Successfully installed %s: %s", dependency_name, path_binary)
                return path_binary
    
    # If not installable via package manager or installation failed, try downloading
    if 'url' not in dependency_info:
        logger.error("Cannot download %s for %s", dependency_name, system)
        return None
    
    # Set up download paths
    download_url = dependency_info['url']
    os.makedirs(extract_dir, exist_ok=True)
    
    # Download and extract
    archive_ext = '.zip' if download_url.endswith('zip') else '.tar.xz'
    archive_path = os.path.join(user_data_dir, f"{dependency_name}{archive_ext}")
    logger.debug("Using archive path: %s", archive_path)
    
    if download_file(download_url, archive_path):
        if extract_archive(archive_path, extract_dir):
            binary = find_binary_in_extracted_dir(extract_dir, binary_path)
            if binary:
                # Make sure it's executable on Unix-like systems
                if system in ['linux', 'darwin']:
                    logger.debug("Setting executable permissions on %s", binary)
                    os.chmod(binary, 0o755)
                logger.info("Successfully set up %s: %s", dependency_name, binary)
                return binary
    
    logger.error("Failed to set up %s", dependency_name)
    return None

def get_ffmpeg_binary(auto_download=False):
    """
    Get the path to the FFmpeg binary, downloading it if necessary.
    
    Args:
        auto_download (bool): Whether to automatically download or install if not found
    
    Returns:
        str: Path to the FFmpeg binary if available, None otherwise
    """
    return ensure_dependency('ffmpeg', auto_download)

def get_opus_binary(auto_download=False):
    """
    Get the path to the opusenc binary, downloading it if necessary.
    
    Args:
        auto_download (bool): Whether to automatically download or install if not found
    
    Returns:
        str: Path to the opusenc binary if available, None otherwise
    """
    return ensure_dependency('opusenc', auto_download)