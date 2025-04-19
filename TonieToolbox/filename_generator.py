"""
Module for generating intelligent output filenames for TonieToolbox.
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from .logger import get_logger

logger = get_logger('filename_generator')

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters and trimming.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        A sanitized filename
    """
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. \t')
    # Avoid empty filenames
    if not sanitized:
        return "tonie"
    return sanitized

def guess_output_filename(input_filename: str, input_files: List[str] = None) -> str:
    """
    Generate a sensible output filename based on input file or directory.
    
    Logic:
    1. For .lst files: Use the lst filename without extension
    2. For directories: Use the directory name
    3. For single files: Use the filename without extension
    4. For multiple files: Use the common parent directory name
    
    Args:
        input_filename: The input filename or pattern
        input_files: List of resolved input files (optional)
        
    Returns:
        Generated output filename without extension
    """
    logger.debug("Guessing output filename from input: %s", input_filename)
    
    # Handle .lst files
    if input_filename.lower().endswith('.lst'):
        base = os.path.basename(input_filename)
        name = os.path.splitext(base)[0]
        logger.debug("Using .lst file name: %s", name)
        return sanitize_filename(name)
    
    # Handle directory pattern
    if input_filename.endswith('/*') or input_filename.endswith('\\*'):
        dir_path = input_filename[:-2]  # Remove the /* or \* at the end
        dir_name = os.path.basename(os.path.normpath(dir_path))
        logger.debug("Using directory name: %s", dir_name)
        return sanitize_filename(dir_name)
    
    # Handle directory
    if os.path.isdir(input_filename):
        dir_name = os.path.basename(os.path.normpath(input_filename))
        logger.debug("Using directory name: %s", dir_name)
        return sanitize_filename(dir_name)
    
    # Handle single file
    if not input_files or len(input_files) == 1:
        file_path = input_files[0] if input_files else input_filename
        base = os.path.basename(file_path)
        name = os.path.splitext(base)[0]
        logger.debug("Using single file name: %s", name)
        return sanitize_filename(name)
    
    # Handle multiple files - try to find common parent directory
    try:
        # Find the common parent directory of all files
        common_path = os.path.commonpath([os.path.abspath(f) for f in input_files])
        dir_name = os.path.basename(common_path)
        
        # If the common path is root or very short, use parent of first file instead
        if len(dir_name) <= 1 or len(common_path) < 4:
            dir_name = os.path.basename(os.path.dirname(os.path.abspath(input_files[0])))
        
        logger.debug("Using common parent directory: %s", dir_name)
        return sanitize_filename(dir_name)
    except ValueError:
        # Files might be on different drives
        logger.debug("Could not determine common path, using generic name")
        return "tonie_collection"