#!/usr/bin/python3
"""
TeddyCloud API client for TonieToolbox.
Handles uploading .taf files to a TeddyCloud instance and interacting with the TeddyCloud API.
"""

import os
import sys
import json
import logging
import urllib.parse
import urllib.request
import urllib.error
import base64
import mimetypes
import ssl
import time
import socket
import glob
from typing import Optional, Dict, Any, Tuple, List

from .logger import get_logger

logger = get_logger('teddycloud')

# Default timeout settings (in seconds)
DEFAULT_CONNECTION_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 300  # 5 minutes
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # seconds

# Add function to get file paths for any file type (not just audio)
def get_file_paths(input_pattern):
    """
    Get file paths based on a pattern, without filtering by file type.
    This is different from audio_conversion.get_input_files as it doesn't filter for audio files.
    
    Args:
        input_pattern: Input file pattern or direct file path
        
    Returns:
        list: List of file paths
    """
    logger.debug("Getting file paths for pattern: %s", input_pattern)
    
    if input_pattern.endswith(".lst"):
        logger.debug("Processing list file: %s", input_pattern)
        list_dir = os.path.dirname(os.path.abspath(input_pattern))
        file_paths = []
        
        with open(input_pattern, 'r', encoding='utf-8') as file_list:
            for line_num, line in enumerate(file_list, 1):
                fname = line.strip()
                if not fname or fname.startswith('#'):  # Skip empty lines and comments
                    continue
                
                # Remove any quote characters from path
                fname = fname.strip('"\'')
                    
                # Check if the path is absolute or has a drive letter (Windows)
                if os.path.isabs(fname) or (len(fname) > 1 and fname[1] == ':'):
                    full_path = fname  # Use as is if it's an absolute path
                    logger.trace("Using absolute path from list: %s", full_path)
                else:
                    full_path = os.path.join(list_dir, fname)
                    logger.trace("Using relative path from list: %s", full_path)
                
                # Handle directory paths by finding all files in the directory
                if os.path.isdir(full_path):
                    logger.debug("Path is a directory, finding files in: %s", full_path)
                    dir_glob = os.path.join(full_path, "*")
                    dir_files = sorted(glob.glob(dir_glob))
                    if dir_files:
                        file_paths.extend([f for f in dir_files if os.path.isfile(f)])
                        logger.debug("Found %d files in directory", len(dir_files))
                    else:
                        logger.warning("No files found in directory at line %d: %s", line_num, full_path)
                elif os.path.isfile(full_path):
                    file_paths.append(full_path)
                else:
                    logger.warning("File not found at line %d: %s", line_num, full_path)
        
        logger.debug("Found %d files in list file", len(file_paths))
        return file_paths
    else:
        # Process as glob pattern
        logger.debug("Processing glob pattern: %s", input_pattern)
        file_paths = sorted([f for f in glob.glob(input_pattern) if os.path.isfile(f)])
        
        if not file_paths:
            # Try with explicit directory if the pattern didn't work
            # This is helpful for Windows paths with backslashes
            dir_name = os.path.dirname(input_pattern)
            file_name = os.path.basename(input_pattern)
            if dir_name:
                alt_pattern = os.path.join(dir_name, file_name)
                file_paths = sorted([f for f in glob.glob(alt_pattern) if os.path.isfile(f)])
            
            # If still no files, try with the literal path (no glob interpretation)
            if not file_paths and os.path.isfile(input_pattern):
                file_paths = [input_pattern]
        
        logger.debug("Found %d files matching pattern", len(file_paths))
        return file_paths

