#!/usr/bin/python3
"""
Artwork handling functionality for TonieToolbox.
"""

import os
import tempfile
import shutil
from typing import List, Optional, Tuple

from .logger import get_logger
from .teddycloud import TeddyCloudClient
from .media_tags import extract_artwork, find_cover_image


def upload_artwork(client: TeddyCloudClient, taf_filename, source_path, audio_files) -> Tuple[bool, Optional[str]]:
    """
    Find and upload artwork for a Tonie file.
    
    Args:
        client: TeddyCloudClient instance to use for API communication
        taf_filename: The filename of the Tonie file (.taf)
        source_path: Source directory to look for artwork
        audio_files: List of audio files to extract artwork from if needed        
    Returns:
        tuple: (success, artwork_url) where success is a boolean and artwork_url is the URL of the uploaded artwork
    """
    logger = get_logger('artwork')
    logger.info("Looking for artwork for Tonie file: %s", taf_filename)
    taf_basename = os.path.basename(taf_filename)
    taf_name = os.path.splitext(taf_basename)[0]
    artwork_path = None
    temp_artwork = None
    artwork_path = find_cover_image(source_path)
    if not artwork_path and audio_files and len(audio_files) > 0:
        logger.info("No cover image found, trying to extract from audio files")
        temp_artwork = extract_artwork(audio_files[0])
        if temp_artwork:
            artwork_path = temp_artwork
            logger.info("Extracted artwork from audio file: %s", temp_artwork)
    
    if not artwork_path:
        logger.warning("No artwork found for %s", source_path)
        return False, None
        
    logger.info("Found artwork: %s", artwork_path)
    artwork_upload_path = "/custom_img"
    artwork_ext = os.path.splitext(artwork_path)[1]
    renamed_artwork_path = None
    upload_success = False
    artwork_url = None
    
    try:
        renamed_artwork_path = os.path.join(os.path.dirname(artwork_path), 
                                          f"{taf_name}{artwork_ext}")
        
        if renamed_artwork_path != artwork_path:
            shutil.copy(artwork_path, renamed_artwork_path)
            logger.debug("Created renamed artwork copy: %s", renamed_artwork_path)
        
        logger.info("Uploading artwork to path: %s as %s%s", 
                  artwork_upload_path, taf_name, artwork_ext)
        try:
            response = client.upload_file(
                file_path=renamed_artwork_path,                
                destination_path=artwork_upload_path,
                special="library"
            )
            upload_success = response.get('success', False)
                
            if not upload_success:
                logger.error("Failed to upload %s to TeddyCloud", renamed_artwork_path)
            else:
                logger.info("Successfully uploaded %s to TeddyCloud", renamed_artwork_path)
            logger.debug("Upload response: %s", response)
        except Exception as e:
            logger.error("Error uploading artwork: %s", e)
            upload_success = False
        
        if upload_success:
            if not artwork_upload_path.endswith('/'):
                artwork_upload_path += '/'                
            artwork_url = f"{artwork_upload_path}{taf_name}{artwork_ext}"
            logger.debug("Artwork URL: %s", artwork_url)
    
    except Exception as e:
        logger.error("Error during artwork handling: %s", e)
        upload_success = False
        
    finally:
        if renamed_artwork_path != artwork_path and renamed_artwork_path and os.path.exists(renamed_artwork_path):
            try:
                os.unlink(renamed_artwork_path)
                logger.debug("Removed temporary renamed artwork file: %s", renamed_artwork_path)
            except Exception as e:
                logger.debug("Failed to remove temporary renamed artwork file: %s", e)
        if temp_artwork and os.path.exists(temp_artwork):
            try:
                if temp_artwork.startswith(tempfile.gettempdir()):
                    os.unlink(temp_artwork)
                    logger.debug("Removed temporary extracted artwork file: %s", temp_artwork)
            except Exception as e:
                logger.debug("Failed to remove temporary artwork file: %s", e)
    
    return upload_success, artwork_url