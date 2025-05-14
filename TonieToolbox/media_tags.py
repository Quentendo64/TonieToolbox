#!/usr/bin/python3
"""
Media tag processing functionality for the TonieToolbox package

This module handles reading and processing metadata tags from audio files,
which can be used to enhance Tonie file creation with proper track information.
"""

import os
from typing import Dict, Any, Optional, List
import logging
import tempfile
import base64
from mutagen.flac import Picture
from .logger import get_logger
from .dependency_manager import is_mutagen_available, ensure_mutagen
from .constants import ARTWORK_NAMES, ARTWORK_EXTENSIONS, TAG_VALUE_REPLACEMENTS, TAG_MAPPINGS
logger = get_logger(__name__)

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

if is_mutagen_available():
    _import_mutagen()

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
            try:
                id3 = audio if isinstance(audio, ID3) else audio.ID3
                for tag_key, tag_value in id3.items():
                    tag_name = tag_key.split(':')[0]  # Handle ID3 tags with colons
                    if tag_name in TAG_MAPPINGS:
                        tag_value_str = str(tag_value)
                        tags[TAG_MAPPINGS[tag_name]] = normalize_tag_value(tag_value_str)
            except (AttributeError, TypeError) as e:
                logger.debug("Error accessing ID3 tags: %s", e)
                # Try alternative approach for ID3 tags
                try:
                    if hasattr(audio, 'tags') and audio.tags:
                        for tag_key in audio.tags.keys():
                            if tag_key in TAG_MAPPINGS:
                                tag_value = audio.tags[tag_key]
                                if hasattr(tag_value, 'text'):
                                    tag_value_str = str(tag_value.text[0]) if tag_value.text else ''
                                else:
                                    tag_value_str = str(tag_value)
                                tags[TAG_MAPPINGS[tag_key]] = normalize_tag_value(tag_value_str)
                except Exception as e:
                    logger.debug("Alternative ID3 tag reading failed: %s", e)
        elif isinstance(audio, (FLAC, OggOpus, OggVorbis)):
            # FLAC and OGG files
            for tag_key, tag_values in audio.items():
                tag_key_lower = tag_key.lower()
                if tag_key_lower in TAG_MAPPINGS:
                    # Some tags might have multiple values, we'll take the first one
                    tag_value = tag_values[0] if tag_values else ''
                    tags[TAG_MAPPINGS[tag_key_lower]] = normalize_tag_value(tag_value)
        elif isinstance(audio, MP4):
            # MP4 files
            for tag_key, tag_value in audio.items():
                if tag_key in TAG_MAPPINGS:
                    if isinstance(tag_value, list):
                        if tag_key in ('trkn', 'disk'):
                            # Handle track and disc number tuples
                            if tag_value and isinstance(tag_value[0], tuple) and len(tag_value[0]) >= 1:
                                tags[TAG_MAPPINGS[tag_key]] = str(tag_value[0][0])
                        else:
                            tag_value_str = str(tag_value[0]) if tag_value else ''
                            tags[TAG_MAPPINGS[tag_key]] = normalize_tag_value(tag_value_str)
                    else:
                        tag_value_str = str(tag_value)
                        tags[TAG_MAPPINGS[tag_key]] = normalize_tag_value(tag_value_str)
        else:
            # Generic audio file - try to read any available tags
            for tag_key, tag_value in audio.items():
                tag_key_lower = tag_key.lower()
                if tag_key_lower in TAG_MAPPINGS:
                    if isinstance(tag_value, list):
                        tag_value_str = str(tag_value[0]) if tag_value else ''
                        tags[TAG_MAPPINGS[tag_key_lower]] = normalize_tag_value(tag_value_str)
                    else:
                        tag_value_str = str(tag_value)
                        tags[TAG_MAPPINGS[tag_key_lower]] = normalize_tag_value(tag_value_str)
                        
        logger.debug("Successfully read %d tags from file", len(tags))
        logger.debug("Tags: %s", str(tags))
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
    result = {}
    all_tag_names = set()
    for tags in all_tags:
        all_tag_names.update(tags.keys())
    
    for tag_name in all_tag_names:
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

