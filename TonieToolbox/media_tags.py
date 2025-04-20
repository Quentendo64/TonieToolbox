"""
Media tag processing functionality for the TonieToolbox package

This module handles reading and processing metadata tags from audio files,
which can be used to enhance Tonie file creation with proper track information.
"""

import os
from typing import Dict, Any, Optional, List
import logging
from .logger import get_logger
from .dependency_manager import is_mutagen_available, ensure_mutagen

# Global variables to track dependency state and store module references
MUTAGEN_AVAILABLE = False
mutagen = None
ID3 = None
FLAC = None
MP4 = None
OggOpus = None
OggVorbis = None

def _import_mutagen():
    """
    Import the mutagen modules and update global variables.
    
    Returns:
        bool: True if import was successful, False otherwise
    """
    global MUTAGEN_AVAILABLE, mutagen, ID3, FLAC, MP4, OggOpus, OggVorbis
    
    try:
        import mutagen as _mutagen
        from mutagen.id3 import ID3 as _ID3
        from mutagen.flac import FLAC as _FLAC
        from mutagen.mp4 import MP4 as _MP4
        from mutagen.oggopus import OggOpus as _OggOpus
        from mutagen.oggvorbis import OggVorbis as _OggVorbis
        
        # Assign to global variables
        mutagen = _mutagen
        ID3 = _ID3
        FLAC = _FLAC
        MP4 = _MP4
        OggOpus = _OggOpus
        OggVorbis = _OggVorbis
        MUTAGEN_AVAILABLE = True
        return True
    except ImportError:
        MUTAGEN_AVAILABLE = False
        return False

# Try to import mutagen if it's available
if is_mutagen_available():
    _import_mutagen()

logger = get_logger('media_tags')

# Define tag mapping for different formats to standardized names
# This helps normalize tags across different audio formats
TAG_MAPPING = {
    # ID3 (MP3) tags
    'TIT2': 'title',
    'TALB': 'album',
    'TPE1': 'artist',
    'TPE2': 'albumartist',
    'TCOM': 'composer',
    'TRCK': 'tracknumber',
    'TPOS': 'discnumber',
    'TDRC': 'date',
    'TCON': 'genre',
    'TPUB': 'publisher',
    'TCOP': 'copyright',
    'COMM': 'comment',
    
    # Vorbis tags (FLAC, OGG)
    'title': 'title',
    'album': 'album',
    'artist': 'artist',
    'albumartist': 'albumartist',
    'composer': 'composer',
    'tracknumber': 'tracknumber',
    'discnumber': 'discnumber',
    'date': 'date',
    'genre': 'genre',
    'publisher': 'publisher',
    'copyright': 'copyright',
    'comment': 'comment',
    
    # MP4 (M4A, AAC) tags
    '©nam': 'title',
    '©alb': 'album',
    '©ART': 'artist',
    'aART': 'albumartist',
    '©wrt': 'composer',
    'trkn': 'tracknumber',
    'disk': 'discnumber',
    '©day': 'date',
    '©gen': 'genre',
    '©pub': 'publisher',
    'cprt': 'copyright',
    '©cmt': 'comment',
    
    # Additional tags some files might have
    'album_artist': 'albumartist',
    'track': 'tracknumber',
    'track_number': 'tracknumber',
    'disc': 'discnumber',
    'disc_number': 'discnumber',
    'year': 'date',
    'albuminterpret': 'albumartist',  # German tag name
    'interpret': 'artist',            # German tag name
}

# Define replacements for special tag values
TAG_VALUE_REPLACEMENTS = {
    "Die drei ???": "Die drei Fragezeichen",
    "Die Drei ???": "Die drei Fragezeichen",
    "DIE DREI ???": "Die drei Fragezeichen",
    "Die drei !!!": "Die drei Ausrufezeichen",
    "Die Drei !!!": "Die drei Ausrufezeichen",
    "DIE DREI !!!": "Die drei Ausrufezeichen",
    "TKKG™": "TKKG",
    "Die drei ??? Kids": "Die drei Fragezeichen Kids",
    "Die Drei ??? Kids": "Die drei Fragezeichen Kids",
    "Bibi & Tina": "Bibi und Tina",
    "Benjamin Blümchen™": "Benjamin Blümchen",
    "???": "Fragezeichen",
    "!!!": "Ausrufezeichen",
}

def normalize_tag_value(value: str) -> str:
    """
    Normalize tag values by replacing special characters or known patterns
    with more file-system-friendly alternatives.
    
    Args:
        value: The original tag value
        
    Returns:
        Normalized tag value
    """
    if not value:
        return value
        
    # Check for direct replacements first
    if value in TAG_VALUE_REPLACEMENTS:
        logger.debug("Direct tag replacement: '%s' -> '%s'", value, TAG_VALUE_REPLACEMENTS[value])
        return TAG_VALUE_REPLACEMENTS[value]
    
    # Check for partial matches and replacements
    result = value
    for pattern, replacement in TAG_VALUE_REPLACEMENTS.items():
        if pattern in result:
            original = result
            result = result.replace(pattern, replacement)
            logger.debug("Partial tag replacement: '%s' -> '%s'", original, result)
    
    # Special case for "Die drei ???" type patterns that might have been missed
    result = result.replace("???", "Fragezeichen")
    
    return result

