"""
TonieToolbox module for handling the tonies.custom.json operations.

This module handles fetching, updating, and saving custom tonies JSON data,
which can be used to manage custom Tonies on TeddyCloud servers.
"""

import os
import json
import time
import locale
import re
import hashlib
import mutagen
from typing import Dict, Any, List, Optional

from .logger import get_logger
from .media_tags import get_file_tags, extract_album_info
from .constants import LANGUAGE_MAPPING, GENRE_MAPPING
from .teddycloud import TeddyCloudClient

logger = get_logger('tonies_json')

class ToniesJsonHandler:
    """Handler for tonies.custom.json operations."""
    
    def __init__(self, client: TeddyCloudClient = None):
        """
        Initialize the handler.
        
        Args:
            client: TeddyCloudClient instance to use for API communication
        """    
        self.client = client
        self.custom_json = []
        self.is_loaded = False

    def load_from_server(self) -> bool:
        """
        Load tonies.custom.json from the TeddyCloud server.
        
        Returns:
            True if successful, False otherwise
        """          
        if self.client is None:
            logger.error("Cannot load from server: no client provided")
            return False
            
        try:
            result = self.client.get_tonies_custom_json()            
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
        If an entry with the same hash exists, it will be updated.
        If an entry with the same series+episode exists, the new hash will be added to it.
        
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
            
            logger.debug("Extracting metadata from input files")
            metadata = self._extract_metadata_from_files(input_files)
            logger.debug("Extracted metadata: %s", metadata)
            with open(taf_file, 'rb') as f:
                taf_hash = hashlib.sha1(f.read()).hexdigest()
            
            taf_size = os.path.getsize(taf_file)
            timestamp = int(time.time())
            series = metadata.get('albumartist', metadata.get('artist', 'Unknown Artist'))
            episode = metadata.get('album', os.path.splitext(os.path.basename(taf_file))[0])
            track_desc = metadata.get('track_descriptions', [])
            language = self._determine_language(metadata)
            category = self._determine_category(metadata)
            age = self._estimate_age(metadata)
            new_id_entry = {
                "audio-id": timestamp,
                "hash": taf_hash,
                "size": taf_size,
                "tracks": len(track_desc),
                "confidence": 1
            }
            existing_entry, entry_idx, data_idx = self.find_entry_by_hash(taf_hash)
            if existing_entry:
                logger.info("Found existing entry with the same hash, updating it")
                data = existing_entry['data'][data_idx]
                if artwork_url and artwork_url != data.get('image', ''):
                    logger.debug("Updating artwork URL")
                    data['image'] = artwork_url
                if track_desc and track_desc != data.get('track-desc', []):
                    logger.debug("Updating track descriptions")
                    data['track-desc'] = track_desc
                
                logger.info("Successfully updated existing entry for %s", taf_file)
                return True
            existing_entry, entry_idx, data_idx = self.find_entry_by_series_episode(series, episode)
            if existing_entry:
                logger.info("Found existing entry with the same series/episode, adding hash to it")
                existing_data = existing_entry['data'][data_idx]
                if 'ids' not in existing_data:
                    existing_data['ids'] = []
                
                existing_data['ids'].append(new_id_entry)
                if artwork_url and artwork_url != existing_data.get('image', ''):
                    logger.debug("Updating artwork URL")
                    existing_data['image'] = artwork_url
                
                logger.info("Successfully added new hash to existing entry for %s", taf_file)
                return True
            logger.debug("No existing entry found, creating new entry")
            logger.debug("Generating article ID")
            article_id = self._generate_article_id()
            logger.debug("Generated article ID: %s", article_id)
            
            entry = {
                "article": article_id,
                "data": [
                    {
                        "series": series,
                        "episode": episode,
                        "release": timestamp,
                        "language": language,
                        "category": category,
                        "runtime": self._calculate_runtime(input_files),
                        "age": age,
                        "origin": "custom",
                        "image": artwork_url if artwork_url else "",
                        "track-desc": track_desc,
                        "ids": [new_id_entry]
                    }
                ]
            }
            
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
        next_num = highest_num + 1
        result = f"tt-42{next_num:010d}"
        logger.debug("Generated new article ID: %s", result)
        
        logger.trace("Exiting _generate_article_id() with result=%s", result)
        return result
    
    def _extract_metadata_from_files(self, input_files: List[str]) -> Dict[str, Any]:
        """
        Extract metadata from audio files to use in the custom JSON entry.
        
        Args:
            input_files: List of paths to audio files
            
        Returns:
            Dictionary containing metadata extracted from files
        """
        metadata = {}
        track_descriptions = []
        for file_path in input_files:
            tags = get_file_tags(file_path)
            if 'title' in tags:
                track_descriptions.append(tags['title'])
            else:
                filename = os.path.splitext(os.path.basename(file_path))[0]
                track_descriptions.append(filename)

            if 'language' not in metadata and 'language' in tags:
                metadata['language'] = tags['language']
            
            if 'genre' not in metadata and 'genre' in tags:
                metadata['genre'] = tags['genre']
        
        metadata['track_descriptions'] = track_descriptions
        
        return metadata
    
    def _determine_language(self, metadata: Dict[str, Any]) -> str:
        if 'language' in metadata:
            lang_value = metadata['language'].lower().strip()
            if lang_value in LANGUAGE_MAPPING:
                return LANGUAGE_MAPPING[lang_value]
        try:
            system_lang, _ = locale.getdefaultlocale()
            if system_lang:
                lang_code = system_lang.split('_')[0].lower()
                if lang_code in LANGUAGE_MAPPING:
                    return LANGUAGE_MAPPING[lang_code]
        except Exception:
            pass
        return 'de-de'
    
    def _determine_category(self, metadata: Dict[str, Any]) -> str:
        if 'genre' in metadata:
            genre_value = metadata['genre'].lower().strip()
            
            if genre_value in GENRE_MAPPING:
                return GENRE_MAPPING[genre_value]
            
            for genre_key, category in GENRE_MAPPING.items():
                if genre_key in genre_value:
                    return category

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
    
    def find_entry_by_hash(self, taf_hash: str) -> tuple[Optional[Dict[str, Any]], Optional[int], Optional[int]]:
        """
        Find an entry in the custom JSON by TAF hash.
        
        Args:
            taf_hash: SHA1 hash of the TAF file to find
            
        Returns:
            Tuple of (entry, entry_index, data_index) if found, or (None, None, None) if not found
        """
        logger.trace("Searching for entry with hash %s", taf_hash)
        
        for entry_idx, entry in enumerate(self.custom_json):
            if 'data' not in entry:
                continue
                
            for data_idx, data in enumerate(entry['data']):
                if 'ids' not in data:
                    continue
                    
                for id_entry in data['ids']:
                    if id_entry.get('hash') == taf_hash:
                        logger.debug("Found existing entry with matching hash %s", taf_hash)
                        return entry, entry_idx, data_idx
        
        logger.debug("No entry found with hash %s", taf_hash)
        return None, None, None
    
    def find_entry_by_series_episode(self, series: str, episode: str) -> tuple[Optional[Dict[str, Any]], Optional[int], Optional[int]]:
        """
        Find an entry in the custom JSON by series and episode.
        
        Args:
            series: Series name to find
            episode: Episode name to find
            
        Returns:
            Tuple of (entry, entry_index, data_index) if found, or (None, None, None) if not found
        """
        logger.trace("Searching for entry with series='%s', episode='%s'", series, episode)
        
        for entry_idx, entry in enumerate(self.custom_json):
            if 'data' not in entry:
                continue
                
            for data_idx, data in enumerate(entry['data']):
                if data.get('series') == series and data.get('episode') == episode:
                    logger.debug("Found existing entry with matching series/episode: %s / %s", series, episode)
                    return entry, entry_idx, data_idx
        
        logger.debug("No entry found with series/episode: %s / %s", series, episode)
        return None, None, None

    def _calculate_runtime(self, input_files: List[str]) -> int:
        """
        Calculate the total runtime in minutes from a list of audio files.

        Args:
            input_files: List of paths to audio files

        Returns:
            Total runtime in minutes (rounded to the nearest minute)
        """
        logger.trace("Entering _calculate_runtime() with %d input files", len(input_files))
        total_runtime_seconds = 0
        processed_files = 0
        
        try:
            logger.debug("Starting runtime calculation for %d audio files", len(input_files))
            
            for i, file_path in enumerate(input_files):
                logger.trace("Processing file %d/%d: %s", i+1, len(input_files), file_path)
                
                if not os.path.exists(file_path):
                    logger.warning("File does not exist: %s", file_path)
                    continue
                    
                try:
                    logger.trace("Loading audio file with mutagen: %s", file_path)
                    audio = mutagen.File(file_path)
                    
                    if audio is None:
                        logger.warning("Mutagen could not identify file format: %s", file_path)
                        continue
                        
                    if not hasattr(audio, 'info'):
                        logger.warning("Audio file has no info attribute: %s", file_path)
                        continue
                        
                    if not hasattr(audio.info, 'length'):
                        logger.warning("Audio info has no length attribute: %s", file_path)
                        continue
                        
                    file_runtime_seconds = int(audio.info.length)
                    total_runtime_seconds += file_runtime_seconds
                    processed_files += 1
                    
                    logger.debug("File %s: runtime=%d seconds, format=%s", 
                                file_path, file_runtime_seconds, audio.__class__.__name__)
                    logger.trace("Current total runtime: %d seconds after %d/%d files", 
                                total_runtime_seconds, i+1, len(input_files))
                    
                except Exception as e:
                    logger.warning("Error processing file %s: %s", file_path, e)
                    logger.trace("Exception details for %s: %s", file_path, str(e), exc_info=True)

            # Convert seconds to minutes, rounding to nearest minute
            total_runtime_minutes = round(total_runtime_seconds / 60)
            
            logger.info("Calculated total runtime: %d seconds (%d minutes) from %d/%d files", 
                        total_runtime_seconds, total_runtime_minutes, processed_files, len(input_files))
            
        except ImportError as e:
            logger.warning("Mutagen library not available, cannot calculate runtime: %s", str(e))
            return 0
        except Exception as e:
            logger.error("Unexpected error during runtime calculation: %s", str(e))
            logger.trace("Exception details: %s", str(e), exc_info=True)
            return 0

        logger.trace("Exiting _calculate_runtime() with total runtime=%d minutes", total_runtime_minutes)
        return total_runtime_minutes
    
