#!/usr/bin/python3
"""
TeddyCloud API client for TonieToolbox.
Handles uploading .taf files to a TeddyCloud instance and interacting with the TeddyCloud API.
"""

import os
import base64
import ssl
import socket
import requests
import json
from .logger import get_logger
logger = get_logger(__name__)
DEFAULT_CONNECTION_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 15  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # seconds

class TeddyCloudClient:
    """Client for interacting with TeddyCloud API."""
    
    def __init__(
        self,
        base_url: str,
        ignore_ssl_verify: bool = False,
        connection_timeout: int = DEFAULT_CONNECTION_TIMEOUT,
        read_timeout: int = DEFAULT_READ_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: int = DEFAULT_RETRY_DELAY,
        username: str = None,
        password: str = None,
        cert_file: str = None,
        key_file: str = None
    ) -> None:
        """
        Initialize the TeddyCloud client.
        
        Args:
            base_url (str): Base URL of the TeddyCloud instance (e.g., https://teddycloud.example.com)
            ignore_ssl_verify (bool): If True, SSL certificate verification will be disabled (useful for self-signed certificates)
            connection_timeout (int): Timeout for establishing a connection
            read_timeout (int): Timeout for reading data from the server
            max_retries (int): Maximum number of retries for failed requests
            retry_delay (int): Delay between retries
            username (str | None): Username for basic authentication (optional)
            password (str | None): Password for basic authentication (optional)
            cert_file (str | None): Path to client certificate file for certificate-based authentication (optional)
            key_file (str | None): Path to client private key file for certificate-based authentication (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.ignore_ssl_verify = ignore_ssl_verify
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.username = username
        self.password = password
        self.cert_file = cert_file
        self.key_file = key_file
        self.ssl_context = ssl.create_default_context()
        if ignore_ssl_verify:
            logger.warning("SSL certificate verification is disabled. This is insecure!")
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE        
        if cert_file:
            if not os.path.isfile(cert_file):
                raise ValueError(f"Client certificate file not found: {cert_file}")                
            cert_key_file = key_file if key_file else cert_file
            if not os.path.isfile(cert_key_file):
                raise ValueError(f"Client key file not found: {cert_key_file}")                
            try:
                logger.info("Using client certificate authentication")
                try:
                    with open(cert_file, 'r') as f:
                        cert_content = f.read(50)
                        logger.debug(f"Certificate file starts with: {cert_content[:20]}...")                    
                    with open(cert_key_file, 'r') as f:
                        key_content = f.read(50)
                        logger.debug(f"Key file starts with: {key_content[:20]}...")
                except Exception as e:
                    logger.warning(f"Error reading certificate files: {e}")
                self.cert = (cert_file, cert_key_file)
                logger.info(f"Client cert setup: {cert_file}, {cert_key_file}")
                self.ssl_context.load_cert_chain(cert_file, cert_key_file)
                logger.debug("Successfully loaded certificate into SSL context")
                
            except ssl.SSLError as e:
                raise ValueError(f"Failed to load client certificate: {e}")
                
    def _create_request_kwargs(self) -> dict:
        """
        Create common request keyword arguments for all API calls.
        
        Returns:
            dict: Dictionary with common request kwargs
        """
        kwargs = {
            'timeout': (self.connection_timeout, self.read_timeout),
            'verify': not self.ignore_ssl_verify
        }
        if self.username and self.password:
            kwargs['auth'] = (self.username, self.password)
        if self.cert_file:
            kwargs['cert'] = self.cert       
        return kwargs
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> 'requests.Response':
        """
        Make an HTTP request to the TeddyCloud API with retry logic.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint (without base URL)
            **kwargs: Additional arguments to pass to requests
        Returns:
            requests.Response: Response object
        Raises:
            requests.exceptions.RequestException: If request fails after all retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_kwargs = self._create_request_kwargs()
        request_kwargs.update(kwargs)
        retry_count = 0
        last_exception = None    
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.connection_timeout * 2)
        
        try:
            while retry_count < self.max_retries:
                try:
                    logger.debug(f"Making {method} request to {url}")
                    logger.debug(f"Using connection timeout: {self.connection_timeout}s, read timeout: {self.read_timeout}s")
                    session = requests.Session()                    
                    try:
                        response = session.request(method, url, **request_kwargs)
                        logger.debug(f"Received response with status code {response.status_code}")
                        response.raise_for_status()
                        return response
                    finally:
                        session.close()
                        
                except requests.exceptions.Timeout as e:
                    retry_count += 1
                    last_exception = e
                    logger.warning(f"Request timed out (attempt {retry_count}/{self.max_retries}): {e}")
                    
                    if retry_count < self.max_retries:
                        import time
                        logger.info(f"Waiting {self.retry_delay} seconds before retrying...")
                        time.sleep(self.retry_delay)
                        
                except requests.exceptions.ConnectionError as e:
                    retry_count += 1
                    last_exception = e
                    logger.warning(f"Connection error (attempt {retry_count}/{self.max_retries}): {e}")
                    
                    if retry_count < self.max_retries:
                        import time
                        logger.info(f"Waiting {self.retry_delay} seconds before retrying...")
                        time.sleep(self.retry_delay)
                        
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    last_exception = e
                    logger.warning(f"Request failed (attempt {retry_count}/{self.max_retries}): {e}")
                    
                    if retry_count < self.max_retries:
                        import time
                        logger.info(f"Waiting {self.retry_delay} seconds before retrying...")
                        time.sleep(self.retry_delay)        
            logger.error(f"Request failed after {self.max_retries} attempts: {last_exception}")
            raise last_exception
        finally:
            socket.setdefaulttimeout(old_timeout)

    # ------------- GET API Methods -------------
    
    def get_tonies_custom_json(self) -> dict:
        """
        Get custom Tonies JSON data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing custom Tonies data
        """
        response = self._make_request('GET', '/api/toniesCustomJson')
        return response.json()
    
    def get_tonies_json(self) -> dict:
        """
        Get Tonies JSON data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing Tonies data
        """
        response = self._make_request('GET', '/api/toniesJson')
        return response.json()
    
    def get_tag_index(self) -> dict:
        """
        Get tag index data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing tag index data
        """
        response = self._make_request('GET', '/api/getTagIndex')
        return response.json()    
    
    def get_file_index(self) -> dict:
        """
        Get file index data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing file index data
        """
        response = self._make_request('GET', '/api/fileIndex')
        return response.json()
    
    def get_file_index_v2(self) -> dict:
        """
        Get version 2 file index data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing version 2 file index data
        """
        response = self._make_request('GET', '/api/fileIndexV2')
        return response.json()
    
    def get_tonieboxes_json(self) -> dict:
        """
        Get Tonieboxes JSON data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing Tonieboxes data
        """
        response = self._make_request('GET', '/api/tonieboxesJson')
        return response.json()
    
    # ------------- POST API Methods -------------
    
    def create_directory(self, path: str, overlay: str = None, special: str = None) -> str:
        """
        Create a directory on the TeddyCloud server.
        
        Args:
            path (str): Directory path to create
            overlay (str | None): Settings overlay ID (optional)
            special (str | None): Special folder source, only 'library' supported yet (optional)
        Returns:
            str: Response message from server (usually "OK")
        """
        params = {}
        if overlay:
            params['overlay'] = overlay
        if special:
            params['special'] = special
            
        response = self._make_request('POST', '/api/dirCreate', params=params, data=path)
        return response.text
    
    def delete_directory(self, path: str, overlay: str = None, special: str = None) -> str:
        """
        Delete a directory from the TeddyCloud server.
        
        Args:
            path (str): Directory path to delete
            overlay (str | None): Settings overlay ID (optional)
            special (str | None): Special folder source, only 'library' supported yet (optional)
        Returns:
            str: Response message from server (usually "OK")
        """
        params = {}
        if overlay:
            params['overlay'] = overlay
        if special:
            params['special'] = special
            
        response = self._make_request('POST', '/api/dirDelete', params=params, data=path)
        return response.text
    
    def delete_file(self, path: str, overlay: str = None, special: str = None) -> str:
        """
        Delete a file from the TeddyCloud server.
        
        Args:
            path (str): File path to delete
            overlay (str | None): Settings overlay ID (optional)
            special (str | None): Special folder source, only 'library' supported yet (optional)
        Returns:
            str: Response message from server (usually "OK")
        """
        params = {}
        if overlay:
            params['overlay'] = overlay
        if special:
            params['special'] = special
            
        response = self._make_request('POST', '/api/fileDelete', params=params, data=path)
        return response.text
    
    def upload_file(self, file_path: str, destination_path: str = None, overlay: str = None, special: str = None) -> dict:
        """
        Upload a file to the TeddyCloud server.
        
        Args:
            file_path (str): Local path to the file to upload
            destination_path (str | None): Server path where to write the file to (optional)
            overlay (str | None): Settings overlay ID (optional)
            special (str | None): Special folder source, only 'library' supported yet (optional)
        Returns:
            dict: JSON response from server
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File to upload not found: {file_path}")
        
        params = {}
        if destination_path:
            params['path'] = destination_path
        if overlay:
            params['overlay'] = overlay
        if special:
            params['special'] = special
            
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
            response = self._make_request('POST', '/api/fileUpload', params=params, files=files)
            
        try:
            return response.json()
        except ValueError:
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'message': response.text
            }
    
    # ------------- Custom API Methods -------------

    def _get_paths_cache_file(self) -> str:
        """
        Get the path to the paths cache file.
        
        Returns:
            str: Path to the paths cache file
        """
        cache_dir = os.path.join(os.path.expanduser("~"), ".tonietoolbox")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, "paths.json")
    
    def _load_paths_cache(self) -> set:
        """
        Load the paths cache from the cache file.
        
        Returns:
            set: Set of existing directory paths
        """
        cache_file = self._get_paths_cache_file()
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    paths_data = json.load(f)
                    # Convert to set for faster lookups
                    return set(paths_data.get('paths', []))
            return set()
        except Exception as e:
            logger.warning(f"Failed to load paths cache: {e}")
            return set()
    
    def _save_paths_cache(self, paths: set) -> None:
        """
        Save the paths cache to the cache file.
        
        Args:
            paths (set): Set of directory paths to save
        """
        cache_file = self._get_paths_cache_file()
        try:
            paths_data = {'paths': list(paths)}
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(paths_data, f, indent=2)
            logger.debug(f"Saved {len(paths)} paths to cache file")
        except Exception as e:
            logger.warning(f"Failed to save paths cache: {e}")
    
    def create_directories_recursive(self, path: str, overlay: str = None, special: str = "library") -> str:
        """
        Create directories recursively on the TeddyCloud server.

        This function handles both cases:
        - Directories that already exist (prevents 500 errors)
        - Parent directories that don't exist yet (creates them first)
        
        This optimized version uses a local paths cache instead of querying the file index,
        since the file index might not represent the correct folders.

        Args:
            path (str): Directory path to create (can contain multiple levels)
            overlay (str | None): Settings overlay ID (optional)
            special (str | None): Special folder source, only 'library' supported yet (optional)

        Returns:
            str: Response message from server
        """
        path = path.replace('\\', '/').strip('/')
        if not path:
            return "Path is empty"
        existing_dirs = self._load_paths_cache()
        logger.debug(f"Loaded {len(existing_dirs)} existing paths from cache")
        path_components = path.split('/')
        current_path = ""
        result = "OK"
        paths_updated = False
        for component in path_components:
            if current_path:
                current_path += f"/{component}"
            else:
                current_path = component
            if current_path in existing_dirs:
                logger.debug(f"Directory '{current_path}' exists in paths cache, skipping creation")
                continue

            try:
                result = self.create_directory(current_path, overlay, special)
                logger.debug(f"Created directory: {current_path}")
                # Add the newly created directory to our cache
                existing_dirs.add(current_path)
                paths_updated = True
            except requests.exceptions.HTTPError as e:
                # If it's a 500 error, likely the directory already exists
                if e.response.status_code == 500:
                    if "already exists" in e.response.text.lower():
                        logger.debug(f"Directory '{current_path}' already exists, continuing")
                        # Add to our cache for future operations
                        existing_dirs.add(current_path)
                        paths_updated = True
                    else:
                        # Log the actual error message but continue anyway
                        # This allows us to continue even if the error is something else
                        logger.warning(f"Warning while creating '{current_path}': {str(e)}")
                else:
                    # Re-raise for other HTTP errors
                    logger.error(f"Failed to create directory '{current_path}': {str(e)}")
                    raise
        
        # Save updated paths cache if any changes were made
        if paths_updated:
            self._save_paths_cache(existing_dirs)
                
        return result