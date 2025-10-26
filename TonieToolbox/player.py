#!/usr/bin/env python3
"""
TAF Player Module for TonieToolbox

This module provides a simple audio player for TAF (Tonie Audio Format) files.
It uses the existing TAF parsing functionality and FFmpeg for cross-platform audio playback.
"""

import os
import sys
import time
import tempfile
import threading
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path

from .logger import get_logger
from .tonie_analysis import get_header_info_cli, get_audio_info
from .dependency_manager import ensure_dependency, get_ffplay_binary
from .constants import SAMPLE_RATE_KHZ


logger = get_logger(__name__)


class TAFPlayerError(Exception):
    """Custom exception for TAF player errors."""
    pass


class TAFPlayer:
    """
    A simple TAF file player using FFmpeg for audio playback.
    
    This player can load TAF files, extract audio data, and play it using FFmpeg.
    It supports basic playback controls like play, pause, resume, stop, and seek.
    """
    
    def __init__(self):
        """Initialize the TAF player."""
        self.taf_file: Optional[Path] = None
        self.taf_info: Optional[Dict[str, Any]] = None
        self.temp_audio_file: Optional[Path] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.current_position: float = 0.0
        self.total_duration: float = 0.0
        self.playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.header_size: int = 0  # Dynamic header size from TAF parsing
        
        # Ensure FFmpeg is available
        try:
            ensure_dependency('ffmpeg')
        except Exception as e:
            raise TAFPlayerError(f"Failed to ensure FFmpeg availability: {e}")
    
    def load(self, taf_file_path: str) -> None:
        """
        Load a TAF file for playback.
        
        Args:
            taf_file_path: Path to the TAF file to load
            
        Raises:
            TAFPlayerError: If the file cannot be loaded or parsed
        """
        taf_path = Path(taf_file_path)
        
        if not taf_path.exists():
            raise TAFPlayerError(f"TAF file not found: {taf_file_path}")
        
        if not taf_path.suffix.lower() == '.taf':
            raise TAFPlayerError(f"File is not a TAF file: {taf_file_path}")
        
        logger.info(f"Loading TAF file: {taf_path}")
        
        try:
            # Parse TAF file header and get info
            with open(taf_path, 'rb') as taf_file:
                # Get header information using the CLI version for better error handling
                header_size, tonie_header, file_size, audio_size, sha1sum, \
                opus_head_found, opus_version, channel_count, sample_rate, \
                bitstream_serial_no, opus_comments, valid = get_header_info_cli(taf_file)
                
                if not valid:
                    raise TAFPlayerError("Invalid or corrupted TAF file")
                
                # Get audio information including total duration
                page_count, alignment_okay, page_size_okay, total_time, \
                chapter_times = get_audio_info(taf_file, sample_rate, tonie_header, header_size)
                
                # Store header size for audio extraction
                self.header_size = 4 + header_size  # 4 bytes for header size + actual header
                
                # Build structured information dictionary
                self.taf_info = {
                    'file_size': file_size,
                    'audio_size': audio_size,
                    'sha1_hash': sha1sum.hexdigest() if sha1sum else None,
                    'sample_rate': sample_rate,
                    'channels': channel_count,
                    'bitstream_serial': bitstream_serial_no,
                    'opus_version': opus_version,
                    'page_count': page_count,
                    'total_time': total_time,
                    'opus_comments': opus_comments,
                    'chapters': []
                }
                
                # Process chapter information
                if hasattr(tonie_header, 'chapterPages') and len(tonie_header.chapterPages) > 0:
                    chapter_granules = [0]  # Start with position 0
                    
                    # Find granule positions for each chapter page
                    for chapter_page in tonie_header.chapterPages:
                        # For now, we'll estimate chapter positions
                        # A more accurate implementation would need to parse OGG pages
                        pass                    # Create chapter list with times
                    chapter_start_time = 0.0
                    for i, chapter_time in enumerate(chapter_times):
                        # Parse the formatted time string back to seconds
                        duration_seconds = self._parse_time_string(chapter_time)
                        
                        # Store the current chapter with correct start position
                        self.taf_info['chapters'].append({
                            'index': i + 1,
                            'title': f'Chapter {i + 1}',
                            'duration': duration_seconds,  # Store as float seconds
                            'start': chapter_start_time  # Position from start of the file
                        })
                        
                        # Update start time for the next chapter
                        chapter_start_time += duration_seconds
                
                # Extract bitrate from opus comments if available
                if opus_comments and 'ENCODER_OPTIONS' in opus_comments:
                    import re
                    match = re.search(r'bitrate=(\d+)', opus_comments['ENCODER_OPTIONS'])
                    if match:
                        self.taf_info['bitrate'] = int(match.group(1))
                self.taf_file = taf_path
                self.total_duration = total_time
                
            logger.info(f"Successfully loaded TAF file: {taf_path.name}")
            self._print_file_info()
            
        except Exception as e:
            raise TAFPlayerError(f"Failed to parse TAF file: {e}")
    
    def _print_file_info(self) -> None:
        """Print information about the loaded TAF file."""
        if not self.taf_info:
            return
        
        print("\n" + "="*50)
        print("TAF FILE INFORMATION")
        print("="*50)
        
        # Basic file info
        if 'audio_id' in self.taf_info:
            print(f"Audio ID: {self.taf_info['audio_id']}")
        
        if 'sha1_hash' in self.taf_info:
            print(f"SHA1 Hash: {self.taf_info['sha1_hash']}")
        
        # Audio properties
        if 'sample_rate' in self.taf_info:
            print(f"Sample Rate: {self.taf_info['sample_rate']} Hz")
        
        if 'channels' in self.taf_info:
            print(f"Channels: {self.taf_info['channels']}")
        
        if 'bitrate' in self.taf_info:
            print(f"Bitrate: {self.taf_info['bitrate']} kbps")
        
        if self.total_duration > 0:
            print(f"Duration: {self._format_time(self.total_duration)}")
        
        # Chapter information
        if 'chapters' in self.taf_info and self.taf_info['chapters']:
            print(f"\nChapters: {len(self.taf_info['chapters'])}")
            for i, chapter in enumerate(self.taf_info['chapters'][:5]):  # Show first 5 chapters
                start_time = self._format_time(chapter.get('start', 0))
                title = chapter.get('title', f'Chapter {i+1}')
                print(f"  {i+1:2d}. {title} ({start_time})")
            
            if len(self.taf_info['chapters']) > 5:
                print(f"  ... and {len(self.taf_info['chapters']) - 5} more chapters")
        
        print("="*50 + "\n")
    
    def _extract_audio_data(self) -> Path:
        """
        Extract audio data from TAF file to a temporary file for playback.
        
        Returns:
            Path to the temporary audio file
            
        Raises:
            TAFPlayerError: If audio extraction fails
        """
        if not self.taf_file:
            raise TAFPlayerError("No TAF file loaded")
        
        try:
            # Create temporary file for extracted audio
            temp_fd, temp_path = tempfile.mkstemp(suffix='.ogg', prefix='taf_player_')
            os.close(temp_fd)
            temp_file = Path(temp_path)
            logger.debug(f"Extracting audio data to: {temp_file}")
            
            # Read TAF file and extract audio data
            with open(self.taf_file, 'rb') as taf:
                # Skip TAF header (use dynamic header size from parsing)
                taf.seek(self.header_size)
                
                # Read remaining data (OGG audio)
                audio_data = taf.read()
                
                # Write to temporary file
                with open(temp_file, 'wb') as temp:
                    temp.write(audio_data)
            
            logger.debug("Audio data extraction completed")
            return temp_file
            
        except Exception as e:
            if 'temp_file' in locals():
                temp_file.unlink(missing_ok=True)
            raise TAFPlayerError(f"Failed to extract audio data: {e}")
    
    def play(self, start_time: float = 0.0) -> None:
        """
        Start playback of the loaded TAF file.
        
        Args:
            start_time: Time in seconds to start playback from
            
        Raises:
            TAFPlayerError: If playback cannot be started
        """
        if not self.taf_file:
            raise TAFPlayerError("No TAF file loaded")
        
        if self.is_playing:
            logger.warning("Playback already in progress")
            return
        
        try:
            # Extract audio data if not already done
            if not self.temp_audio_file or not self.temp_audio_file.exists():
                self.temp_audio_file = self._extract_audio_data()
            
            self.current_position = start_time
            self._stop_event.clear()
            
            # Start playback in a separate thread
            self.playback_thread = threading.Thread(
                target=self._playback_worker,
                args=(start_time,),
                daemon=True
            )
            self.playback_thread.start()
            self.is_playing = True
            self.is_paused = False
            
            logger.info(f"Started playback of: {self.taf_file.name}")
            if start_time > 0:
                logger.info(f"Starting from: {self._format_time(start_time)}")
            
        except Exception as e:
            raise TAFPlayerError(f"Failed to start playback: {e}")    
    def _playback_worker(self, start_time: float = 0.0) -> None:
        """Worker thread for handling FFplay audio playback."""
        try:
            # Get FFplay binary path
            ffplay_path = get_ffplay_binary(auto_download=True)
            if not ffplay_path:
                raise TAFPlayerError("FFplay not found and could not be downloaded")
            
            logger.debug(f"Using FFplay at: {ffplay_path}")
            
            # Verify temp audio file exists
            if not self.temp_audio_file or not self.temp_audio_file.exists():
                raise TAFPlayerError("No audio data available for playback")
            
            # Build FFplay command
            ffplay_cmd = [
                ffplay_path,
                str(self.temp_audio_file),
                '-nodisp',  # No video display window
                '-autoexit',  # Exit when playback finishes
                '-loglevel', 'warning'  # Reduce output noise
            ]
            
            # Add start time if specified
            if start_time > 0:
                ffplay_cmd.extend(['-ss', str(start_time)])
            
            logger.debug(f"FFplay command: {' '.join(ffplay_cmd)}")
            
            # Start FFplay process
            self.ffmpeg_process = subprocess.Popen(
                ffplay_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # Wait for process completion or stop signal
            while self.ffmpeg_process.poll() is None:
                if self._stop_event.wait(0.1):
                    break
                
                # Update current position (rough estimate)
                if not self.is_paused:
                    self.current_position += 0.1
            
            # Clean up process
            if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            
        except Exception as e:
            logger.error(f"Playback error: {e}")
        finally:
            self.is_playing = False
            self.is_paused = False
            self.ffmpeg_process = None
    def pause(self) -> None:
        """Pause playback."""
        if not self.is_playing:
            logger.warning("No playback in progress")
            return
        
        if self.is_paused:
            logger.warning("Playback already paused")
            return
        
        if self.ffmpeg_process:
            try:
                # Send SIGSTOP to pause (Unix) or terminate and remember position (Windows)
                if hasattr(self.ffmpeg_process, 'suspend'):
                    self.ffmpeg_process.suspend()
                    self.is_paused = True
                    logger.info("Playback paused")
                else:
                    # For Windows, we'll need to stop and restart
                    # Save current position before stopping
                    pause_position = self.current_position
                    self._stop_playback_process()
                    # Restore the position and set paused state
                    self.current_position = pause_position
                    self.is_playing = False
                    self.is_paused = True
                    logger.info("Playback paused")
                
            except Exception as e:
                logger.error(f"Failed to pause playback: {e}")
    def resume(self) -> None:
        """Resume paused playback."""
        if not self.is_paused:
            logger.warning("Playback is not paused")
            return
        
        try:
            if self.ffmpeg_process and hasattr(self.ffmpeg_process, 'resume'):
                # Unix-like systems with process suspension support
                self.ffmpeg_process.resume()
                self.is_paused = False
                logger.info("Playback resumed")
            else:
                # Windows or systems without suspension - restart from saved position
                resume_position = self.current_position
                self.is_paused = False
                self.play(resume_position)
                return
            
        except Exception as e:
            logger.error(f"Failed to resume playback: {e}")
    
    def _stop_playback_process(self) -> None:
        """Stop the playback process without resetting position or state."""
        # Signal stop to playback thread
        self._stop_event.set()
        
        # Terminate FFmpeg process
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
            except Exception as e:
                logger.error(f"Error stopping FFmpeg process: {e}")
        
        # Wait for playback thread to finish
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=5)
        
        self.ffmpeg_process = None

    def stop(self) -> None:
        """Stop playback."""
        if not self.is_playing:
            return
        
        logger.info("Stopping playback")
        
        self._stop_playback_process()
        
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0.0
        
        logger.info("Playback stopped")
    
    def seek(self, position: float) -> None:
        """
        Seek to a specific position in the audio.
        
        Args:
            position: Time in seconds to seek to
        """
        if position < 0:
            position = 0.0
        elif self.total_duration > 0 and position > self.total_duration:
            position = self.total_duration
        
        was_playing = self.is_playing
        
        if was_playing:
            self.stop()
        
        self.current_position = position
        
        if was_playing:
            self.play(position)
        
        logger.info(f"Seeked to: {self._format_time(position)}")
    def get_status(self) -> Dict[str, Any]:
        """
        Get current player status.
        
        Returns:
            Dictionary containing player status information
        """
        return {
            'file_loaded': self.taf_file is not None,
            'file_path': str(self.taf_file) if self.taf_file else None,
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_position': self.current_position,
            'total_duration': self.total_duration,
            'progress_percent': (self.current_position / self.total_duration * 100) if self.total_duration > 0 else 0.0
        }
    
    def cleanup(self) -> None:
        """Clean up resources used by the player."""
        self.stop()
        
        # Remove temporary audio file
        if self.temp_audio_file and self.temp_audio_file.exists():
            try:
                self.temp_audio_file.unlink()
                logger.debug("Cleaned up temporary audio file")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to MM:SS or HH:MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _parse_time_string(self, time_str: str) -> float:
        """
        Parse a time string (HH:MM:SS.FF or MM:SS) back to seconds.
        
        Args:
            time_str: Formatted time string
            
        Returns:
            Time in seconds as float
        """
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                # HH:MM:SS or HH:MM:SS.FF format
                hours = int(parts[0])
                minutes = int(parts[1])
                # Handle potential fractional seconds
                seconds_part = parts[2]
                if '.' in seconds_part:
                    seconds = float(seconds_part)
                else:
                    seconds = int(seconds_part)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                # MM:SS format
                minutes = int(parts[0])
                seconds_part = parts[1]
                if '.' in seconds_part:
                    seconds = float(seconds_part)
                else:
                    seconds = int(seconds_part)
                return minutes * 60 + seconds
            else:
                # Single number, assume seconds
                return float(time_str)
        except (ValueError, IndexError):
            logger.warning(f"Could not parse time string: {time_str}")
            return 0.0
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()


