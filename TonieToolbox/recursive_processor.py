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

logger = get_logger('recursive_processor')


def find_audio_folders(root_path: str) -> List[Dict[str, any]]:
    """
    Find and return all folders that contain audio files in a recursive manner,
    organized in a way that handles nested folder structures.
    
    Args:
        root_path: Root directory to start searching from
        
    Returns:
        List of dictionaries with folder information, including paths and relationships
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


def determine_processing_folders(folders: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Determine which folders should be processed based on their position in the hierarchy.
    
    Args:
        folders: List of folder dictionaries with hierarchy information
        
    Returns:
        List of folders that should be processed (filtered)
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


def get_folder_audio_files(folder_path: str) -> List[str]:
    """
    Get all audio files in a specific folder.
    
    Args:
        folder_path: Path to folder
        
    Returns:
        List of paths to audio files in natural sort order
    """
    audio_files = glob.glob(os.path.join(folder_path, "*"))
    filtered_files = filter_directories(audio_files)
    
    # Sort files naturally (so that '2' comes before '10')
    sorted_files = natural_sort(filtered_files)
    logger.debug("Found %d audio files in folder: %s", len(sorted_files), folder_path)
    
    return sorted_files


def natural_sort(file_list: List[str]) -> List[str]:
    """
    Sort a list of files in natural order (so that 2 comes before 10).
    
    Args:
        file_list: List of file paths
        
    Returns:
        Naturally sorted list of file paths
    """
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    
    def alphanum_key(key):
        return [convert(c) for c in re.split('([0-9]+)', key)]
    
    return sorted(file_list, key=alphanum_key)


def extract_folder_meta(folder_path: str) -> Dict[str, str]:
    """
    Extract metadata from folder name.
    Common format might be: "YYYY - NNN - Title"
    
    Args:
        folder_path: Path to folder
        
    Returns:
        Dictionary with extracted metadata (year, number, title)
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


def process_recursive_folders(root_path: str) -> List[Tuple[str, str, List[str]]]:
    """
    Process folders recursively and prepare data for conversion.
    
    Args:
        root_path: Root directory to start processing from
        
    Returns:
        List of tuples: (output_filename, folder_path, list_of_audio_files)
    """
    logger.info("Processing folders recursively: %s", root_path)
    
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
        
        meta = extract_folder_meta(folder_path)
        
        if audio_files:
            # Create output filename from metadata
            if meta['number'] and meta['title']:
                output_name = f"{meta['number']} - {meta['title']}"
            else:
                output_name = os.path.basename(folder_path)
                
            # Clean up the output name (remove invalid filename characters)
            output_name = re.sub(r'[<>:"/\\|?*]', '_', output_name)
            
            results.append((output_name, folder_path, audio_files))
            logger.debug("Created processing task: %s -> %s (%d files)", 
                        folder_path, output_name, len(audio_files))
    
    logger.info("Created %d processing tasks", len(results))
    return results