class ProgressTracker:
    """Helper class to track and display upload progress."""
    
    def __init__(self, total_size, file_name):
        """
        Initialize progress tracker.
        
        Args:
            total_size: Total size of the file in bytes
            file_name: Name of the file being uploaded
        """
        self.total_size = total_size
        self.file_name = file_name
        self.uploaded = 0
        self.start_time = time.time()
        self.last_update = 0
        self.last_percent = 0
        
    def update(self, chunk_size):
        """
        Update progress by the given chunk size.
        
        Args:
            chunk_size: Size of the chunk that was uploaded
        """
        self.uploaded += chunk_size
        current_time = time.time()
        
        # Limit updates to max 10 per second to avoid flooding console
        if current_time - self.last_update >= 0.1:
            percent = min(100, int((self.uploaded / self.total_size) * 100))
            
            # Only update if percentage changed or it's been more than a second
            if percent != self.last_percent or current_time - self.last_update >= 1:
                self.print_progress(percent)
                self.last_update = current_time
                self.last_percent = percent
    
    def print_progress(self, percent):
        """
        Print progress bar.
        
        Args:
            percent: Current percentage of upload completed
        """
        bar_length = 30
        filled_length = int(bar_length * percent // 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        # Calculate speed
        elapsed_time = max(0.1, time.time() - self.start_time)
        speed = self.uploaded / elapsed_time / 1024  # KB/s
        
        # Format speed based on magnitude
        if speed >= 1024:
            speed_str = f"{speed/1024:.2f} MB/s"
        else:
            speed_str = f"{speed:.2f} KB/s"
        
        # Format size
        if self.total_size >= 1048576:  # 1 MB
            size_str = f"{self.uploaded/1048576:.2f}/{self.total_size/1048576:.2f} MB"
        else:
            size_str = f"{self.uploaded/1024:.2f}/{self.total_size/1024:.2f} KB"
        
        # Calculate remaining time
        if percent > 0:
            remaining = (self.total_size - self.uploaded) / (self.uploaded / elapsed_time)
            if remaining > 60:
                remaining_str = f"{int(remaining/60)}m {int(remaining%60)}s"
            else:
                remaining_str = f"{int(remaining)}s"
        else:
            remaining_str = "calculating..."
        
        # Print progress bar
        sys.stdout.write(f"\r{self.file_name}: |{bar}| {percent}% {size_str} {speed_str} ETA: {remaining_str}")
        sys.stdout.flush()
        
        if percent >= 100:
            sys.stdout.write("\n")
            sys.stdout.flush()

class ProgressTrackerHandler(urllib.request.HTTPHandler):
    """Custom HTTP handler to track upload progress."""
    
    def __init__(self, tracker=None):
        """
        Initialize handler.
        
        Args:
            tracker: ProgressTracker instance to use for tracking
        """
        super().__init__()
        self.tracker = tracker
    
    def http_request(self, req):
        """
        Hook into HTTP request to track upload progress.
        
        Args:
            req: HTTP request object
        
        Returns:
            Modified request object
        """
        if self.tracker and req.data:
            req.add_unredirected_header('Content-Length', str(len(req.data)))
            old_data = req.data
            
            # Replace data with an iterator that tracks progress
            def data_iterator():
                chunk_size = 8192
                total_sent = 0
                data = old_data
                while total_sent < len(data):
                    chunk = data[total_sent:total_sent + chunk_size]
                    total_sent += len(chunk)
                    self.tracker.update(len(chunk))
                    yield chunk
            
            req.data = data_iterator()
        
        return req

class TeddyCloudClient:
    """Client for interacting with TeddyCloud API."""
    
    def __init__(self, base_url: str, ignore_ssl_verify: bool = False, 
                 connection_timeout: int = DEFAULT_CONNECTION_TIMEOUT, 
                 read_timeout: int = DEFAULT_READ_TIMEOUT, 
                 max_retries: int = DEFAULT_MAX_RETRIES, 
                 retry_delay: int = DEFAULT_RETRY_DELAY):
        """
        Initialize the TeddyCloud client.
        
        Args:
            base_url: Base URL of the TeddyCloud instance (e.g., https://teddycloud.example.com)
            ignore_ssl_verify: If True, SSL certificate verification will be disabled (useful for self-signed certificates)
            connection_timeout: Timeout for establishing a connection
            read_timeout: Timeout for reading data from the server
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries
        """
        self.base_url = base_url.rstrip('/')
        self.ignore_ssl_verify = ignore_ssl_verify
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Create SSL context if needed
        self.ssl_context = None
        if ignore_ssl_verify:
            logger.warning("SSL certificate verification is disabled. This is insecure!")
            self.ssl_context = ssl._create_unverified_context()
            
    def _urlopen(self, req):
        """Helper method to open URLs with optional SSL verification bypass and retry logic."""
        for attempt in range(self.max_retries):
            try:
                if self.ignore_ssl_verify:
                    return urllib.request.urlopen(req, context=self.ssl_context, timeout=self.connection_timeout)
                else:
                    return urllib.request.urlopen(req, timeout=self.connection_timeout)
            except (urllib.error.URLError, socket.timeout) as e:
                logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, self.max_retries, e)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
            except Exception as e:
                logger.error("Unexpected error during request: %s", e)
                raise
        
    def get_tag_index(self) -> Optional[list]:
        """
        Get list of tags from TeddyCloud.
        
        Returns:
            List of tags or None if request failed
        """
        try:
            url = f"{self.base_url}/api/getTagIndex"
            headers = {'Content-Type': 'application/json'}
            
            req = urllib.request.Request(url, headers=headers)
            
            with self._urlopen(req) as response:
                tags = json.loads(response.read().decode('utf-8'))
                logger.debug("Found %d tags", len(tags))
                return tags
                
        except urllib.error.HTTPError as e:
            logger.error("Failed to get tags: %s", e)
            return None
        except Exception as e:
            logger.error("Error getting tags: %s", e)
            return None
            
    def upload_file(self, file_path: str, special_folder: str = None, path: str = None, show_progress: bool = True) -> bool:
        """
        Upload a .taf or image file to TeddyCloud.
        
        Args:
            file_path: Path to the file to upload (.taf, .jpg, .jpeg, .png)
            special_folder: Special folder to upload to (currently only 'library' is supported)
            path: Path where to write the file within the special folder
            show_progress: Whether to show a progress bar during upload
        
        Returns:
            True if upload was successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error("File does not exist: %s", file_path)
                return False
            
            # Check for supported file types
            file_ext = os.path.splitext(file_path.lower())[1]
            is_taf = file_ext == '.taf'
            is_image = file_ext in ['.jpg', '.jpeg', '.png']
            
            if not (is_taf or is_image):
                logger.error("Unsupported file type %s: %s", file_ext, file_path)
                return False
                
            # Read file and prepare for upload
            file_size = os.path.getsize(file_path)
            logger.info("File size: %.2f MB", file_size / (1024 * 1024))
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
                
            filename = os.path.basename(file_path)
            
            # Build multipart form data
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            headers = {
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'User-Agent': 'TonieToolbox/1.0'
            }
            
            # Start request data with boundary
            body = []
            body.append(f'--{boundary}'.encode())
            
            # Set appropriate content type based on file extension
            content_type = 'application/octet-stream'
            if is_image:
                if file_ext == '.jpg' or file_ext == '.jpeg':
                    content_type = 'image/jpeg'
                elif file_ext == '.png':
                    content_type = 'image/png'
            
            body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
            body.append(f'Content-Type: {content_type}'.encode())
            body.append(b'')
            body.append(file_content)
            body.append(f'--{boundary}--'.encode())
            body.append(b'')
            
            # Join all parts with CRLF
            body = b'\r\n'.join(body)
            
            # Build the upload URL with query parameters
            if special_folder or path:
                query_params = []
                
                if special_folder:
                    query_params.append(f"special={urllib.parse.quote(special_folder)}")
                
                if path:
                    query_params.append(f"path={urllib.parse.quote(path)}")
                
                query_string = "&".join(query_params)
                upload_url = f"{self.base_url}/api/fileUpload?{query_string}"
                logger.debug("Using endpoint with params: %s", upload_url)
            else:
                # Fallback to previous endpoint for backward compatibility
                upload_url = f"{self.base_url}/api/v1/audio"
                logger.debug("Using legacy endpoint: %s", upload_url)
            
            # Setup progress tracking if requested
            if show_progress:
                tracker = ProgressTracker(total_size=len(body), file_name=filename)
                handler = ProgressTrackerHandler(tracker=tracker)
                opener = urllib.request.build_opener(handler)
                urllib.request.install_opener(opener)
            
            # Try upload with retries
            for attempt in range(self.max_retries):
                try:
                    # Create a fresh request for each attempt
                    req = urllib.request.Request(upload_url, data=body, headers=headers, method='POST')
                    
                    # Set timeouts
                    socket.setdefaulttimeout(self.read_timeout)
                    
                    with self._urlopen(req) as response:
                        result_text = response.read().decode('utf-8')
                        
                        # Try to parse as JSON, but handle plain text responses too
                        try:
                            result = json.loads(result_text)
                            logger.info("Upload successful: %s", result.get('name', 'Unknown'))
                        except json.JSONDecodeError:
                            logger.info("Upload successful, response: %s", result_text)
                        
                        return True
                        
                except urllib.error.HTTPError as e:
                    logger.error("HTTP error during upload (attempt %d/%d): %s", 
                                attempt + 1, self.max_retries, e)
                    
                    # Try to parse error response
                    try:
                        error_msg = json.loads(e.read().decode('utf-8'))
                        logger.error("Error details: %s", error_msg)
                    except:
                        pass
                    
                    # Only retry on certain HTTP errors (e.g. 500, 502, 503, 504)
                    if e.code >= 500 and attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    
                    return False
                    
                except (urllib.error.URLError, socket.timeout) as e:
                    # Network errors, timeout errors
                    logger.error("Network error during upload (attempt %d/%d): %s", 
                                attempt + 1, self.max_retries, e)
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    
                    return False
                    
                except Exception as e:
                    logger.error("Unexpected error during upload: %s", e)
                    return False
            
            return False
                
        except Exception as e:
            logger.error("Error preparing file for upload: %s", e)
            return False

    def get_tonies_custom_json(self) -> Optional[list]:
        """
        Get tonies.custom.json from the TeddyCloud server.
        
        Returns:
            List of custom tonie entries or None if request failed
        """
        try:
            url = f"{self.base_url}/api/toniesCustomJson"
            logger.info("Loading tonies.custom.json from %s", url)
            
            req = urllib.request.Request(url)
            
            with self._urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                if isinstance(data, list):
                    logger.info("Successfully loaded tonies.custom.json with %d entries", len(data))
                    return data
                else:
                    logger.error("Invalid tonies.custom.json format, expected list")
                    return None
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.info("tonies.custom.json not found on server, starting with empty list")
                return []
            else:
                logger.error("HTTP error loading tonies.custom.json: %s", e)
                return None
        except Exception as e:
            logger.error("Error loading tonies.custom.json: %s", e)
            return None
    
    def put_tonies_custom_json(self, custom_json_data: List[Dict[str, Any]]) -> bool:
        """
        Save tonies.custom.json to the TeddyCloud server.
        
        Args:
            custom_json_data: List of custom tonie entries to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/toniesCustomJson"
            logger.info("Saving tonies.custom.json to %s", url)
            
            data = json.dumps(custom_json_data, indent=2).encode('utf-8')
            headers = {'Content-Type': 'application/json'}
            
            req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
            
            with self._urlopen(req) as response:
                result = response.read().decode('utf-8')
                logger.info("Successfully saved tonies.custom.json to server")
                return True
                
        except Exception as e:
            logger.error("Error saving tonies.custom.json to server: %s", e)
            return False