def interactive_player(taf_file_path: str) -> None:
    """
    Start an interactive TAF player session.
    
    Args:
        taf_file_path: Path to the TAF file to play
    """
    print("TonieToolbox TAF Player")
    print("======================")
    
    try:
        with TAFPlayer() as player:
            player.load(taf_file_path)
            
            print("\nControls:")
            print("  [p]lay    - Play/pause toggle")
            print("  [s]top    - Stop playback")
            print("  [q]uit    - Quit player")
            print("  [i]nfo    - Show file information")
            print("  seek <MM:SS> - Seek to specific time")
            print("  status    - Show current status")
            print("\nType a command and press Enter:")
            
            while True:
                try:
                    command = input("> ").strip().lower()
                    
                    if command in ['q', 'quit', 'exit']:
                        break
                    elif command in ['p', 'play']:
                        if player.is_playing and not player.is_paused:
                            # Currently playing, so pause
                            player.pause()
                        elif player.is_paused:
                            # Currently paused, so resume
                            player.resume()
                        else:
                            # Not playing, so start
                            player.play()
                    elif command in ['s', 'stop']:
                        player.stop()
                    elif command in ['i', 'info']:
                        player._print_file_info()
                    elif command == 'status':
                        status = player.get_status()
                        print(f"Status: {'Playing' if status['is_playing'] else 'Stopped'}")
                        if status['is_paused']:
                            print("        (Paused)")
                        print(f"Position: {player._format_time(status['current_position'])}")
                        if status['total_duration'] > 0:
                            print(f"Duration: {player._format_time(status['total_duration'])}")
                            print(f"Progress: {status['progress_percent']:.1f}%")
                    elif command.startswith('seek '):
                        try:
                            time_str = command[5:].strip()
                            if ':' in time_str:
                                parts = time_str.split(':')
                                if len(parts) == 2:
                                    minutes, seconds = map(int, parts)
                                    seek_time = minutes * 60 + seconds
                                elif len(parts) == 3:
                                    hours, minutes, seconds = map(int, parts)
                                    seek_time = hours * 3600 + minutes * 60 + seconds
                                else:
                                    raise ValueError("Invalid time format")
                            else:
                                seek_time = float(time_str)
                            
                            player.seek(seek_time)
                        except ValueError:
                            print("Invalid time format. Use MM:SS or HH:MM:SS or seconds")
                    elif command == '':
                        continue
                    else:
                        print("Unknown command. Type 'q' to quit.")
                
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Command error: {e}")
            
            print("\nGoodbye!")
            
    except TAFPlayerError as e:
        logger.error(f"Player error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m TonieToolbox.player <taf_file>")
        sys.exit(1)
    
    interactive_player(sys.argv[1])