#!/usr/bin/python3
"""
Recursive folder processing functionality for the TonieToolbox package
"""

import os
import glob
from typing import List, Dict, Tuple, Set
import logging
import re

from .audio_conversion import filter_directories
from .logger import get_logger

logger = get_logger(__name__)


def find_audio_folders(root_path: str) -> list[dict[str, any]]:
    """
    Find and return all folders that contain audio files in a recursive manner,
    organized in a way that handles nested folder structures.
    
    Args:
        root_path (str): Root directory to start searching from
        
    Returns:
        list[dict[str, any]]: List of dictionaries with folder information, including paths and relationships
    """
    logger.info("Finding folders with audio files in: %s", root_path)
    
    # Dictionary to store folder information
    # Key: folder path, Value: {audio_files, parent, children, depth}
    folders_info = {}
    abs_root = os.path.abspath(root_path)
    
    # First pass: Identify all folders containing audio files and calculate their depth
    for dirpath, dirnames, filenames in os.walk(abs_root):
        # Look for audio files in this directory
        all_files = [os.path.join(dirpath, f) for f in filenames]
        audio_files = filter_directories(all_files)
        
        if audio_files:
            # Calculate folder depth relative to root
            rel_path = os.path.relpath(dirpath, abs_root)
            depth = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
            
            # Store folder info
            folders_info[dirpath] = {
                'path': dirpath,
                'audio_files': audio_files,
                'parent': os.path.dirname(dirpath),
                'children': [],
                'depth': depth,
                'file_count': len(audio_files)
            }
            logger.debug("Found folder with %d audio files: %s (depth %d)", 
                        len(audio_files), dirpath, depth)
    
    # Second pass: Build parent-child relationships
    for folder_path, info in folders_info.items():
        parent_path = info['parent']
        if parent_path in folders_info:
            folders_info[parent_path]['children'].append(folder_path)
    
    # Convert to list and sort by path for consistent processing
    folder_list = sorted(folders_info.values(), key=lambda x: x['path'])
    logger.info("Found %d folders containing audio files", len(folder_list))
    
    return folder_list


def determine_processing_folders(folders: list[dict[str, any]]) -> list[dict[str, any]]:
    """
    Determine which folders should be processed based on their position in the hierarchy.
    
    Args:
        folders (list[dict[str, any]]): List of folder dictionaries with hierarchy information
        
    Returns:
        list[dict[str, any]]: List of folders that should be processed (filtered)
    """
    # We'll use a set to track which folders we've decided to process
    to_process = set()
    
    # Let's examine folders with the deepest nesting level first
    max_depth = max(folder['depth'] for folder in folders) if folders else 0
    
    # First, mark terminal folders (leaf nodes) for processing
    for folder in folders:
        if not folder['children']:  # No children means it's a leaf node
            to_process.add(folder['path'])
            logger.debug("Marking leaf folder for processing: %s", folder['path'])
    
    # Check if any parent folders should be processed
    # If a parent folder has significantly more audio files than the sum of its children,
    # or some children aren't marked for processing, we should process the parent too
    all_folders_by_path = {folder['path']: folder for folder in folders}
    
    # Work from bottom up (max depth to min)
    for depth in range(max_depth, -1, -1):
        for folder in [f for f in folders if f['depth'] == depth]:
            if folder['path'] in to_process:
                continue
                
            # Count audio files in children that will be processed
            child_file_count = sum(all_folders_by_path[child]['file_count'] 
                                  for child in folder['children'] 
                                  if child in to_process)
            
            # If this folder has more files than what will be processed in children,
            # or not all children will be processed, then process this folder too
            if folder['file_count'] > child_file_count or any(child not in to_process for child in folder['children']):
                to_process.add(folder['path'])
                logger.debug("Marking parent folder for processing: %s (files: %d, child files: %d)", 
                           folder['path'], folder['file_count'], child_file_count)
    
    # Return only folders that should be processed
    result = [folder for folder in folders if folder['path'] in to_process]
    logger.info("Determined %d folders should be processed (out of %d total folders with audio)", 
              len(result), len(folders))
    return result


def get_folder_audio_files(folder_path: str) -> list[str]:
    """
    Get all audio files in a specific folder.
    
    Args:
        folder_path (str): Path to folder
        
    Returns:
        list[str]: List of paths to audio files in natural sort order
    """
    audio_files = glob.glob(os.path.join(folder_path, "*"))
    filtered_files = filter_directories(audio_files)
    
    # Sort files naturally (so that '2' comes before '10')
    sorted_files = natural_sort(filtered_files)
    logger.debug("Found %d audio files in folder: %s", len(sorted_files), folder_path)
    
    return sorted_files


def natural_sort(file_list: list[str]) -> list[str]:
    """
    Sort a list of files in natural order (so that 2 comes before 10).
    
    Args:
        file_list (list[str]): List of file paths
        
    Returns:
        list[str]: Naturally sorted list of file paths
    """
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    
    def alphanum_key(key):
        return [convert(c) for c in re.split('([0-9]+)', key)]
    
    return sorted(file_list, key=alphanum_key)


