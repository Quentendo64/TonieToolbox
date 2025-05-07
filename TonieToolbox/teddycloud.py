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
from .logger import get_logger
logger = get_logger('teddycloud')
DEFAULT_CONNECTION_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 15  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # seconds

class TeddyCloudClient:
    """Client for interacting with TeddyCloud API."""
    
    def __init__(self, base_url: str, ignore_ssl_verify: bool = False, 
                 connection_timeout: int = DEFAULT_CONNECTION_TIMEOUT, 
                 read_timeout: int = DEFAULT_READ_TIMEOUT, 
                 max_retries: int = DEFAULT_MAX_RETRIES, 
                 retry_delay: int = DEFAULT_RETRY_DELAY,
                 username: str = None, password: str = None,
                 cert_file: str = None, key_file: str = None):
        """
        Initialize the TeddyCloud client.
        
        Args:
            base_url: Base URL of the TeddyCloud instance (e.g., https://teddycloud.example.com)
            ignore_ssl_verify: If True, SSL certificate verification will be disabled (useful for self-signed certificates)
            connection_timeout: Timeout for establishing a connection
            read_timeout: Timeout for reading data from the server
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries
            username: Username for basic authentication (optional)
            password: Password for basic authentication (optional)
            cert_file: Path to client certificate file for certificate-based authentication (optional)
            key_file: Path to client private key file for certificate-based authentication (optional)
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
                
    def _create_request_kwargs(self):
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
    
    def _make_request(self, method, endpoint, **kwargs):
        """
        Make an HTTP request to the TeddyCloud API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
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
    
    def get_tonies_custom_json(self):
        """
        Get custom Tonies JSON data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing custom Tonies data
        """
        response = self._make_request('GET', '/api/toniesCustomJson')
        return response.json()
    
    def get_tonies_json(self):
        """
        Get Tonies JSON data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing Tonies data
        """
        response = self._make_request('GET', '/api/toniesJson')
        return response.json()
    
    def get_tag_index(self):
        """
        Get tag index data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing tag index data
        """
        response = self._make_request('GET', '/api/getTagIndex')
        return response.json()    
    
    def get_file_index(self):
        """
        Get file index data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing file index data
        """
        response = self._make_request('GET', '/api/fileIndex')
        return response.json()
    
    def get_file_index_v2(self):
        """
        Get version 2 file index data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing version 2 file index data
        """
        response = self._make_request('GET', '/api/fileIndexV2')
        return response.json()
    
    def get_tonieboxes_json(self):
        """
        Get Tonieboxes JSON data from the TeddyCloud server.
        
        Returns:
            dict: JSON response containing Tonieboxes data
        """
        response = self._make_request('GET', '/api/tonieboxesJson')
        return response.json()
    
    # ------------- POST API Methods -------------
    
    def create_directory(self, path, overlay=None, special=None):
        """
        Create a directory on the TeddyCloud server.
        
        Args:
            path: Directory path to create
            overlay: Settings overlay ID (optional)
            special: Special folder source, only 'library' supported yet (optional)
            
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
    
    def delete_directory(self, path, overlay=None, special=None):
        """
        Delete a directory from the TeddyCloud server.
        
        Args:
            path: Directory path to delete
            overlay: Settings overlay ID (optional)
            special: Special folder source, only 'library' supported yet (optional)
            
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
    
    def delete_file(self, path, overlay=None, special=None):
        """
        Delete a file from the TeddyCloud server.
        
        Args:
            path: File path to delete
            overlay: Settings overlay ID (optional)
            special: Special folder source, only 'library' supported yet (optional)
            
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
    
    def upload_file(self, file_path, destination_path=None, overlay=None, special=None):
        """
        Upload a file to the TeddyCloud server.
        
        Args:
            file_path: Local path to the file to upload
            destination_path: Server path where to write the file to (optional)
            overlay: Settings overlay ID (optional)
            special: Special folder source, only 'library' supported yet (optional)
            
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