def extract_artwork(file_path: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Extract artwork from an audio file.
    
    Args:
        file_path: Path to the audio file
        output_path: Path where to save the extracted artwork.
                     If None, a temporary file will be created.
    
    Returns:
        Path to the extracted artwork file, or None if no artwork was found
    """
    if not MUTAGEN_AVAILABLE:
        logger.debug("Mutagen not available - cannot extract artwork")
        return None
        
    if not os.path.exists(file_path):
        logger.error("File not found: %s", file_path)
        return None
    
    try:
        file_ext = os.path.splitext(file_path.lower())[1]
        artwork_data = None
        mime_type = None
        
        # Extract artwork based on file type
        if file_ext == '.mp3':
            audio = mutagen.File(file_path)
            
            # Try to get artwork from APIC frames
            if audio.tags:
                for frame in audio.tags.values():
                    if frame.FrameID == 'APIC':
                        artwork_data = frame.data
                        mime_type = frame.mime
                        break
                        
        elif file_ext == '.flac':
            audio = FLAC(file_path)
            
            # Get pictures from FLAC
            if audio.pictures:
                artwork_data = audio.pictures[0].data
                mime_type = audio.pictures[0].mime
                
        elif file_ext in ['.m4a', '.mp4', '.aac']:
            audio = MP4(file_path)
            
            # Check 'covr' atom
            if 'covr' in audio:
                artwork_data = audio['covr'][0]
                # Determine mime type based on data format
                if isinstance(artwork_data, mutagen.mp4.MP4Cover):
                    if artwork_data.format == mutagen.mp4.MP4Cover.FORMAT_JPEG:
                        mime_type = 'image/jpeg'
                    elif artwork_data.format == mutagen.mp4.MP4Cover.FORMAT_PNG:
                        mime_type = 'image/png'
                    else:
                        mime_type = 'image/jpeg'  # Default guess
                    
        elif file_ext == '.ogg':
            try:
                audio = OggVorbis(file_path)
            except:
                try:
                    audio = OggOpus(file_path)
                except:
                    logger.debug("Could not determine OGG type for %s", file_path)
                    return None
            
            # For OGG files, metadata pictures are more complex to extract
            if 'metadata_block_picture' in audio:
                picture_data = base64.b64decode(audio['metadata_block_picture'][0])
                flac_picture = Picture(data=picture_data)
                artwork_data = flac_picture.data
                mime_type = flac_picture.mime
                
        # If we found artwork data, save it to a file
        if artwork_data:
            # Determine file extension from mime type
            if mime_type == 'image/jpeg':
                ext = '.jpg'
            elif mime_type == 'image/png':
                ext = '.png'
            else:
                ext = '.jpg'  # Default to jpg
                
            # Create output path if not provided
            if not output_path:
                # Create a temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                output_path = temp_file.name
                temp_file.close()
            elif not os.path.splitext(output_path)[1]:
                # Add extension if not in the output path
                output_path += ext
                
            # Write artwork to file
            with open(output_path, 'wb') as f:
                f.write(artwork_data)
                
            logger.info("Extracted artwork saved to %s", output_path)
            return output_path
        else:
            logger.debug("No artwork found in file: %s", file_path)
            return None
            
    except Exception as e:
        logger.debug("Error extracting artwork: %s", e)
        return None

def find_cover_image(source_dir):
    """
    Find a cover image in the source directory.
    
    Args:
        source_dir: Path to the directory to search for cover images
        
    Returns:
        str: Path to the found cover image, or None if not found
    """
    if not os.path.isdir(source_dir):
        return None
        
    # Common cover image file names
    cover_names = ARTWORK_NAMES
    
    # Common image extensions
    image_extensions = ARTWORK_EXTENSIONS
    
    # Try different variations
    for name in cover_names:
        for ext in image_extensions:
            # Try exact name match
            cover_path = os.path.join(source_dir, name + ext)
            if os.path.exists(cover_path):
                logger.debug("Found cover image: %s", cover_path)
                return cover_path
                
            # Try case-insensitive match
            for file in os.listdir(source_dir):
                if file.lower() == (name + ext).lower():
                    cover_path = os.path.join(source_dir, file)
                    logger.debug("Found cover image: %s", cover_path)
                    return cover_path
    
    # If no exact matches, try finding any file containing the cover names
    for file in os.listdir(source_dir):
        file_lower = file.lower()
        file_ext = os.path.splitext(file_lower)[1]
        if file_ext in image_extensions:
            for name in cover_names:
                if name in file_lower:
                    cover_path = os.path.join(source_dir, file)
                    logger.debug("Found cover image: %s", cover_path)
                    return cover_path
    
    logger.debug("No cover image found in directory: %s", source_dir)
    return None