def is_available() -> bool:
    """
    Check if tag reading functionality is available.
    
    Returns:
        bool: True if mutagen is available, False otherwise
    """
    return MUTAGEN_AVAILABLE or is_mutagen_available()

def get_file_tags(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata tags from an audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dictionary containing standardized tag names and values
    """
    global MUTAGEN_AVAILABLE
    
    if not MUTAGEN_AVAILABLE:
        # Try to ensure mutagen is available
        if ensure_mutagen(auto_install=True):
            # If successful, import the necessary modules
            if not _import_mutagen():
                logger.warning("Mutagen library not available. Cannot read media tags.")
                return {}
        else:
            logger.warning("Mutagen library not available. Cannot read media tags.")
            return {}
        
    logger.debug("Reading tags from file: %s", file_path)
    tags = {}
    
    try:
        # Use mutagen to identify and load the file
        audio = mutagen.File(file_path)
        if audio is None:
            logger.warning("Could not identify file format: %s", file_path)
            return tags
            
        # Process different file types
        if isinstance(audio, ID3) or hasattr(audio, 'ID3'):
            # MP3 files
            id3 = audio if isinstance(audio, ID3) else audio.ID3
            for tag_key, tag_value in id3.items():
                tag_name = tag_key.split(':')[0]  # Handle ID3 tags with colons
                if tag_name in TAG_MAPPING:
                    tag_value_str = str(tag_value)
                    tags[TAG_MAPPING[tag_name]] = normalize_tag_value(tag_value_str)
        elif isinstance(audio, (FLAC, OggOpus, OggVorbis)):
            # FLAC and OGG files
            for tag_key, tag_values in audio.items():
                tag_key_lower = tag_key.lower()
                if tag_key_lower in TAG_MAPPING:
                    # Some tags might have multiple values, we'll take the first one
                    tag_value = tag_values[0] if tag_values else ''
                    tags[TAG_MAPPING[tag_key_lower]] = normalize_tag_value(tag_value)
        elif isinstance(audio, MP4):
            # MP4 files
            for tag_key, tag_value in audio.items():
                if tag_key in TAG_MAPPING:
                    if isinstance(tag_value, list):
                        if tag_key in ('trkn', 'disk'):
                            # Handle track and disc number tuples
                            if tag_value and isinstance(tag_value[0], tuple) and len(tag_value[0]) >= 1:
                                tags[TAG_MAPPING[tag_key]] = str(tag_value[0][0])
                        else:
                            tag_value_str = str(tag_value[0]) if tag_value else ''
                            tags[TAG_MAPPING[tag_key]] = normalize_tag_value(tag_value_str)
                    else:
                        tag_value_str = str(tag_value)
                        tags[TAG_MAPPING[tag_key]] = normalize_tag_value(tag_value_str)
        else:
            # Generic audio file - try to read any available tags
            for tag_key, tag_value in audio.items():
                tag_key_lower = tag_key.lower()
                if tag_key_lower in TAG_MAPPING:
                    if isinstance(tag_value, list):
                        tag_value_str = str(tag_value[0]) if tag_value else ''
                        tags[TAG_MAPPING[tag_key_lower]] = normalize_tag_value(tag_value_str)
                    else:
                        tag_value_str = str(tag_value)
                        tags[TAG_MAPPING[tag_key_lower]] = normalize_tag_value(tag_value_str)
                        
        logger.debug("Successfully read %d tags from file", len(tags))
        return tags
    except Exception as e:
        logger.error("Error reading tags from file %s: %s", file_path, str(e))
        return tags

def extract_first_audio_file_tags(folder_path: str) -> Dict[str, str]:
    """
    Extract tags from the first audio file in a folder.
    
    Args:
        folder_path: Path to folder containing audio files
        
    Returns:
        Dictionary containing standardized tag names and values
    """
    from .audio_conversion import filter_directories
    import glob
    
    logger.debug("Looking for audio files in %s", folder_path)
    files = filter_directories(glob.glob(os.path.join(folder_path, "*")))
    
    if not files:
        logger.debug("No audio files found in folder")
        return {}
        
    # Get tags from the first file
    first_file = files[0]
    logger.debug("Using first audio file for tags: %s", first_file)
    
    return get_file_tags(first_file)

def extract_album_info(folder_path: str) -> Dict[str, str]:
    """
    Extract album information from audio files in a folder.
    Tries to get consistent album, artist and other information.
    
    Args:
        folder_path: Path to folder containing audio files
        
    Returns:
        Dictionary with extracted metadata (album, albumartist, etc.)
    """
    from .audio_conversion import filter_directories
    import glob
    
    logger.debug("Extracting album information from folder: %s", folder_path)
    
    # Get all audio files in the folder
    audio_files = filter_directories(glob.glob(os.path.join(folder_path, "*")))
    if not audio_files:
        logger.debug("No audio files found in folder")
        return {}
    
    # Collect tag information from all files
    all_tags = []
    for file_path in audio_files:
        tags = get_file_tags(file_path)
        if tags:
            all_tags.append(tags)
    
    if not all_tags:
        logger.debug("Could not read tags from any files in folder")
        return {}
    
    # Try to find consistent album information
    result = {}
    key_tags = ['album', 'albumartist', 'artist', 'date', 'genre']
    
    for tag_name in key_tags:
        # Count occurrences of each value
        value_counts = {}
        for tags in all_tags:
            if tag_name in tags:
                value = tags[tag_name]
                if value in value_counts:
                    value_counts[value] += 1
                else:
                    value_counts[value] = 1
        
        # Use the most common value, or the first one if there's a tie
        if value_counts:
            most_common_value = max(value_counts.items(), key=lambda x: x[1])[0]
            result[tag_name] = most_common_value
    
    logger.debug("Extracted album info: %s", str(result))
    return result

def get_file_metadata(file_path: str) -> Dict[str, str]:
    """
    Get comprehensive metadata about a single audio file,
    including both file tags and additional information.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dictionary containing metadata information
    """
    metadata = {}
    
    # Get basic file information
    try:
        basename = os.path.basename(file_path)
        filename, extension = os.path.splitext(basename)
        
        metadata['filename'] = filename
        metadata['extension'] = extension.lower().replace('.', '')
        metadata['path'] = file_path
        
        # Get file size
        metadata['filesize'] = os.path.getsize(file_path)
        
        # Add tags from the file
        tags = get_file_tags(file_path)
        metadata.update(tags)
        
        return metadata
    except Exception as e:
        logger.error("Error getting file metadata for %s: %s", file_path, str(e))
        return metadata

def get_folder_metadata(folder_path: str) -> Dict[str, Any]:
    """
    Get comprehensive metadata about a folder of audio files.
    
    Args:
        folder_path: Path to folder containing audio files
        
    Returns:
        Dictionary containing metadata information and list of files
    """
    folder_metadata = {}
    
    # Get basic folder information
    folder_metadata['folder_name'] = os.path.basename(folder_path)
    folder_metadata['folder_path'] = folder_path
    
    # Try to extract album info
    album_info = extract_album_info(folder_path)
    folder_metadata.update(album_info)
    
    # Also get folder name metadata using existing function
    from .recursive_processor import extract_folder_meta
    folder_name_meta = extract_folder_meta(folder_path)
    
    # Combine the metadata, prioritizing tag-based over folder name based
    for key, value in folder_name_meta.items():
        if key not in folder_metadata or not folder_metadata[key]:
            folder_metadata[key] = value
    
    # Get list of audio files with their metadata
    from .audio_conversion import filter_directories
    import glob
    
    audio_files = filter_directories(glob.glob(os.path.join(folder_path, "*")))
    files_metadata = []
    
    for file_path in audio_files:
        file_metadata = get_file_metadata(file_path)
        files_metadata.append(file_metadata)
    
    folder_metadata['files'] = files_metadata
    folder_metadata['file_count'] = len(files_metadata)
    
    return folder_metadata

def format_metadata_filename(metadata: Dict[str, str], template: str = "{tracknumber} - {title}") -> str:
    """
    Format a filename using metadata and a template string.
    
    Args:
        metadata: Dictionary of metadata tags
        template: Template string with placeholders matching metadata keys
        
    Returns:
        Formatted string, or empty string if formatting fails
    """
    try:
        # Format track numbers correctly (e.g., "1" -> "01")
        if 'tracknumber' in metadata:
            track = metadata['tracknumber']
            if '/' in track:  # Handle "1/10" format
                track = track.split('/')[0]
            try:
                metadata['tracknumber'] = f"{int(track):02d}"
            except (ValueError, TypeError):
                pass  # Keep original value if not a simple number
                
        # Format disc numbers the same way
        if 'discnumber' in metadata:
            disc = metadata['discnumber']
            if '/' in disc:  # Handle "1/2" format
                disc = disc.split('/')[0]
            try:
                metadata['discnumber'] = f"{int(disc):02d}"
            except (ValueError, TypeError):
                pass
        
        # Substitute keys in template
        result = template
        for key, value in metadata.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
                
        # Clean up any remaining placeholders for missing metadata
        import re
        result = re.sub(r'\{[^}]+\}', '', result)
        
        # Clean up consecutive spaces, dashes, etc.
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'[-_\s]*-[-_\s]*', ' - ', result)
        result = re.sub(r'^\s+|\s+$', '', result)  # trim
        
        # Replace characters that aren't allowed in filenames
        result = re.sub(r'[<>:"/\\|?*]', '-', result)
        
        return result
    except Exception as e:
        logger.error("Error formatting metadata: %s", str(e))
        return ""