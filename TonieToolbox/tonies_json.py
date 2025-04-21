"""
TonieToolbox module for handling the tonies.custom.json operations.

This module handles fetching, updating, and saving custom tonies JSON data,
which can be used to manage custom Tonies on TeddyCloud servers.
"""

import os
import json
import time
import urllib.error
import ssl
import uuid
import locale
import re
from typing import Dict, Any, List, Optional, Tuple

from .logger import get_logger
from .media_tags import get_file_tags, extract_album_info
from .constants import LANGUAGE_MAPPING, GENRE_MAPPING
from .teddycloud import get_tonies_custom_json_from_server, put_tonies_custom_json_to_server

logger = get_logger('tonies_json')

class ToniesJsonHandler:
    """Handler for tonies.custom.json operations."""
    
    def __init__(self, teddycloud_url: Optional[str] = None, ignore_ssl_verify: bool = False):
        """
        Initialize the handler.
        
        Args:
            teddycloud_url: URL of the TeddyCloud instance (optional)
            ignore_ssl_verify: If True, SSL certificate verification will be disabled
        """
        self.teddycloud_url = teddycloud_url.rstrip('/') if teddycloud_url else None
        self.ignore_ssl_verify = ignore_ssl_verify
        self.custom_json = []
        self.is_loaded = False
    
    def load_from_server(self) -> bool:
        """
        Load tonies.custom.json from the TeddyCloud server.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.teddycloud_url:
            logger.error("Cannot load from server: No TeddyCloud URL provided")
            return False
            
        try:
            result = get_tonies_custom_json_from_server(self.teddycloud_url, self.ignore_ssl_verify)
            
            if result is not None:
                self.custom_json = result
                self.is_loaded = True
                logger.info("Successfully loaded tonies.custom.json with %d entries", len(self.custom_json))
                return True
            else:
                logger.error("Failed to load tonies.custom.json from server")
                return False
                
        except Exception as e:
            logger.error("Error loading tonies.custom.json: %s", e)
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load tonies.custom.json from a local file.
        
        Args:
            file_path: Path to the tonies.custom.json file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                logger.info("Loading tonies.custom.json from file: %s", file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.custom_json = data
                        self.is_loaded = True
                        logger.info("Successfully loaded tonies.custom.json with %d entries", len(self.custom_json))
                        return True
                    else:
                        logger.error("Invalid tonies.custom.json format in file, expected list")
                        return False
            else:
                logger.info("tonies.custom.json file not found, starting with empty list")
                self.custom_json = []
                self.is_loaded = True
                return True
                
        except Exception as e:
            logger.error("Error loading tonies.custom.json from file: %s", e)
            return False
    
    def save_to_server(self) -> bool:
        """
        Save tonies.custom.json to the TeddyCloud server.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.teddycloud_url:
            logger.error("Cannot save to server: No TeddyCloud URL provided")
            return False
            
        if not self.is_loaded:
            logger.error("Cannot save tonies.custom.json: data not loaded")
            return False
            
        try:
            result = put_tonies_custom_json_to_server(
                self.teddycloud_url, 
                self.custom_json, 
                self.ignore_ssl_verify
            )
            
            if result:
                logger.info("Successfully saved tonies.custom.json to server")
                return True
            else:
                logger.error("Failed to save tonies.custom.json to server")
                return False
                
        except Exception as e:
            logger.error("Error saving tonies.custom.json to server: %s", e)
            return False
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Save tonies.custom.json to a local file.
        
        Args:
            file_path: Path where to save the tonies.custom.json file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_loaded:
            logger.error("Cannot save tonies.custom.json: data not loaded")
            return False
            
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            logger.info("Saving tonies.custom.json to file: %s", file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_json, f, indent=2, ensure_ascii=False)
                
            logger.info("Successfully saved tonies.custom.json to file")
            return True
                
        except Exception as e:
            logger.error("Error saving tonies.custom.json to file: %s", e)
            return False
    
    def add_entry_from_taf(self, taf_file: str, input_files: List[str], artwork_url: Optional[str] = None) -> bool:
        """
        Add an entry to the custom JSON from a TAF file.
        
        Args:
            taf_file: Path to the TAF file
            input_files: List of input audio files used to create the TAF
            artwork_url: URL of the uploaded artwork (if any)
            
        Returns:
            True if successful, False otherwise
        """
        logger.trace("Entering add_entry_from_taf() with taf_file=%s, input_files=%s, artwork_url=%s", 
                    taf_file, input_files, artwork_url)
        
        if not self.is_loaded:
            logger.error("Cannot add entry: tonies.custom.json not loaded")
            return False
        
        try:
            logger.info("Adding entry for %s to tonies.custom.json", taf_file)
            
            logger.debug("Generating article ID")
            article_id = self._generate_article_id()
            logger.debug("Generated article ID: %s", article_id)
            
            logger.debug("Extracting metadata from input files")
            metadata = self._extract_metadata_from_files(input_files)
            logger.debug("Extracted metadata: %s", metadata)
            
            logger.debug("Creating JSON entry")
            entry = self._create_json_entry(article_id, taf_file, metadata, input_files, artwork_url)
            logger.debug("Created entry: %s", entry)
            
            self.custom_json.append(entry)
            logger.debug("Added entry to custom_json (new length: %d)", len(self.custom_json))
            
            logger.info("Successfully added entry for %s", taf_file)
            logger.trace("Exiting add_entry_from_taf() with success=True")
            return True
            
        except Exception as e:
            logger.error("Error adding entry for %s: %s", taf_file, e)
            logger.trace("Exiting add_entry_from_taf() with success=False due to exception: %s", str(e))
            return False
    
    def _generate_article_id(self) -> str:
        """
        Generate a unique article ID for a new entry.
        
        Returns:
            Unique article ID in the format "tt-42" followed by sequential number starting from 0
        """
        logger.trace("Entering _generate_article_id()")
        
        # Find the highest sequential number for tt-42 IDs
        highest_num = -1
        pattern = re.compile(r'tt-42(\d+)')
        
        logger.debug("Searching for highest tt-42 ID in %d existing entries", len(self.custom_json))
        for entry in self.custom_json:
            article = entry.get('article', '')
            logger.trace("Checking article ID: %s", article)
            match = pattern.match(article)
            if match:
                try:
                    num = int(match.group(1))
                    logger.trace("Found numeric part: %d", num)
                    highest_num = max(highest_num, num)
                except (IndexError, ValueError) as e:
                    logger.trace("Failed to parse article ID: %s (%s)", article, str(e))
                    pass
        
        logger.debug("Highest tt-42 ID number found: %d", highest_num)
        
        # Generate the next sequential number
        next_num = highest_num + 1
        
        # Format the ID with leading zeros to make it 10 digits
        result = f"tt-42{next_num:010d}"
        logger.debug("Generated new article ID: %s", result)
        
        logger.trace("Exiting _generate_article_id() with result=%s", result)
        return result
    
    def _extract_metadata_from_files(self, input_files: List[str]) -> Dict[str, Any]:
        metadata = {}
        
        # If there are multiple files in the same folder, use album info
        if len(input_files) > 1 and os.path.dirname(input_files[0]) == os.path.dirname(input_files[-1]):
            folder_path = os.path.dirname(input_files[0])
            album_info = extract_album_info(folder_path)
            metadata.update(album_info)
        
        # For all files, collect tags to use for track descriptions
        track_descriptions = []
        for file_path in input_files:
            tags = get_file_tags(file_path)
            if 'title' in tags:
                track_descriptions.append(tags['title'])
            else:
                # Use filename as fallback
                filename = os.path.splitext(os.path.basename(file_path))[0]
                track_descriptions.append(filename)

            # Extract language and genre from the first file if not already present
            if 'language' not in metadata and 'language' in tags:
                metadata['language'] = tags['language']
            
            if 'genre' not in metadata and 'genre' in tags:
                metadata['genre'] = tags['genre']
        
        metadata['track_descriptions'] = track_descriptions
        
        return metadata
    
    def _determine_language(self, metadata: Dict[str, Any]) -> str:
        # Check for language tag in metadata
        if 'language' in metadata:
            lang_value = metadata['language'].lower().strip()
            if lang_value in LANGUAGE_MAPPING:
                return LANGUAGE_MAPPING[lang_value]
        
        # If not found, try to use system locale
        try:
            system_lang, _ = locale.getdefaultlocale()
            if system_lang:
                lang_code = system_lang.split('_')[0].lower()
                if lang_code in LANGUAGE_MAPPING:
                    return LANGUAGE_MAPPING[lang_code]
                # Try to map system language code to tonie format
                if lang_code == 'de':
                    return 'de-de'
                elif lang_code == 'en':
                    return 'en-us'
                elif lang_code == 'fr':
                    return 'fr-fr'
                elif lang_code == 'it':
                    return 'it-it'
                elif lang_code == 'es':
                    return 'es-es'
        except Exception:
            pass
        
        # Default to German as it's most common for Tonies
        return 'de-de'
    
    def _determine_category(self, metadata: Dict[str, Any]) -> str:
        # Check for genre tag in metadata
        if 'genre' in metadata:
            genre_value = metadata['genre'].lower().strip()
            
            # Check for direct mapping
            if genre_value in GENRE_MAPPING:
                return GENRE_MAPPING[genre_value]
            
            # Check for partial matching
            for genre_key, category in GENRE_MAPPING.items():
                if genre_key in genre_value:
                    return category
            
            # Check for common keywords in the genre
            if any(keyword in genre_value for keyword in ['musik', 'song', 'music', 'lied']):
                return 'music'
            elif any(keyword in genre_value for keyword in ['hörspiel', 'hörspiele', 'audio play']):
                return 'Hörspiele & Hörbücher'
            elif any(keyword in genre_value for keyword in ['hörbuch', 'audiobook', 'book']):
                return 'Hörspiele & Hörbücher'
            elif any(keyword in genre_value for keyword in ['märchen', 'fairy', 'tales']):
                return 'Hörspiele & Hörbücher'
            elif any(keyword in genre_value for keyword in ['wissen', 'knowledge', 'learn']):
                return 'Wissen & Hörmagazine'
            elif any(keyword in genre_value for keyword in ['schlaf', 'sleep', 'meditation']):
                return 'Schlaflieder & Entspannung'
        
        # Default to standard category for most custom content
        return 'Hörspiele & Hörbücher'
    
    def _estimate_age(self, metadata: Dict[str, Any]) -> int:
        default_age = 3
        if 'comment' in metadata:
            comment = metadata['comment'].lower()
            age_indicators = ['ab ', 'age ', 'alter ', 'Jahre']
            for indicator in age_indicators:
                if indicator in comment:
                    try:
                        idx = comment.index(indicator) + len(indicator)
                        age_str = ''.join(c for c in comment[idx:idx+2] if c.isdigit())
                        if age_str:
                            return int(age_str)
                    except (ValueError, IndexError):
                        pass        
        if 'genre' in metadata:
            genre = metadata['genre'].lower()
            if any(term in genre for term in ['kind', 'child', 'kids']):
                return 3
            if any(term in genre for term in ['jugend', 'teen', 'youth']):
                return 10
            if any(term in genre for term in ['erwachsen', 'adult']):
                return 18
        
        return default_age
    
    def _create_json_entry(self, article_id: str, taf_file: str, metadata: Dict[str, Any], 
                          input_files: List[str], artwork_url: Optional[str] = None) -> Dict[str, Any]:
        # Calculate the size in bytes
        taf_size = os.path.getsize(taf_file)
        
        # Get current timestamp
        timestamp = int(time.time())
        
        # Create entry from metadata
        series = metadata.get('albumartist', metadata.get('artist', 'Unknown Artist'))
        episode = metadata.get('album', os.path.splitext(os.path.basename(taf_file))[0])
        track_desc = metadata.get('track_descriptions', [])
        language = self._determine_language(metadata)
        category = self._determine_category(metadata)
        age = self._estimate_age(metadata)
        
        # Create a unique hash for the file
        import hashlib
        with open(taf_file, 'rb') as f:
            taf_hash = hashlib.sha1(f.read()).hexdigest()
        
        # Build the entry
        entry = {
            "article": article_id,
            "data": [
                {
                    "series": series,
                    "episode": episode,
                    "release": timestamp,
                    "language": language,
                    "category": category,
                    "runtime": 0,  # Could calculate this with proper audio analysis
                    "age": age,
                    "origin": "custom",
                    "image": artwork_url if artwork_url else "",
                    "track-desc": track_desc,
                    "ids": [
                        {
                            "audio-id": timestamp,
                            "hash": taf_hash,
                            "size": taf_size,
                            "tracks": len(track_desc),
                            "confidence": 1
                        }
                    ]
                }
            ]
        }
        
        return entry


