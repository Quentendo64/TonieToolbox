#!/usr/bin/python3
"""
Dependency management for the TonieToolbox package.

This module handles the download and management of external dependencies
required by the TonieToolbox package, such as FFmpeg and opus-tools.
"""

import os
import sys
import platform
import subprocess
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import shutil
import zipfile
import tarfile
import time
import hashlib
import tempfile
import concurrent.futures
from tqdm.auto import tqdm

from .logger import get_logger
logger = get_logger(__name__)

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tonietoolbox")
LIBS_DIR = os.path.join(CACHE_DIR, "libs")

DEPENDENCIES = {
    'ffmpeg': {
        'windows': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
            'bin_path': 'bin/ffmpeg.exe',
            'extract_dir': 'ffmpeg',
            'mirrors': [
                ''
            ]
        },
        'linux': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz',
            'bin_path': 'ffmpeg',
            'extract_dir': 'ffmpeg',
            'mirrors': [
                ''
            ]
        },
        'darwin': {
            'url': 'https://evermeet.cx/ffmpeg/get/zip',
            'bin_path': 'ffmpeg',
            'extract_dir': 'ffmpeg'
        }
    },
    'opusenc': {
        'windows': {
            'url': 'https://archive.mozilla.org/pub/opus/win32/opus-tools-0.2-opus-1.3.zip',
            'bin_path': 'opusenc.exe',
            'extract_dir': 'opusenc',
            'mirrors': [
                ''
            ]
        },
        'linux': {
            'package': 'opus-tools'
        },
        'darwin': {
            'package': 'opus-tools'
        }
    },
    'mutagen': {
        'package': 'mutagen',
        'python_package': True
    }
}

def get_system():
    """Get the current operating system."""
    system = platform.system().lower()
    logger.debug("Detected operating system: %s", system)
    return system

