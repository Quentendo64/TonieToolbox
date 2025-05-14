#!/usr/bin/python3
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

logger = get_logger(__name__)

class ToniesJsonHandlerv1:
    """Handler for tonies.custom.json operations using v1 format."""
    
    def __init__(self, client: TeddyCloudClient = None):
        """
        Initialize the handler.
        
        Args:
            client (TeddyCloudClient | None): TeddyCloudClient instance to use for API communication
        """    
        self.client = client
        self.custom_json = []
        self.is_loaded = False

    def load_from_server(self) -> bool:
        """
        Load tonies.custom.json from the TeddyCloud server.
        
        Returns:
            bool: True if successful, False otherwise
        """          
        if self.client is None:
            logger.error("Cannot load from server: no client provided")
            return False
            
        try:
            result = self.client.get_tonies_custom_json()            
            if result is not None:
                # Convert v2 format to v1 format if necessary
                if len(result) > 0 and "data" in result[0]:
                    logger.debug("Converting v2 format from server to v1 format")
                    self.custom_json = self._convert_v2_to_v1(result)
                else:
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
            file_path (str): Path to the tonies.custom.json file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                logger.info("Loading tonies.custom.json from file: %s", file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Convert v2 format to v1 format if necessary
                        if len(data) > 0 and "data" in data[0]:
                            logger.debug("Converting v2 format from file to v1 format")
                            self.custom_json = self._convert_v2_to_v1(data)
                        else:
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
            file_path (str): Path where to save the tonies.custom.json file
            
        Returns:
            bool: True if successful, False otherwise
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
    
    def renumber_series_entries(self, series: str) -> None:
        """
        Re-sort and re-number all entries for a series by year (chronological),
        with entries without a year coming last.
        
        Args:
            series (str): Series name to renumber
        """
        # Collect all entries for the series
        series_entries = [entry for entry in self.custom_json if entry.get('series') == series]
        # Separate entries with and without year
        with_year = []
        without_year = []
        for entry in series_entries:
            year = self._extract_year_from_text(entry.get('title', ''))
            if not year:
                year = self._extract_year_from_text(entry.get('episodes', ''))
            if year:
                with_year.append((year, entry))
            else:
                without_year.append(entry)
        # Sort entries with year
        with_year.sort(key=lambda x: x[0])
        # Assign new numbers
        new_no = 1
        for _, entry in with_year:
            entry['no'] = str(new_no)
            new_no += 1
        for entry in without_year:
            entry['no'] = str(new_no)
            new_no += 1

    def add_entry_from_taf(self, taf_file: str, input_files: List[str], artwork_url: Optional[str] = None) -> bool:
        """
        Add an entry to the custom JSON from a TAF file.
        If an entry with the same hash exists, it will be updated.
        If an entry with the same series+episodes exists, the new hash will be added to it.
        
        Args:
            taf_file (str): Path to the TAF file
            input_files (list[str]): List of input audio files used to create the TAF
            artwork_url (str | None): URL of the uploaded artwork (if any)
            
        Returns:
            bool: True if successful, False otherwise
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
                taf_hash = hashlib.sha1(f.read()).hexdigest().upper()
            
            timestamp = str(int(time.time()))
            series = metadata.get('albumartist', metadata.get('artist', 'Unknown Artist'))
            episodes = metadata.get('album', os.path.splitext(os.path.basename(taf_file))[0])
            copyright = metadata.get('copyright', '')
            
            # Extract year from metadata or from episode title
            year = None
            year_str = metadata.get('year', metadata.get('date', None))
            
            # Try to convert metadata year to int if it exists
            if year_str:
                try:
                    # Extract 4 digits if the date includes more information (e.g., "2022-05-01")
                    import re
                    year_match = re.search(r'(\d{4})', str(year_str))
                    if year_match:
                        year = int(year_match.group(1))
                    else:
                        # If year is just a number, try to format it properly
                        year_val = int(year_str)
                        if 0 <= year_val <= 99:  # Assume 2-digit year format
                            if year_val <= 25:  # Arbitrary cutoff for 20xx vs 19xx
                                year = 2000 + year_val
                            else:
                                year = 1900 + year_val
                        else:
                            year = year_val
                except (ValueError, TypeError):
                    logger.debug("Could not convert metadata year '%s' to integer", year_str)
            
            if not year:
                year_from_episodes = self._extract_year_from_text(episodes)
                year_from_copyright = self._extract_year_from_text(copyright)            
                if year_from_episodes:
                    year = year_from_episodes
                else:
                    year = year_from_copyright
            
            # Ensure year is in YYYY format
            year_formatted = None
            if year:
                # Validate the year is in the reasonable range
                if 1900 <= year <= 2099:
                    year_formatted = f"{year:04d}"  # Format as 4 digits
                    logger.debug("Formatted year '%s' as '%s'", year, year_formatted)
                else:
                    logger.warning("Year '%s' outside reasonable range (1900-2099), ignoring", year)
            
            if year_formatted:
                title = f"{series} - {year_formatted} - {episodes}"
            else:
                title = f"{series} - {episodes}"
            
            tracks = metadata.get('track_descriptions', [])
            language = self._determine_language(metadata)
            category = self._determine_category_v1(metadata)
            
            existing_entry, entry_idx = self.find_entry_by_hash(taf_hash)
            if existing_entry:
                logger.info("Found existing entry with the same hash, updating it")
                if artwork_url and artwork_url != existing_entry.get('pic', ''):
                    logger.debug("Updating artwork URL")
                    existing_entry['pic'] = artwork_url
                if tracks and tracks != existing_entry.get('tracks', []):
                    logger.debug("Updating track descriptions")
                    existing_entry['tracks'] = tracks
                if episodes and episodes != existing_entry.get('episodes', ''):
                    logger.debug("Updating episodes")
                    existing_entry['episodes'] = episodes
                if series and series != existing_entry.get('series', ''):
                    logger.debug("Updating series")
                    existing_entry['series'] = series                
                logger.info("Successfully updated existing entry for %s", taf_file)
                self.renumber_series_entries(series)
                return True
            
            existing_entry, entry_idx = self.find_entry_by_series_episodes(series, episodes)
            if existing_entry:
                logger.info("Found existing entry with the same series/episodes, adding hash to it")
                if 'audio_id' not in existing_entry:
                    existing_entry['audio_id'] = []
                if 'hash' not in existing_entry:
                    existing_entry['hash'] = []
                
                existing_entry['audio_id'].append(timestamp)
                existing_entry['hash'].append(taf_hash)
                
                if artwork_url and artwork_url != existing_entry.get('pic', ''):
                    logger.debug("Updating artwork URL")
                    existing_entry['pic'] = artwork_url
                
                logger.info("Successfully added new hash to existing entry for %s", taf_file)
                self.renumber_series_entries(series)
                return True
            
            logger.debug("No existing entry found, creating new entry")
            
            logger.debug("Generating entry number")
            entry_no = self._generate_entry_no(series, episodes, year)
            logger.debug("Generated entry number: %s", entry_no)
            
            logger.debug("Generating model number")
            model_number = self._generate_model_number()
            logger.debug("Generated model number: %s", model_number)
            
            entry = {
                "no": entry_no,
                "model": model_number,
                "audio_id": [timestamp],
                "hash": [taf_hash],
                "title": title,
                "series": series,
                "episodes": episodes,
                "tracks": tracks,
                "release": timestamp,
                "language": language,
                "category": category,
                "pic": artwork_url if artwork_url else ""
            }
            
            self.custom_json.append(entry)
            logger.debug("Added entry to custom_json (new length: %d)", len(self.custom_json))
            
            logger.info("Successfully added entry for %s", taf_file)
            self.renumber_series_entries(series)
            logger.trace("Exiting add_entry_from_taf() with success=True")
            return True
            
        except Exception as e:
            logger.error("Error adding entry for %s: %s", taf_file, e)
            logger.trace("Exiting add_entry_from_taf() with success=False due to exception: %s", str(e))
            return False
    
    def _generate_entry_no(self, series: str, episodes: str, year: Optional[int] = None) -> str:
        """
        Generate an entry number based on specific rules:
        1. For series entries with years: assign numbers in chronological order (1, 2, 3, etc.)
        2. For entries without years: assign the next available number after those with years
        
        Args:
            series (str): Series name
            episodes (str): Episodes name
            year (int | None): Release year from metadata, if available
            
        Returns:
            str: Generated entry number as string
        """
        logger.trace("Entering _generate_entry_no() with series='%s', episodes='%s', year=%s", 
                    series, episodes, year)
        
        # If we don't have a series name, use a simple approach to get the next number
        if not series:
            max_no = 0
            for entry in self.custom_json:
                try:
                    no_value = int(entry.get('no', '0'))
                    max_no = max(max_no, no_value)
                except (ValueError, TypeError):
                    pass
            return str(max_no + 1)
        
        logger.debug("Generating entry number for series '%s'", series)
        
        # Step 1: Collect all existing entries for this series and extract their years
        series_entries = []
        used_numbers = set()
        
        for entry in self.custom_json:
            entry_series = entry.get('series', '')
            if entry_series == series:
                entry_no = entry.get('no', '')
                try:
                    entry_no_int = int(entry_no)
                    used_numbers.add(entry_no_int)
                except (ValueError, TypeError):
                    pass
                
                entry_title = entry.get('title', '')
                entry_episodes = entry.get('episodes', '')
                
                # Extract year from title and episodes
                entry_year = self._extract_year_from_text(entry_title)
                if not entry_year:
                    entry_year = self._extract_year_from_text(entry_episodes)
                
                series_entries.append({
                    'no': entry_no,
                    'title': entry_title,
                    'episodes': entry_episodes,
                    'year': entry_year
                })
        
        # Try to extract year from episodes if not explicitly provided
        if not year:
            extracted_year = self._extract_year_from_text(episodes)
            if extracted_year:
                year = extracted_year
                logger.debug("Extracted year %d from episodes '%s'", year, episodes)
        
        # Step 2: Split entries into those with years and those without
        entries_with_years = [e for e in series_entries if e['year'] is not None]
        entries_without_years = [e for e in series_entries if e['year'] is None]
        
        # Sort entries with years by year (oldest first)
        entries_with_years.sort(key=lambda x: x['year'])
        
        logger.debug("Found %d entries with years and %d entries without years", 
                    len(entries_with_years), len(entries_without_years))
        
        # Step 3: If this entry has a year, determine where it should be inserted
        if year:
            # Find position based on chronological order
            insertion_index = 0
            while insertion_index < len(entries_with_years) and entries_with_years[insertion_index]['year'] < year:
                insertion_index += 1
            
            # Resulting position is 1-indexed
            position = insertion_index + 1
            logger.debug("For year %d, calculated position %d based on chronological order", year, position)
            
            # Now adjust position if needed to avoid conflicts with existing entries
            while position in used_numbers:
                position += 1
                logger.debug("Position %d already used, incrementing to %d", position-1, position)
            
            logger.debug("Final assigned entry number: %d", position)
            return str(position)
        else:
            # Step 4: If this entry has no year, it should come after all entries with years
            # Find the highest number used by entries with years
            years_highest_no = 0
            if entries_with_years:
                for i, entry in enumerate(entries_with_years):
                    try:
                        expected_no = i + 1  # 1-indexed
                        actual_no = int(entry['no'])
                        years_highest_no = max(years_highest_no, actual_no)
                    except (ValueError, TypeError):
                        pass
            
            # Find the highest number used overall
            highest_no = max(used_numbers) if used_numbers else 0
            
            # Next number should be at least one more than the highest from entries with years
            next_no = max(years_highest_no, highest_no) + 1
            
            logger.debug("No year available, assigned next number: %d", next_no)
            return str(next_no)
    
    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """
        Extract a year (1900-2099) from text.
        
        Args:
            text (str): The text to extract the year from
            
        Returns:
            int | None: The extracted year as int, or None if no valid year found
        """
        import re
        year_pattern = re.compile(r'(19\d{2}|20\d{2})')
        year_match = year_pattern.search(text)
        
        if year_match:
            try:
                extracted_year = int(year_match.group(1))
                if 1900 <= extracted_year <= 2099:
                    return extracted_year
            except (ValueError, TypeError):
                pass
                
        return None
    
    def _format_number(self, number: int, existing_entries: List[Dict[str, Any]]) -> str:
        """
        Format a number to match the existing entry number format (e.g., with leading zeros).
        
        Args:
            number (int): The number to format
            existing_entries (list[dict]): List of existing entries with their numbers
            
        Returns:
            str: Formatted number as string
        """
        max_digits = 1
        for entry in existing_entries:
            entry_no = entry.get('no', '')
            if entry_no and isinstance(entry_no, str) and entry_no.isdigit():
                leading_zeros = len(entry_no) - len(entry_no.lstrip('0'))
                if leading_zeros > 0:
                    digits = len(entry_no)
                    max_digits = max(max_digits, digits)
        if max_digits > 1:
            logger.trace("Formatting with %d digits", max_digits)
            return f"{number:0{max_digits}d}"
        
        return str(number)
    
    def _generate_model_number(self) -> str:
        """
        Generate a unique model number for a new entry.
        
        Returns:
            str: Unique model number in the format "model-" followed by sequential number with zero padding
        """
        logger.trace("Entering _generate_model_number()")
        highest_num = -1
        pattern = re.compile(r'tt-42(\d+)')
        
        logger.debug("Searching for highest tt-42 ID in %d existing entries", len(self.custom_json))
        for entry in self.custom_json:
            model = entry.get('model', '')
            logger.trace("Checking model ID: %s", model)
            match = pattern.match(model)
            if match:
                try:
                    num = int(match.group(1))
                    logger.trace("Found numeric part: %d", num)
                    highest_num = max(highest_num, num)
                except (IndexError, ValueError) as e:
                    logger.trace("Failed to parse model ID: %s (%s)", model, str(e))
                    pass
        
        logger.debug("Highest tt-42 ID number found: %d", highest_num)
        next_num = highest_num + 1
        result = f"tt-42{next_num:010d}"
        logger.debug("Generated new model ID: %s", result)
        
        logger.trace("Exiting _generate_model_number() with result=%s", result)
        return result
    
    def _determine_category_v1(self, metadata: Dict[str, Any]) -> str:
        """
        Determine the category in v1 format.
        
        Args:
            metadata (dict): Dictionary containing file metadata
            
        Returns:
            str: Category string in v1 format
        """
        if 'genre' in metadata:
            genre_value = metadata['genre'].lower().strip()
            
            if any(keyword in genre_value for keyword in ['musik', 'song', 'music', 'lied']):
                return "music"
            elif any(keyword in genre_value for keyword in ['hörspiel', 'audio play', 'hörbuch', 'audiobook']):
                return "audio-play"
            elif any(keyword in genre_value for keyword in ['märchen', 'fairy', 'tales']):
                return "fairy-tale"
            elif any(keyword in genre_value for keyword in ['wissen', 'knowledge', 'learn']):
                return "knowledge"
            elif any(keyword in genre_value for keyword in ['schlaf', 'sleep', 'meditation']):
                return "sleep"
        
        return "audio-play"
    
    def find_entry_by_hash(self, taf_hash: str) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """
        Find an entry in the custom JSON by TAF hash.
        
        Args:
            taf_hash (str): SHA1 hash of the TAF file to find
            
        Returns:
            tuple[dict | None, int | None]: Tuple of (entry, entry_index) if found, or (None, None) if not found
        """
        logger.trace("Searching for entry with hash %s", taf_hash)
        
        for entry_idx, entry in enumerate(self.custom_json):
            if 'hash' not in entry:
                continue
                
            for hash_value in entry['hash']:
                if hash_value == taf_hash:
                    logger.debug("Found existing entry with matching hash %s", taf_hash)
                    return entry, entry_idx
        
        logger.debug("No entry found with hash %s", taf_hash)
        return None, None
    
    def find_entry_by_series_episodes(self, series: str, episodes: str) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """
        Find an entry in the custom JSON by series and episodes.
        
        Args:
            series (str): Series name to find
            episodes (str): Episodes name to find
            
        Returns:
            tuple[dict | None, int | None]: Tuple of (entry, entry_index) if found, or (None, None) if not found
        """
        logger.trace("Searching for entry with series='%s', episodes='%s'", series, episodes)
        
        for entry_idx, entry in enumerate(self.custom_json):
            if entry.get('series') == series and entry.get('episodes') == episodes:
                logger.debug("Found existing entry with matching series/episodes: %s / %s", series, episodes)
                return entry, entry_idx
        
        logger.debug("No entry found with series/episodes: %s / %s", series, episodes)
        return None, None

    def _extract_metadata_from_files(self, input_files: List[str]) -> Dict[str, Any]:
        """
        Extract metadata from audio files to use in the custom JSON entry.
        
        Args:
            input_files (list[str]): List of paths to audio files
            
        Returns:
            dict: Dictionary containing metadata extracted from files
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
            for tag_name, tag_value in tags.items():
                if tag_name not in metadata:
                    metadata[tag_name] = tag_value
        
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
    
    def _convert_v2_to_v1(self, v2_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert data from v2 format to v1 format.
        
        Args:
            v2_data (list[dict]): Data in v2 format
            
        Returns:
            list[dict]: Converted data in v1 format
        """
        v1_data = []
        
        entry_no = 0
        for v2_entry in v2_data:
            if 'data' not in v2_entry:
                continue
                
            for v2_data_item in v2_entry['data']:
                series = v2_data_item.get('series', '')
                episodes = v2_data_item.get('episode', '')
                model = v2_data_item.get('article', '')
                title = f"{series} - {episodes}" if series and episodes else episodes
                
                v1_entry = {
                    "no": str(entry_no),
                    "model": model,
                    "audio_id": [],
                    "hash": [],
                    "title": title,
                    "series": series,
                    "episodes": episodes,
                    "tracks": v2_data_item.get('track-desc', []),
                    "release": str(v2_data_item.get('release', int(time.time()))),
                    "language": v2_data_item.get('language', 'de-de'),
                    "category": self._convert_category_v2_to_v1(v2_data_item.get('category', '')),
                    "pic": v2_data_item.get('image', '')
                }
                if 'ids' in v2_data_item:
                    for id_entry in v2_data_item['ids']:
                        if 'audio-id' in id_entry:
                            v1_entry['audio_id'].append(str(id_entry['audio-id']))
                        if 'hash' in id_entry:
                            v1_entry['hash'].append(id_entry['hash'].upper())
                
                v1_data.append(v1_entry)
                entry_no += 1
        
        return v1_data
    
    def _convert_category_v2_to_v1(self, v2_category: str) -> str:
        """
        Convert category from v2 format to v1 format.
        
        Args:
            v2_category (str): Category in v2 format
            
        Returns:
            str: Category in v1 format
        """
        v2_to_v1_mapping = {
            "music": "music",
            "Hörspiele & Hörbücher": "audio-play",
            "Schlaflieder & Entspannung": "sleep",
            "Wissen & Hörmagazine": "knowledge",
            "Märchen": "fairy-tale"
        }
        
        return v2_to_v1_mapping.get(v2_category, "audio-play")

class ToniesJsonHandlerv2:
    """Handler for tonies.custom.json operations."""
    
    def __init__(self, client: TeddyCloudClient = None):
        """
        Initialize the handler.
        
        Args:
            client (TeddyCloudClient | None): TeddyCloudClient instance to use for API communication
        """    
        self.client = client
        self.custom_json = []
        self.is_loaded = False

    def load_from_server(self) -> bool:
        """
        Load tonies.custom.json from the TeddyCloud server.
        
        Returns:
            bool: True if successful, False otherwise
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
            file_path (str): Path to the tonies.custom.json file
            
        Returns:
            bool: True if successful, False otherwise
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
            file_path (str): Path where to save the tonies.custom.json file
            
        Returns:
            bool: True if successful, False otherwise
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
            taf_file (str): Path to the TAF file
            input_files (list[str]): List of input audio files used to create the TAF
            artwork_url (str | None): URL of the uploaded artwork (if any)
            
        Returns:
            bool: True if successful, False otherwise
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
            str: Unique article ID in the format "tt-42" followed by sequential number starting from 0
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
            input_files (list[str]): List of paths to audio files
            
        Returns:
            dict: Dictionary containing metadata extracted from files
        """
        metadata = {}
        track_descriptions = []
        for file_path in input_files:
            tags = get_file_tags(file_path)
            # Extract track descriptions
            if 'title' in tags:
                track_descriptions.append(tags['title'])
            else:
                filename = os.path.splitext(os.path.basename(file_path))[0]
                track_descriptions.append(filename)
            
            # Copy all available tags, but don't overwrite existing ones
            for tag_name, tag_value in tags.items():
                if tag_name not in metadata:
                    metadata[tag_name] = tag_value
        
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
            taf_hash (str): SHA1 hash of the TAF file to find
            
        Returns:
            tuple[dict | None, int | None, int | None]: Tuple of (entry, entry_index, data_index) if found, or (None, None, None) if not found
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
            series (str): Series name to find
            episode (str): Episode name to find
            
        Returns:
            tuple[dict | None, int | None, int | None]: Tuple of (entry, entry_index, data_index) if found, or (None, None, None) if not found
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
            input_files (list[str]): List of paths to audio files

        Returns:
            int: Total runtime in minutes (rounded to the nearest minute)
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
    
def fetch_and_update_tonies_json_v1(client: TeddyCloudClient, taf_file: Optional[str] = None, input_files: Optional[List[str]] = None, 
                               artwork_url: Optional[str] = None, output_dir: Optional[str] = None) -> bool:
    """
    Fetch tonies.custom.json from server and merge with local file if it exists, then update with new entry in v1 format.
    
    Args:
        client (TeddyCloudClient): TeddyCloudClient instance to use for API communication
        taf_file (str | None): Path to the TAF file to add
        input_files (list[str] | None): List of input audio files used to create the TAF
        artwork_url (str | None): URL of the uploaded artwork (if any)
        output_dir (str | None): Directory where to save the tonies.custom.json file (defaults to './output')
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.trace("Entering fetch_and_update_tonies_json_v1 with client=%s, taf_file=%s, input_files=%s, artwork_url=%s, output_dir=%s",
                client, taf_file, input_files, artwork_url, output_dir)
    
    handler = ToniesJsonHandlerv1(client)
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
        
        local_handler = ToniesJsonHandlerv1()
        if local_handler.load_from_file(json_file_path):
            logger.debug("Successfully loaded local file with %d entries", len(local_handler.custom_json))
            
            if loaded_from_server:
                logger.debug("Merging local entries with server entries")
                server_hashes = set()
                for entry in handler.custom_json:
                    if 'hash' in entry:
                        for hash_value in entry['hash']:
                            server_hashes.add(hash_value)
                
                logger.debug("Found %d unique hash values from server", len(server_hashes))
                
                added_count = 0
                for local_entry in local_handler.custom_json:
                    if 'hash' in local_entry:
                        has_unique_hash = False
                        for hash_value in local_entry['hash']:
                            if hash_value not in server_hashes:
                                has_unique_hash = True
                                break
                        
                        if has_unique_hash:
                            logger.trace("Adding local-only entry to merged content")
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
            logger.trace("Exiting fetch_and_update_tonies_json_v1 with success=False (failed to add entry)")
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
        logger.trace("Exiting fetch_and_update_tonies_json_v1 with success=False (failed to save file)")
        return False
    
    logger.debug("Successfully saved tonies.custom.json with %d entries", len(handler.custom_json))
    logger.trace("Exiting fetch_and_update_tonies_json_v1 with success=True")
    return True

def fetch_and_update_tonies_json_v2(client: TeddyCloudClient, taf_file: Optional[str] = None, input_files: Optional[List[str]] = None, 
                               artwork_url: Optional[str] = None, output_dir: Optional[str] = None) -> bool:
    """
    Fetch tonies.custom.json from server and merge with local file if it exists, then update with new entry.
    
    Args:
        client (TeddyCloudClient): TeddyCloudClient instance to use for API communication
        taf_file (str | None): Path to the TAF file to add
        input_files (list[str] | None): List of input audio files used to create the TAF
        artwork_url (str | None): URL of the uploaded artwork (if any)
        output_dir (str | None): Directory where to save the tonies.custom.json file (defaults to './output')
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.trace("Entering fetch_and_update_tonies_json with client=%s, taf_file=%s, input_files=%s, artwork_url=%s, output_dir=%s",
                client, taf_file, input_files, artwork_url, output_dir)
    
    handler = ToniesJsonHandlerv2(client)
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
        
        local_handler = ToniesJsonHandlerv2()
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