def upload_to_teddycloud(file_path: str, teddycloud_url: str, ignore_ssl_verify: bool = False, 
                  special_folder: str = None, path: str = None, show_progress: bool = True,
                  connection_timeout: int = DEFAULT_CONNECTION_TIMEOUT, 
                  read_timeout: int = DEFAULT_READ_TIMEOUT,
                  max_retries: int = DEFAULT_MAX_RETRIES,
                  retry_delay: int = DEFAULT_RETRY_DELAY) -> bool:
    """
    Upload a .taf file to TeddyCloud.
    
    Args:
        file_path: Path to the .taf file to upload
        teddycloud_url: URL of the TeddyCloud instance
        ignore_ssl_verify: If True, SSL certificate verification will be disabled
        special_folder: Special folder to upload to (currently only 'library' is supported)
        path: Path where to write the file within the special folder
        show_progress: Whether to show a progress bar during upload
        connection_timeout: Timeout for establishing a connection in seconds
        read_timeout: Timeout for reading data from the server in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retry attempts in seconds
        
    Returns:
        True if upload was successful, False otherwise
    """
    logger.info("Uploading %s to TeddyCloud %s", file_path, teddycloud_url)
    
    if special_folder:
        logger.info("Using special folder: %s", special_folder)
    
    if path:
        logger.info("Using custom path: %s", path)

    if max_retries > 1:
        logger.info("Will retry up to %d times with %d second delay if upload fails", 
                   max_retries, retry_delay)
    
    client = TeddyCloudClient(
        teddycloud_url, ignore_ssl_verify,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        max_retries=max_retries,
        retry_delay=retry_delay
    )
    
    return client.upload_file(file_path, special_folder, path, show_progress)