def extract_folder_meta(folder_path: str) -> dict[str, str]:
    """
    Extract metadata from folder name.
    Common format might be: "YYYY - NNN - Title"
    
    Args:
        folder_path (str): Path to folder
        
    Returns:
        dict[str, str]: Dictionary with extracted metadata (year, number, title)
    """
    folder_name = os.path.basename(folder_path)
    logger.debug("Extracting metadata from folder: %s", folder_name)
    
    # Try to match the format "YYYY - NNN - Title"
    match = re.match(r'(\d{4})\s*-\s*(\d+)\s*-\s*(.+)', folder_name)
    
    meta = {
        'year': '',
        'number': '',
        'title': folder_name  # Default to the folder name if parsing fails
    }
    
    if match:
        year, number, title = match.groups()
        meta['year'] = year
        meta['number'] = number
        meta['title'] = title.strip()
        logger.debug("Extracted metadata: year=%s, number=%s, title=%s", 
                    meta['year'], meta['number'], meta['title'])
    else:
        # Try to match just the number format "NNN - Title"
        match = re.match(r'(\d+)\s*-\s*(.+)', folder_name)
        if match:
            number, title = match.groups()
            meta['number'] = number
            meta['title'] = title.strip()
            logger.debug("Extracted metadata: number=%s, title=%s", 
                        meta['number'], meta['title'])
        else:
            logger.debug("Could not extract structured metadata from folder name")
    
    return meta


def get_folder_name_from_metadata(folder_path: str, use_media_tags: bool = False, template: str = None) -> str:
    """
    Generate a suitable output filename for a folder based on folder name
    and optionally audio file metadata.
    
    Args:
        folder_path (str): Path to folder
        use_media_tags (bool): Whether to use media tags from audio files if available
        template (str | None): Optional template for formatting output name using media tags
        
    Returns:
        str: String with cleaned output name
    """
    folder_meta = extract_folder_meta(folder_path)
    output_name = None    
    if use_media_tags:
        try:
            from .media_tags import extract_album_info, format_metadata_filename, is_available, normalize_tag_value
            
            if is_available():
                logger.debug("Using media tags to generate folder name for: %s", folder_path)
                
                # Get album metadata from the files
                album_info = extract_album_info(folder_path)
                
                if album_info:
                    # Normalize all tag values to handle special characters
                    for key, value in album_info.items():
                        album_info[key] = normalize_tag_value(value)
                    
                    # Add folder metadata as fallback values
                    if 'number' in folder_meta and folder_meta['number']:
                        if 'tracknumber' not in album_info or not album_info['tracknumber']:
                            album_info['tracknumber'] = folder_meta['number']
                    
                    if 'title' in folder_meta and folder_meta['title']:
                        if 'album' not in album_info or not album_info['album']:
                            album_info['album'] = normalize_tag_value(folder_meta['title'])
                    
                    if template:
                        format_template = template
                        logger.debug("Using provided name template: %s", format_template)
                    else:                    
                        format_template = "{album}"
                        if 'artist' in album_info and album_info['artist']:
                            format_template = format_template + " - {artist}"
                        if 'number' in folder_meta and folder_meta['number']:
                            format_template = "{tracknumber} - " + format_template
                    
                    formatted_name = format_metadata_filename(album_info, format_template)
                    
                    if formatted_name:
                        logger.debug("Generated name from media tags: %s", formatted_name)
                        output_name = formatted_name
        except Exception as e:
            logger.warning("Error using media tags for folder naming: %s", str(e))
    
    # Fall back to folder name parsing if no media tags or if media tag extraction failed
    if not output_name:
        if folder_meta['number'] and folder_meta['title']:
            # Apply normalization to the title from the folder name
            try:
                from .media_tags import normalize_tag_value
                normalized_title = normalize_tag_value(folder_meta['title'])
                output_name = f"{folder_meta['number']} - {normalized_title}"
            except:
                output_name = f"{folder_meta['number']} - {folder_meta['title']}"
        else:
            # Try to normalize the folder name itself
            folder_name = os.path.basename(folder_path)
            try:
                from .media_tags import normalize_tag_value
                output_name = normalize_tag_value(folder_name)
            except:
                output_name = folder_name
    
    # Clean up the output name (remove invalid filename characters)
    output_name = re.sub(r'[<>:"/\\|?*]', '_', output_name)
    output_name = output_name.replace("???", "Fragezeichen")
    output_name = output_name.replace("!!!", "Ausrufezeichen")
    
    logger.debug("Final generated output name: %s", output_name)
    return output_name


def process_recursive_folders(root_path: str, use_media_tags: bool = False, name_template: str = None) -> list[tuple[str, str, list[str]]]:
    """
    Process folders recursively for audio files to create Tonie files.
    
    Args:
        root_path (str): The root path to start processing from
        use_media_tags (bool): Whether to use media tags for naming
        name_template (str | None): Template for naming files using media tags
    
    Returns:
        list[tuple[str, str, list[str]]]: A list of tuples (output_name, folder_path, audio_files)
    """
    logger = get_logger("recursive_processor")
    logger.info("Processing folders recursively: %s", root_path)
    # Make sure the path exists
    if not os.path.exists(root_path):
        logger.error("Path does not exist: %s", root_path)
        return []
    
    logger.info("Finding folders with audio files in: %s", root_path)
    
    # Get folder info with hierarchy details
    all_folders = find_audio_folders(root_path)
    
    # Determine which folders should be processed
    folders_to_process = determine_processing_folders(all_folders)
    
    results = []
    for folder_info in folders_to_process:
        folder_path = folder_info['path']
        audio_files = folder_info['audio_files']
        
        # Use natural sort order to ensure consistent results
        audio_files = natural_sort(audio_files)
        
        if audio_files:
            # Generate output filename using metadata
            output_name = get_folder_name_from_metadata(
                folder_path, 
                use_media_tags=use_media_tags, 
                template=name_template
            )
            
            results.append((output_name, folder_path, audio_files))
            logger.debug("Created processing task: %s -> %s (%d files)", 
                        folder_path, output_name, len(audio_files))
    
    logger.info("Created %d processing tasks", len(results))
    return results