def get_user_data_dir():
    """Get the user data directory for storing downloaded dependencies."""
    app_dir = CACHE_DIR
    logger.debug("Using application data directory: %s", app_dir)
    
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def create_session():
    """
    Create a requests session with retry capabilities.
    
    Returns:
        requests.Session: Configured session with retries
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def configure_tqdm():
    """
    Configure tqdm to ensure it displays properly in various environments.
    """
    # Check if we're in a notebook environment or standard terminal
    is_notebook = 'ipykernel' in sys.modules
    
    # Set global defaults for tqdm
    tqdm.monitor_interval = 0  # Prevent monitor thread issues
    
    # Return common kwargs for consistency
    return {
        'file': sys.stdout,
        'leave': True,
        'dynamic_ncols': True,
        'mininterval': 0.5,
        'smoothing': 0.2,
        'ncols': 100 if not is_notebook else None,
        'disable': False
    }

def download_file(url, destination, chunk_size=1024*1024, timeout=30, use_tqdm=True):
    """
    Download a file from a URL to the specified destination using optimized methods.
    
    Args:
        url (str): The URL of the file to download
        destination (str): The path to save the file to
        chunk_size (int): Size of chunks to download (default: 1MB)
        timeout (int): Connection timeout in seconds (default: 30s)
        use_tqdm (bool): Whether to display a progress bar (default: True)
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        logger.info("Downloading %s to %s", url, destination)
        headers = {'User-Agent': 'TonieToolbox-dependency-downloader/1.1'}
        
        # Create a directory for the destination file if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
        
        # Use a session for connection pooling and retries
        session = create_session()
        
        # Start with a HEAD request to get the file size before downloading
        head_response = session.head(url, headers=headers, timeout=timeout)
        head_response.raise_for_status()
        file_size = int(head_response.headers.get('Content-Length', 0))
        logger.debug("File size: %d bytes", file_size)
        
        # Now start the download
        response = session.get(url, headers=headers, stream=True, timeout=timeout)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
          # Set up the progress bar
        desc = os.path.basename(destination)
        if len(desc) > 25:
            desc = desc[:22] + "..."
        
        with open(destination, 'wb') as out_file:
            if use_tqdm and file_size > 0:
                # Force tqdm to output to console
                pbar = tqdm(
                    total=file_size, 
                    unit='B', 
                    unit_scale=True, 
                    desc=desc, 
                    **configure_tqdm()
                )
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    out_file.write(chunk)
                    pbar.update(len(chunk))
                pbar.close()
                # Print an empty line after progress is done
                print("")
            else:
                # Fallback if no file size or tqdm is disabled
                downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    out_file.write(chunk)
                    if file_size > 0:
                        percent = downloaded * 100 / file_size
                        logger.debug("Download progress: %.1f%%", percent)
        
        logger.info("Download completed successfully")
        return True
    except requests.exceptions.SSLError as e:
        logger.error("Failed to download %s: SSL Error: %s", url, e)
        # On macOS, provide more helpful error message for SSL certificate issues
        if platform.system() == 'Darwin':
            logger.error("SSL certificate verification failed on macOS. This is a known issue.")
            logger.error("You can solve this by running: /Applications/Python 3.x/Install Certificates.command")
            logger.error("Or by using the --auto-download flag which will bypass certificate verification.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error("Failed to download %s: %s", url, e)
        return False
    except Exception as e:
        logger.error("Unexpected error downloading %s: %s", url, e)
        return False

def download_file_multipart(url, destination, num_parts=4, chunk_size=1024*1024, timeout=30):
    """
    Download a file in multiple parts concurrently for better performance.
    
    Args:
        url (str): The URL of the file to download
        destination (str): The path to save the file to
        num_parts (int): Number of parts to download concurrently
        chunk_size (int): Size of chunks to download (default: 1MB)
        timeout (int): Connection timeout in seconds (default: 30s)
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        logger.info("Starting multi-part download of %s with %d parts", url, num_parts)
        headers = {'User-Agent': 'TonieToolbox-dependency-downloader/1.1'}
        
        session = create_session()
        response = session.head(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        file_size = int(response.headers.get('Content-Length', 0))
        if file_size <= 0:
            logger.warning("Multi-part download requested but Content-Length not available, falling back to regular download")
            return download_file(url, destination, chunk_size, timeout)
        
        # If file size is too small for multipart, fallback to regular download
        if file_size < num_parts * 1024 * 1024 * 5:  # Less than 5MB per part
            logger.debug("File size too small for efficient multi-part download, using regular download")
            return download_file(url, destination, chunk_size, timeout)
        
        # Calculate part sizes
        part_size = file_size // num_parts
        ranges = [(i * part_size, min((i + 1) * part_size - 1, file_size - 1)) 
                 for i in range(num_parts)]
        if ranges[-1][1] < file_size - 1:
            ranges[-1] = (ranges[-1][0], file_size - 1)
        
        # Create temporary directory for parts
        temp_dir = tempfile.mkdtemp(prefix="tonietoolbox_download_")
        part_files = [os.path.join(temp_dir, f"part_{i}") for i in range(num_parts)]
        
        # Define the download function for each part
        def download_part(part_idx):
            start, end = ranges[part_idx]
            part_path = part_files[part_idx]
            
            headers_with_range = headers.copy()
            headers_with_range['Range'] = f'bytes={start}-{end}'
            
            part_size = end - start + 1
            
            try:
                response = session.get(url, headers=headers_with_range, stream=True, timeout=timeout)
                response.raise_for_status()
                  # Set up progress bar for this part
                desc = f"Part {part_idx+1}/{num_parts}"
                with tqdm(
                    total=part_size, 
                    unit='B', 
                    unit_scale=True, 
                    desc=desc, 
                    position=part_idx,
                    **configure_tqdm()
                ) as pbar:
                    with open(part_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if not chunk:
                                continue
                            f.write(chunk)
                            pbar.update(len(chunk))
                
                return True
            except Exception as e:
                logger.error("Error downloading part %d: %s", part_idx, str(e))
                return False
        
        # Download all parts in parallel
        logger.info("Starting concurrent download of %d parts...", num_parts)
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_parts) as executor:
            futures = [executor.submit(download_part, i) for i in range(num_parts)]
            all_successful = all(future.result() for future in concurrent.futures.as_completed(futures))
        
        if not all_successful:
            logger.error("One or more parts failed to download")
            
            # Clean up
            for part_file in part_files:
                if os.path.exists(part_file):
                    os.remove(part_file)
            os.rmdir(temp_dir)
            
            return False
        
        # Combine all parts into the final file
        logger.info("All parts downloaded successfully, combining into final file")
        with open(destination, 'wb') as outfile:
            for part_file in part_files:
                with open(part_file, 'rb') as infile:
                    shutil.copyfileobj(infile, outfile)
                os.remove(part_file)
        
        # Clean up temp directory
        os.rmdir(temp_dir)
        
        logger.info("Multi-part download completed successfully")
        return True
    
    except Exception as e:
        logger.error("Failed multi-part download: %s", str(e))
        # Fall back to regular download
        logger.info("Falling back to regular download method")
        return download_file(url, destination, chunk_size, timeout)

def smart_download(url, destination, use_multipart=True, min_size_for_multipart=20*1024*1024, num_parts=4, use_tqdm=True):
    """
    Smart download function that selects the best download method based on file size.
    
    Args:
        url (str): The URL of the file to download
        destination (str): The path to save the file to
        use_multipart (bool): Whether to allow multi-part downloads (default: True)
        min_size_for_multipart (int): Minimum file size in bytes to use multi-part download (default: 20MB)
        num_parts (int): Number of parts for multi-part download (default: 4)
        use_tqdm (bool): Whether to display progress bars (default: True)
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        # Check if multipart is enabled and get file size
        if not use_multipart:
            return download_file(url, destination, use_tqdm=use_tqdm)
            
        # Create session and check file size
        session = create_session()
        response = session.head(url, timeout=30)
        file_size = int(response.headers.get('Content-Length', 0))
        
        if file_size >= min_size_for_multipart and use_multipart:
            logger.info("File size (%d bytes) is suitable for multi-part download", file_size)
            print(f"Starting multi-part download of {os.path.basename(destination)} ({file_size/1024/1024:.1f} MB)")
            return download_file_multipart(url, destination, num_parts=num_parts)
        else:
            logger.debug("Using standard download method (file size: %d bytes)", file_size)
            return download_file(url, destination, use_tqdm=use_tqdm)
    except Exception as e:
        logger.warning("Error determining download method: %s, falling back to standard download", e)
        return download_file(url, destination, use_tqdm=use_tqdm)

def download_with_mirrors(url, destination, mirrors=None):
    """
    Try downloading a file from the primary URL and fall back to mirrors if needed.
    
    Args:
        url (str): Primary URL to download from
        destination (str): Path to save the file to
        mirrors (list): List of alternative URLs to try if primary fails
        
    Returns:
        bool: True if download was successful from any source, False otherwise
    """
    logger.debug("Starting download with primary URL and %s mirrors", 
               "0" if mirrors is None else len(mirrors))
    
    # Try the primary URL first
    if smart_download(url, destination):
        logger.debug("Download successful from primary URL")
        return True
    
    # If primary URL fails and we have mirrors, try them
    if mirrors:
        for i, mirror_url in enumerate(mirrors, 1):
            logger.info("Primary download failed, trying mirror %d of %d", 
                      i, len(mirrors))
            if smart_download(mirror_url, destination):
                logger.info("Download successful from mirror %d", i)
                return True
    
    logger.error("All download attempts failed")
    return False

def extract_archive(archive_path, extract_dir):
    """
    Extract an archive file to the specified directory using optimized methods.
    
    Args:
        archive_path (str): Path to the archive file
        extract_dir (str): Directory to extract to
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    try:
        logger.info("Extracting %s to %s", archive_path, extract_dir)
        os.makedirs(extract_dir, exist_ok=True)
        
        # Extract to a secure temporary directory
        temp_extract_dir = tempfile.mkdtemp(prefix="tonietoolbox_extract_")
        logger.debug("Using temporary extraction directory: %s", temp_extract_dir)
        
        if archive_path.endswith('.zip'):
            logger.debug("Extracting ZIP archive")
            try:
                # Use a with statement for proper cleanup
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # Get the list of files for informational purposes
                    files_extracted = zip_ref.namelist()
                    total_size = sum(info.file_size for info in zip_ref.infolist())
                    logger.debug("ZIP contains %d files, total size: %d bytes", 
                              len(files_extracted), total_size)
                    
                    # Extract with progress indication for large archives
                    if total_size > 50*1024*1024:  # 50 MB
                        # Use configure_tqdm() for consistent parameters
                        tqdm_params = configure_tqdm()
                        with tqdm(
                            total=total_size, 
                            unit='B', 
                            unit_scale=True, 
                            desc="Extracting ZIP",
                            **tqdm_params
                        ) as pbar:
                            for file in zip_ref.infolist():
                                zip_ref.extract(file, temp_extract_dir)
                                pbar.update(file.file_size)
                        # Print empty line after progress completion
                        print("")
                    else:
                        zip_ref.extractall(temp_extract_dir)
            except zipfile.BadZipFile as e:
                logger.error("Bad ZIP file: %s", str(e))
                return False
                
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            logger.debug("Extracting TAR.GZ archive")
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                files_extracted = tar_ref.getnames()
                logger.debug("TAR.GZ contains %d files", len(files_extracted))
                tar_ref.extractall(path=temp_extract_dir)
                
        elif archive_path.endswith(('.tar.xz', '.txz')):
            logger.debug("Extracting TAR.XZ archive")
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                files_extracted = tar_ref.getnames()
                logger.debug("TAR.XZ contains %d files", len(files_extracted))
                tar_ref.extractall(path=temp_extract_dir)
                
        elif archive_path.endswith('.tar'):
            logger.debug("Extracting TAR archive")
            with tarfile.open(archive_path, 'r') as tar_ref:
                files_extracted = tar_ref.getnames()
                logger.debug("TAR contains %d files", len(files_extracted))
                tar_ref.extractall(path=temp_extract_dir)
        else:
            logger.error("Unsupported archive format: %s", archive_path)
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return False
            
        logger.info("Archive extracted successfully")
        
        # Fix FFmpeg nested directory issue by moving binary files to the correct location
        dependency_name = os.path.basename(extract_dir)
        if dependency_name == 'ffmpeg':
            # Check for common nested directory structures for FFmpeg
            if os.path.exists(os.path.join(temp_extract_dir, "ffmpeg-master-latest-win64-gpl", "bin")):
                # Windows FFmpeg path
                bin_dir = os.path.join(temp_extract_dir, "ffmpeg-master-latest-win64-gpl", "bin")
                logger.debug("Found nested FFmpeg bin directory: %s", bin_dir)
                
                # Move all files from bin directory to the main dependency directory
                for file in os.listdir(bin_dir):
                    src = os.path.join(bin_dir, file)
                    dst = os.path.join(extract_dir, file)
                    logger.debug("Moving %s to %s", src, dst)
                    shutil.move(src, dst)
            
            elif os.path.exists(os.path.join(temp_extract_dir, "ffmpeg-master-latest-linux64-gpl", "bin")):
                # Linux FFmpeg path
                bin_dir = os.path.join(temp_extract_dir, "ffmpeg-master-latest-linux64-gpl", "bin")
                logger.debug("Found nested FFmpeg bin directory: %s", bin_dir)
                
                # Move all files from bin directory to the main dependency directory
                for file in os.listdir(bin_dir):
                    src = os.path.join(bin_dir, file)
                    dst = os.path.join(extract_dir, file)
                    logger.debug("Moving %s to %s", src, dst)
                    shutil.move(src, dst)
            else:
                # Check for any directory with a 'bin' subdirectory
                for root, dirs, _ in os.walk(temp_extract_dir):
                    if "bin" in dirs:
                        bin_dir = os.path.join(root, "bin")
                        logger.debug("Found nested bin directory: %s", bin_dir)
                        
                        # Move all files from bin directory to the main dependency directory
                        for file in os.listdir(bin_dir):
                            src = os.path.join(bin_dir, file)
                            dst = os.path.join(extract_dir, file)
                            logger.debug("Moving %s to %s", src, dst)
                            shutil.move(src, dst)
                        break
                else:
                    # If no bin directory was found, just move everything from the temp directory
                    logger.debug("No bin directory found, moving all files from temp directory")
                    for item in os.listdir(temp_extract_dir):
                        src = os.path.join(temp_extract_dir, item)
                        dst = os.path.join(extract_dir, item)
                        if os.path.isfile(src):
                            logger.debug("Moving file %s to %s", src, dst)
                            shutil.move(src, dst)
        else:
            # For non-FFmpeg dependencies, just move all files from temp directory
            for item in os.listdir(temp_extract_dir):
                src = os.path.join(temp_extract_dir, item)
                dst = os.path.join(extract_dir, item)
                if os.path.isfile(src):
                    logger.debug("Moving file %s to %s", src, dst)
                    shutil.move(src, dst)
                else:
                    logger.debug("Moving directory %s to %s", src, dst)
                    # If destination already exists, remove it first
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.move(src, dst)
        
        # Clean up the temporary extraction directory
        try:
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            logger.debug("Removed temporary extraction directory")
        except Exception as e:
            logger.warning("Failed to remove temporary extraction directory: %s", e)
        
        # Remove the archive file after successful extraction
        try:
            logger.debug("Removing archive file: %s", archive_path)
            os.remove(archive_path)
            logger.debug("Archive file removed successfully")
        except Exception as e:
            logger.warning("Failed to remove archive file: %s (error: %s)", archive_path, e)
            # Continue even if we couldn't remove the file
        
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

def ensure_dependency(dependency_name, auto_download=False):
    """
    Ensure that a dependency is available, downloading it if necessary.
    
    Args:
        dependency_name (str): Name of the dependency ('ffmpeg' or 'opusenc')
        auto_download (bool): Whether to automatically download or install the dependency if not found
        
    Returns:
        str: Path to the binary if available, None otherwise
    """
    logger.debug("Ensuring dependency: %s", dependency_name)
    system = get_system()
    
    if system not in ['windows', 'linux', 'darwin']:
        logger.error("Unsupported operating system: %s", system)
        return None
        
    if dependency_name not in DEPENDENCIES:
        logger.error("Unknown dependency: %s", dependency_name)
        return None
    
    # Set up paths to check for previously downloaded versions
    user_data_dir = get_user_data_dir()
    dependency_info = DEPENDENCIES[dependency_name].get(system, {})
    binary_path = dependency_info.get('bin_path', dependency_name if dependency_name != 'opusenc' else 'opusenc')
    
    # Define bin_name early so it's available in all code paths
    bin_name = dependency_name if dependency_name != 'opusenc' else 'opusenc'
    
    # Create a specific folder for this dependency
    dependency_dir = os.path.join(user_data_dir, 'libs', dependency_name)
    
    # First priority: Check if we already downloaded and extracted it previously
    # When auto_download is True, we'll skip this check and download fresh versions
    if not auto_download:
        logger.debug("Checking for previously downloaded %s in %s", dependency_name, dependency_dir)
        if os.path.exists(dependency_dir):
            existing_binary = find_binary_in_extracted_dir(dependency_dir, binary_path)
            if existing_binary and os.path.exists(existing_binary):
                # Verify that the binary works
                logger.debug("Found previously downloaded %s: %s", dependency_name, existing_binary)
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
                                    logger.debug("Using previously downloaded %s: %s", dependency_name, existing_binary)
                                    return existing_binary
                            except:
                                # If --version fails, try without arguments
                                try:
                                    result = subprocess.run([existing_binary], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                                    if result.returncode == 0:
                                        logger.debug("Using previously downloaded %s: %s", dependency_name, existing_binary)
                                        return existing_binary
                                except:
                                    pass
                        else:
                            cmd = [existing_binary, '-version']
                            try:
                                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                                if result.returncode == 0:
                                    logger.debug("Using previously downloaded %s: %s", dependency_name, existing_binary)
                                    return existing_binary
                            except:
                                pass
                                
                        logger.warning("Previously downloaded %s exists but failed verification", dependency_name)
                except Exception as e:
                    logger.warning("Error verifying downloaded binary: %s", e)

        # Second priority: Check if it's in PATH (only if auto_download is False)
        path_binary = check_binary_in_path(bin_name)
        if path_binary:
            logger.info("Found %s in PATH: %s", dependency_name, path_binary)
            return path_binary
    else:
        logger.info("Auto-download enabled, forcing download/installation of %s", dependency_name)
        # If there's an existing download directory, rename or remove it
        if os.path.exists(dependency_dir):
            try:
                backup_dir = f"{dependency_dir}_backup_{int(time.time())}"
                logger.debug("Moving existing dependency directory to: %s", backup_dir)
                os.rename(dependency_dir, backup_dir)
            except Exception as e:
                logger.warning("Failed to rename existing dependency directory: %s", e)
                try:
                    logger.debug("Trying to remove existing dependency directory")
                    shutil.rmtree(dependency_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning("Failed to remove existing dependency directory: %s", e)
    
    # If auto_download is not enabled, don't try to install or download
    if not auto_download:
        logger.warning("%s not found in libs directory or PATH and auto-download is disabled. Use --auto-download to enable automatic installation.", dependency_name)
        return None
        
    # If not in libs or PATH, check if we should install via package manager
    if 'package' in dependency_info:
        package_name = dependency_info['package']
        logger.info("%s not found or forced download. Attempting to install %s package...", dependency_name, package_name)
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
    mirrors = dependency_info.get('mirrors', [])
    
    # Create dependency-specific directory
    os.makedirs(dependency_dir, exist_ok=True)
    
    # Download and extract
    archive_ext = '.zip' if download_url.endswith('zip') else '.tar.xz'
    archive_path = os.path.join(dependency_dir, f"{dependency_name}{archive_ext}")
    logger.debug("Using archive path: %s", archive_path)
    
    # Use our improved download function with mirrors and tqdm progress bar
    print(f"Downloading {dependency_name}...")
    if download_with_mirrors(download_url, archive_path, mirrors):
        print(f"Extracting {dependency_name}...")
        if extract_archive(archive_path, dependency_dir):
            binary = find_binary_in_extracted_dir(dependency_dir, binary_path)
            if binary:
                # Make sure it's executable on Unix-like systems
                if system in ['linux', 'darwin']:
                    logger.debug("Setting executable permissions on %s", binary)
                    os.chmod(binary, 0o755)
                logger.info("Successfully set up %s: %s", dependency_name, binary)
                return binary
    
    logger.error("Failed to set up %s", dependency_name)
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

def get_ffmpeg_binary(auto_download=False):
    """
    Get the path to the FFmpeg binary, downloading it if necessary and allowed.
    
    Args:
        auto_download (bool): Whether to automatically download FFmpeg if not found (defaults to False)
        
    Returns:
        str: Path to the FFmpeg binary, or None if not available
    """
    logger.debug("Getting FFmpeg binary")
    
    # Define the expected binary path
    local_dir = os.path.join(get_user_data_dir(), 'libs', 'ffmpeg')
    if sys.platform == 'win32':
        binary_path = os.path.join(local_dir, 'ffmpeg.exe')
    else:
        binary_path = os.path.join(local_dir, 'ffmpeg')
    
    # Check if binary exists
    if os.path.exists(binary_path) and os.path.isfile(binary_path):
        logger.debug("FFmpeg binary found at %s", binary_path)
        return binary_path
    
    # Check if a system-wide FFmpeg is available
    try:
        if sys.platform == 'win32':
            # On Windows, look for ffmpeg in PATH
            from shutil import which
            system_binary = which('ffmpeg')
            if system_binary:
                logger.debug("System-wide FFmpeg found at %s", system_binary)
                return system_binary
        else:
            # On Unix-like systems, use 'which' command
            system_binary = subprocess.check_output(['which', 'ffmpeg']).decode('utf-8').strip()
            if system_binary:
                logger.debug("System-wide FFmpeg found at %s", system_binary)
                return system_binary
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.debug("No system-wide FFmpeg found")
    
    # Download if allowed
    if auto_download:
        logger.info("Auto-download enabled, forcing download/installation of ffmpeg")
        print("Downloading ffmpeg...")
        
        # Create directory if it doesn't exist
        os.makedirs(local_dir, exist_ok=True)
        
        # Download FFmpeg based on platform
        if sys.platform == 'win32':
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            archive_path = os.path.join(local_dir, "ffmpeg.zip")
            
            # Download the file
            logger.info("Downloading %s to %s", url, archive_path)
            download_with_mirrors(url, archive_path)
            
            # Extract the archive
            print("Extracting ffmpeg...")
            logger.info("Extracting %s to %s", archive_path, local_dir)
            extract_archive(archive_path, local_dir)
            
            # Find the binary in the extracted files
            for root, dirs, files in os.walk(local_dir):
                if 'ffmpeg.exe' in files:
                    binary_path = os.path.join(root, 'ffmpeg.exe')
                    break
            
            # Verify the binary exists
            if not os.path.exists(binary_path):
                logger.error("FFmpeg binary not found after extraction")
                return None
                
            logger.info("Successfully set up ffmpeg: %s", binary_path)
            return binary_path
            
        elif sys.platform == 'darwin':  # macOS
            url = "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"
            archive_path = os.path.join(local_dir, "ffmpeg.zip")
            
            # Download and extract
            download_with_mirrors(url, archive_path)
            extract_archive(archive_path, local_dir)
            
            # Make binary executable
            binary_path = os.path.join(local_dir, "ffmpeg")
            os.chmod(binary_path, 0o755)
            logger.info("Successfully set up ffmpeg: %s", binary_path)
            return binary_path
            
        else:  # Linux and others
            url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
            archive_path = os.path.join(local_dir, "ffmpeg.tar.xz")
            
            # Download and extract
            download_with_mirrors(url, archive_path)
            extract_archive(archive_path, local_dir)
            
            # Find the binary in the extracted files
            for root, dirs, files in os.walk(local_dir):
                if 'ffmpeg' in files:
                    binary_path = os.path.join(root, 'ffmpeg')
                    os.chmod(binary_path, 0o755)
                    logger.info("Successfully set up ffmpeg: %s", binary_path)
                    return binary_path
            
            logger.error("FFmpeg binary not found after extraction")
            return None
    else:
        logger.warning("FFmpeg is not available and --auto-download is not used.")
        return None

def get_opus_binary(auto_download=False):
    """
    Get the path to the Opus binary, downloading it if necessary and allowed.
    
    Args:
        auto_download (bool): Whether to automatically download Opus if not found (defaults to False)
        
    Returns:
        str: Path to the Opus binary, or None if not available
    """
    logger.debug("Getting Opus binary")
    
    # Define the expected binary path
    local_dir = os.path.join(get_user_data_dir(), 'libs', 'opusenc')
    if sys.platform == 'win32':
        binary_path = os.path.join(local_dir, 'opusenc.exe')
    else:
        binary_path = os.path.join(local_dir, 'opusenc')
    
    # Check if binary exists
    if os.path.exists(binary_path) and os.path.isfile(binary_path):
        logger.debug("Opus binary found at %s", binary_path)
        return binary_path
    
    # Check if a system-wide Opus is available
    try:
        if sys.platform == 'win32':
            # On Windows, look for opusenc in PATH
            from shutil import which
            system_binary = which('opusenc')
            if system_binary:
                logger.debug("System-wide Opus found at %s", system_binary)
                return system_binary
        else:
            # On Unix-like systems, use 'which' command
            system_binary = subprocess.check_output(['which', 'opusenc']).decode('utf-8').strip()
            if system_binary:
                logger.debug("System-wide Opus found at %s", system_binary)
                return system_binary
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.debug("No system-wide Opus found")
    
    # Download if allowed
    if auto_download:
        logger.info("Auto-download enabled, forcing download/installation of opusenc")
        print("Downloading opusenc...")
        
        # Create directory if it doesn't exist
        os.makedirs(local_dir, exist_ok=True)
        
        # Download Opus based on platform
        if sys.platform == 'win32':
            url = "https://archive.mozilla.org/pub/opus/win32/opus-tools-0.2-opus-1.3.zip"
            archive_path = os.path.join(local_dir, "opusenc.zip")
        else:
            # For non-Windows, we'll need to compile from source or find precompiled binaries
            logger.error("Automatic download of Opus for non-Windows platforms is not supported yet")
            return None
            
        # Download the file
        logger.info("Downloading %s to %s", url, archive_path)
        download_with_mirrors(url, archive_path)
        
        # Extract the archive
        print("Extracting opusenc...")
        logger.info("Extracting %s to %s", archive_path, local_dir)
        extract_archive(archive_path, local_dir)
        
        # For Windows, the binary should now be in the directory
        if sys.platform == 'win32':
            binary_path = os.path.join(local_dir, 'opusenc.exe')
            if not os.path.exists(binary_path):
                # Try to find it in the extracted directory structure
                for root, dirs, files in os.walk(local_dir):
                    if 'opusenc.exe' in files:
                        binary_path = os.path.join(root, 'opusenc.exe')
                        break
        
        # Verify the binary exists
        if not os.path.exists(binary_path):
            logger.error("Opus binary not found after extraction")
            return None
            
        logger.info("Successfully set up opusenc: %s", binary_path)
        return binary_path
    else:
        logger.warning("Opus is not available and --auto-download is not used.")
        return None

def get_opus_version(opus_binary=None):
    """
    Get the version of opusenc.
    
    Args:
        opus_binary: Path to the opusenc binary
        
    Returns:
        str: The version string of opusenc, or a fallback string if the version cannot be determined
    """
    import subprocess
    import re
    
    logger = get_logger('dependency_manager')
    
    if opus_binary is None:
        opus_binary = get_opus_binary()
    
    if opus_binary is None:
        logger.debug("opusenc binary not found, using fallback version string")
        return "opusenc from opus-tools XXX"  # Fallback
    
    try:
        # Run opusenc --version and capture output
        result = subprocess.run([opus_binary, "--version"], 
                                capture_output=True, text=True, check=False)
        
        # Extract version information from output
        version_output = result.stdout.strip() or result.stderr.strip()
        
        if version_output:
            # Try to extract just the version information using regex
            match = re.search(r"(opusenc.*)", version_output)
            if match:
                return match.group(1)
            else:
                return version_output.splitlines()[0]  # Use first line
        else:
            logger.debug("Could not determine opusenc version, using fallback")
            return "opusenc from opus-tools XXX"  # Fallback
    
    except Exception as e:
        logger.debug(f"Error getting opusenc version: {str(e)}")
        return "opusenc from opus-tools XXX"  # Fallback

def check_python_package(package_name):
    """
    Check if a Python package is installed.
    
    Args:
        package_name (str): Name of the package to check
        
    Returns:
        bool: True if the package is installed, False otherwise
    """
    logger.debug("Checking if Python package is installed: %s", package_name)
    try:
        __import__(package_name)
        logger.debug("Python package %s is installed", package_name)
        return True
    except ImportError:
        logger.debug("Python package %s is not installed", package_name)
        return False

def install_python_package(package_name):
    """
    Attempt to install a Python package using pip.
    
    Args:
        package_name (str): Name of the package to install
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    logger.info("Attempting to install Python package: %s", package_name)
    try:
        import subprocess
        
        # Try to install the package using pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info("Successfully installed Python package: %s", package_name)
        return True
    except Exception as e:
        logger.error("Failed to install Python package %s: %s", package_name, str(e))
        return False

def ensure_mutagen(auto_install=True):
    """
    Ensure that the Mutagen library is available, installing it if necessary and allowed.
    
    Args:
        auto_install (bool): Whether to automatically install Mutagen if not found (defaults to True)
        
    Returns:
        bool: True if Mutagen is available, False otherwise
    """
    logger.debug("Checking if Mutagen is available")
    
    try:
        import mutagen
        logger.debug("Mutagen is already installed")
        return True
    except ImportError:
        logger.debug("Mutagen is not installed")
        
        if auto_install:
            logger.info("Auto-install enabled, attempting to install Mutagen")
            if install_python_package('mutagen'):
                try:
                    import mutagen
                    logger.info("Successfully installed and imported Mutagen")
                    return True
                except ImportError:
                    logger.error("Mutagen was installed but could not be imported")
            else:
                logger.error("Failed to install Mutagen")
        else:
            logger.warning("Mutagen is not installed and --auto-download is not used.")
        
        return False

def is_mutagen_available():
    """
    Check if the Mutagen library is available.
    
    Returns:
        bool: True if Mutagen is available, False otherwise
    """
    return check_python_package('mutagen')