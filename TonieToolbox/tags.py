#!/usr/bin/python3
"""
TonieToolbox - Tags handling functionality.
This module provides functionality to retrieve and display tags from a TeddyCloud instance.
"""
from .logger import get_logger
from .teddycloud import TeddyCloudClient
import json
from typing import Optional, Union

logger = get_logger(__name__)

def get_tags(client: 'TeddyCloudClient') -> bool:
    """
    Get and display tags from a TeddyCloud instance.
    
    Args:
        client (TeddyCloudClient): TeddyCloudClient instance to use for API communication
    Returns:
        bool: True if tags were retrieved successfully, False otherwise
    """
    logger.info("Getting tags from TeddyCloud using provided client")
    
    response = client.get_tag_index()
    
    if not response:
        logger.error("Failed to retrieve tags from TeddyCloud")
        return False
    if isinstance(response, dict) and 'tags' in response:
        tags = response['tags']
        logger.info("Successfully retrieved %d tags from TeddyCloud", len(tags))
        
        print("\nAvailable Tags from TeddyCloud:")
        print("-" * 60)
        
        sorted_tags = sorted(tags, key=lambda x: (x.get('type', ''), x.get('uid', '')))
        
        for tag in sorted_tags:
            uid = tag.get('uid', 'Unknown UID')
            tag_type = tag.get('type', 'Unknown')
            valid = "✓" if tag.get('valid', False) else "✗"
            series = tag.get('tonieInfo', {}).get('series', '')
            episode = tag.get('tonieInfo', {}).get('episode', '')
            source = tag.get('source', '')
            print(f"UID: {uid} ({tag_type}) - Valid: {valid}")
            if series:
                print(f"Series: {series}")
            if episode:
                print(f"Episode: {episode}")
            if source:
                print(f"Source: {source}")
            tracks = tag.get('tonieInfo', {}).get('tracks', [])
            if tracks:
                print("Tracks:")
                for i, track in enumerate(tracks, 1):
                    print(f"  {i}. {track}")
            track_seconds = tag.get('trackSeconds', [])
            if track_seconds and len(track_seconds) > 1:
                total_seconds = track_seconds[-1]
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                print(f"Duration: {minutes}:{seconds:02d} ({len(track_seconds)-1} tracks)")
            
            print("-" * 60)
    else:
        logger.info("Successfully retrieved tag data from TeddyCloud")
        print("\nTag data from TeddyCloud:")
        print("-" * 60)        
        print(json.dumps(response, indent=2))
        
        print("-" * 60)
    
    return True