def get_tags_from_teddycloud(teddycloud_url: str, ignore_ssl_verify: bool = False) -> bool:
    """
    Get and display tags from a TeddyCloud instance.
    
    Args:
        teddycloud_url: URL of the TeddyCloud instance
        ignore_ssl_verify: If True, SSL certificate verification will be disabled
        
    Returns:
        True if tags were retrieved successfully, False otherwise
    """
    logger.info("Getting tags from TeddyCloud %s", teddycloud_url)
    
    client = TeddyCloudClient(teddycloud_url, ignore_ssl_verify)
    response = client.get_tag_index()
    
    if not response:
        logger.error("Failed to retrieve tags from TeddyCloud")
        return False
    
    # Handle the specific JSON structure returned by TeddyCloud API
    if isinstance(response, dict) and 'tags' in response:
        tags = response['tags']
        logger.info("Successfully retrieved %d tags from TeddyCloud", len(tags))
        
        print("\nAvailable Tags from TeddyCloud:")
        print("-" * 60)
        
        # Sort tags by type and then by uid for better organization
        sorted_tags = sorted(tags, key=lambda x: (x.get('type', ''), x.get('uid', '')))
        
        for tag in sorted_tags:
            uid = tag.get('uid', 'Unknown UID')
            tag_type = tag.get('type', 'Unknown')
            valid = "✓" if tag.get('valid', False) else "✗"
            series = tag.get('tonieInfo', {}).get('series', '')
            episode = tag.get('tonieInfo', {}).get('episode', '')
            source = tag.get('source', '')
            
            # Format header with key information
            print(f"UID: {uid} ({tag_type}) - Valid: {valid}")
            
            # Show more detailed information
            if series:
                print(f"Series: {series}")
            if episode:
                print(f"Episode: {episode}")
            if source:
                print(f"Source: {source}")
                
            # Show track information if available
            tracks = tag.get('tonieInfo', {}).get('tracks', [])
            if tracks:
                print("Tracks:")
                for i, track in enumerate(tracks, 1):
                    print(f"  {i}. {track}")
                    
            # Show track duration information
            track_seconds = tag.get('trackSeconds', [])
            if track_seconds and len(track_seconds) > 1:
                total_seconds = track_seconds[-1]
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                print(f"Duration: {minutes}:{seconds:02d} ({len(track_seconds)-1} tracks)")
            
            print("-" * 60)
    else:
        # Fallback for unexpected formats
        logger.info("Successfully retrieved tag data from TeddyCloud")
        print("\nTag data from TeddyCloud:")
        print("-" * 60)
        
        # Pretty print JSON data
        import json
        print(json.dumps(response, indent=2))
        
        print("-" * 60)
    
    return True