def fetch_and_update_tonies_json(client: TeddyCloudClient, taf_file: Optional[str] = None, input_files: Optional[List[str]] = None, 
                               artwork_url: Optional[str] = None, output_dir: Optional[str] = None) -> bool:
    """
    Fetch tonies.custom.json from server and merge with local file if it exists, then update with new entry.
    
    Args:
        client: TeddyCloudClient instance to use for API communication
        taf_file: Path to the TAF file to add
        input_files: List of input audio files used to create the TAF
        artwork_url: URL of the uploaded artwork (if any)
        output_dir: Directory where to save the tonies.custom.json file (defaults to './output')
        
    Returns:
        True if successful, False otherwise
    """
    logger.trace("Entering fetch_and_update_tonies_json with client=%s, taf_file=%s, input_files=%s, artwork_url=%s, output_dir=%s",
                client, taf_file, input_files, artwork_url, output_dir)
    
    handler = ToniesJsonHandler(client)
    if not output_dir:
        output_dir = './output'
        logger.debug("No output directory specified, using default: %s", output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    logger.debug("Ensuring output directory exists: %s", output_dir)
    
    json_file_path = os.path.join(output_dir, 'tonies.custom.json')
    logger.debug("JSON file path: %s", json_file_path)
    
    loaded_from_server = False
    if client:
        logger.info("Attempting to load tonies.custom.json from server")
        loaded_from_server = handler.load_from_server()
        logger.debug("Load from server result: %s", "success" if loaded_from_server else "failed")
    else:
        logger.debug("No client provided, skipping server load")
    
    if os.path.exists(json_file_path):
        logger.info("Local tonies.custom.json file found, merging with server content")
        logger.debug("Local file exists at %s, size: %d bytes", json_file_path, os.path.getsize(json_file_path))
        
        local_handler = ToniesJsonHandler()
        if local_handler.load_from_file(json_file_path):
            logger.debug("Successfully loaded local file with %d entries", len(local_handler.custom_json))
            
            if loaded_from_server:
                logger.debug("Merging local entries with server entries")
                server_article_ids = {entry.get('article') for entry in handler.custom_json}
                logger.debug("Found %d unique article IDs from server", len(server_article_ids))
                
                added_count = 0
                for local_entry in local_handler.custom_json:
                    local_article_id = local_entry.get('article')
                    if local_article_id not in server_article_ids:
                        logger.trace("Adding local-only entry %s to merged content", local_article_id)
                        handler.custom_json.append(local_entry)
                        added_count += 1
                
                logger.debug("Added %d local-only entries to merged content", added_count)
            else:
                logger.debug("Using only local entries (server load failed or no client)")
                handler.custom_json = local_handler.custom_json
                handler.is_loaded = True
                logger.info("Using local tonies.custom.json content")
    elif not loaded_from_server:
        logger.debug("No local file found and server load failed, starting with empty list")
        handler.custom_json = []
        handler.is_loaded = True
        logger.info("No tonies.custom.json found, starting with empty list")
    
    if taf_file and input_files and handler.is_loaded:
        logger.debug("Adding new entry for TAF file: %s", taf_file)
        logger.debug("Using %d input files for metadata extraction", len(input_files))
        
        if not handler.add_entry_from_taf(taf_file, input_files, artwork_url):
            logger.error("Failed to add entry to tonies.custom.json")
            logger.trace("Exiting fetch_and_update_tonies_json with success=False (failed to add entry)")
            return False
        
        logger.debug("Successfully added new entry for %s", taf_file)
    else:
        if not taf_file:
            logger.debug("No TAF file provided, skipping add entry step")
        elif not input_files:
            logger.debug("No input files provided, skipping add entry step")
        elif not handler.is_loaded:
            logger.debug("Handler not properly loaded, skipping add entry step")
    
    logger.debug("Saving updated tonies.custom.json to %s", json_file_path)
    if not handler.save_to_file(json_file_path):
        logger.error("Failed to save tonies.custom.json to file")
        logger.trace("Exiting fetch_and_update_tonies_json with success=False (failed to save file)")
        return False
    
    logger.debug("Successfully saved tonies.custom.json with %d entries", len(handler.custom_json))
    logger.trace("Exiting fetch_and_update_tonies_json with success=True")
    return True