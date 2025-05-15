#!/usr/bin/python3
"""
Module for generating intelligent output filenames for TonieToolbox.
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from .logger import get_logger

logger = get_logger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters and trimming.
    
    Args:
        filename (str): The filename to sanitize
    Returns:
        str: A sanitized filename
    """
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. \t')
    # Avoid empty filenames
    if not sanitized:
        return "tonie"
    return sanitized

def guess_output_filename(input_filename: str, input_files: list[str] = None) -> str:
    """
    Generate a sensible output filename based on input file or directory.
    
    Logic:
    1. For .lst files: Use the lst filename without extension
    2. For directories: Use the directory name
    3. For single files: Use the filename without extension
    4. For multiple files: Use the common parent directory name
    
    Args:
        input_filename (str): The input filename or pattern
        input_files (list[str] | None): List of resolved input files (optional)
    Returns:
        str: Generated output filename without extension
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

def apply_template_to_path(template, metadata):
    """
    Apply metadata to a path template and ensure the path is valid.
    
    Args:
        template: String template with {tag} placeholders
        metadata: Dictionary of tag values
        
    Returns:
        Formatted path with placeholders replaced by actual values
    """
    if not template or not metadata:
        return None
        
    try:
        # Replace any tags in the path with their values
        formatted_path = template
        for tag, value in metadata.items():
            if value:
                # Sanitize value for use in path
                safe_value = re.sub(r'[<>:"|?*]', '_', str(value))
                # Replace forward slashes with appropriate character, but NOT hyphens
                safe_value = safe_value.replace('/', ' - ')
                # Remove leading/trailing whitespace and dots
                safe_value = safe_value.strip('. \t')
                if not safe_value:
                    safe_value = "unknown"

                placeholder = '{' + tag + '}'
                formatted_path = formatted_path.replace(placeholder, safe_value)
        
        # Check if there are any remaining placeholders
        if re.search(r'{[^}]+}', formatted_path):
            return None  # Some placeholders couldn't be filled
            
        # Normalize path separators for the OS
        formatted_path = os.path.normpath(formatted_path)
        return formatted_path
    except Exception as e:
        logger.error(f"Error applying template to path: {e}")
        return None

def ensure_directory_exists(file_path):
    """Create the directory structure for a given file path if it doesn't exist."""
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)