def get_tonies_custom_json_from_server(teddycloud_url: str, ignore_ssl_verify: bool = False) -> Optional[list]:
    """
    Get tonies.custom.json from the TeddyCloud server.
    
    Args:
        teddycloud_url: URL of the TeddyCloud instance
        ignore_ssl_verify: If True, SSL certificate verification will be disabled
        
    Returns:
        List of custom tonie entries or None if request failed
    """
    if not teddycloud_url:
        logger.error("Cannot load from server: No TeddyCloud URL provided")
        return None
        
    client = TeddyCloudClient(teddycloud_url, ignore_ssl_verify)
    return client.get_tonies_custom_json()

def put_tonies_custom_json_to_server(teddycloud_url: str, custom_json_data: List[Dict[str, Any]], 
                                  ignore_ssl_verify: bool = False) -> bool:
    """
    Save tonies.custom.json to the TeddyCloud server.
    
    Args:
        teddycloud_url: URL of the TeddyCloud instance
        custom_json_data: List of custom tonie entries to save
        ignore_ssl_verify: If True, SSL certificate verification will be disabled
        
    Returns:
        True if successful, False otherwise
    """
    if not teddycloud_url:
        logger.error("Cannot save to server: No TeddyCloud URL provided")
        return False
        
    client = TeddyCloudClient(teddycloud_url, ignore_ssl_verify)
    return client.put_tonies_custom_json(custom_json_data)