def fetch_and_update_tonies_json(teddycloud_url: Optional[str] = None, ignore_ssl_verify: bool = False,
                               taf_file: Optional[str] = None, input_files: Optional[List[str]] = None, 
                               artwork_url: Optional[str] = None, output_dir: Optional[str] = None) -> bool:
    """
    Fetch tonies.custom.json from server and merge with local file if it exists, then update with new entry.
    
    Args:
        teddycloud_url: URL of the TeddyCloud instance (optional)
        ignore_ssl_verify: If True, SSL certificate verification will be disabled
        taf_file: Path to the TAF file to add
        input_files: List of input audio files used to create the TAF
        artwork_url: URL of the uploaded artwork (if any)
        output_dir: Directory where to save the tonies.custom.json file (defaults to './output')
        
    Returns:
        True if successful, False otherwise
    """
    handler = ToniesJsonHandler(teddycloud_url, ignore_ssl_verify)
    
    # Determine where to load from and save to
    if not output_dir:
        output_dir = './output'
        
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the full path for the JSON file
    json_file_path = os.path.join(output_dir, 'tonies.custom.json')
    
    loaded_from_server = False
    
    # Step 1: Try to get live version from the server first
    if teddycloud_url:
        logger.info("Attempting to load tonies.custom.json from server")
        loaded_from_server = handler.load_from_server()
    
    # Step 2: If we have a local file, merge with the server content
    if os.path.exists(json_file_path):
        logger.info("Local tonies.custom.json file found, merging with server content")
        
        # Create a temporary handler to load local content
        local_handler = ToniesJsonHandler()
        if local_handler.load_from_file(json_file_path):
            if loaded_from_server:
                # Merge local content with server content
                # Use server-loaded content as base, then add any local entries not in server version
                server_article_ids = {entry.get('article') for entry in handler.custom_json}
                for local_entry in local_handler.custom_json:
                    local_article_id = local_entry.get('article')
                    if local_article_id not in server_article_ids:
                        logger.info(f"Adding local-only entry {local_article_id} to merged content")
                        handler.custom_json.append(local_entry)
            else:
                # Use local content as we couldn't load from server
                handler.custom_json = local_handler.custom_json
                handler.is_loaded = True
                logger.info("Using local tonies.custom.json content")
    elif not loaded_from_server:
        # No server content and no local file, start with empty list
        handler.custom_json = []
        handler.is_loaded = True
        logger.info("No tonies.custom.json found, starting with empty list")
    
    # Add entry if needed
    if taf_file and input_files and handler.is_loaded:
        if not handler.add_entry_from_taf(taf_file, input_files, artwork_url):
            logger.error("Failed to add entry to tonies.custom.json")
            return False
    
    # Save to file
    if not handler.save_to_file(json_file_path):
        logger.error("Failed to save tonies.custom.json to file")
        return False
    
    # Try to save to server if URL is provided
    # For future use if the API enpoints are available
    #if teddycloud_url and handler.is_loaded:
        try:
            if not handler.save_to_server():
                logger.warning("Could not save tonies.custom.json to server")
        except Exception as e:
            logger.warning("Error when saving tonies.custom.json to server: %s", e)
            # Don't fail the operation if server upload fails
    
    return True