#!/usr/bin/python3
"""
Audio conversion functionality for the TonieToolbox package
"""

import os
import glob
import subprocess
import tempfile
from .dependency_manager import get_ffmpeg_binary, get_opus_binary
from .constants import SUPPORTED_EXTENSIONS
from .logger import get_logger

logger = get_logger(__name__)


def get_opus_tempfile(
    ffmpeg_binary: str = None,
    opus_binary: str = None,
    filename: str = None,
    bitrate: int = 48,
    vbr: bool = True,
    keep_temp: bool = False,
    auto_download: bool = False,
    no_mono_conversion: bool = False
) -> tuple[tempfile.SpooledTemporaryFile | None, str | None]:
    """
    Convert an audio file to Opus format and return a temporary file handle.
    
    Args:
        ffmpeg_binary (str | None): Path to the ffmpeg binary. If None, will be auto-detected or downloaded.
        opus_binary (str | None): Path to the opusenc binary. If None, will be auto-detected or downloaded.
        filename (str | None): Path to the input audio file
        bitrate (int): Bitrate for the Opus encoding in kbps
        vbr (bool): Whether to use variable bitrate encoding
        keep_temp (bool): Whether to keep the temporary files for testing
        auto_download (bool): Whether to automatically download dependencies if not found
        no_mono_conversion (bool): Whether to skip mono to stereo conversion
    Returns:
        tuple[tempfile.SpooledTemporaryFile | None, str | None]: (file handle, temp_file_path) or (file handle, None) if keep_temp is False
    """
    logger.trace("Entering get_opus_tempfile(ffmpeg_binary=%s, opus_binary=%s, filename=%s, bitrate=%d, vbr=%s, keep_temp=%s, auto_download=%s, no_mono_conversion=%s)",
                ffmpeg_binary, opus_binary, filename, bitrate, vbr, keep_temp, auto_download, no_mono_conversion)
    
    logger.debug("Converting %s to Opus format (bitrate: %d kbps, vbr: %s)", filename, bitrate, vbr)
    
    if ffmpeg_binary is None:
        logger.debug("FFmpeg not specified, attempting to auto-detect")
        ffmpeg_binary = get_ffmpeg_binary(auto_download)
        if ffmpeg_binary is None:
            logger.error("Could not find FFmpeg binary. Use --auto-download to enable automatic installation")
            raise RuntimeError("Could not find FFmpeg binary. Use --auto-download to enable automatic installation")
        logger.debug("Found FFmpeg at: %s", ffmpeg_binary)
    
    if opus_binary is None:
        logger.debug("Opusenc not specified, attempting to auto-detect")
        opus_binary = get_opus_binary(auto_download)
        if opus_binary is None:
            logger.error("Could not find Opus binary. Use --auto-download to enable automatic installation")
            raise RuntimeError("Could not find Opus binary. Use --auto-download to enable automatic installation")
        logger.debug("Found opusenc at: %s", opus_binary)
    
    vbr_parameter = "--vbr" if vbr else "--hard-cbr"
    logger.debug("Using encoding parameter: %s", vbr_parameter)

    is_mono = False
    ffprobe_path = None
    ffmpeg_dir, ffmpeg_file = os.path.split(ffmpeg_binary)
    ffprobe_candidates = [
        os.path.join(ffmpeg_dir, 'ffprobe'),
        os.path.join(ffmpeg_dir, 'ffprobe.exe'),
        'ffprobe',
        'ffprobe.exe',
    ]
    for candidate in ffprobe_candidates:
        if os.path.exists(candidate):
            ffprobe_path = candidate
            break
    if ffprobe_path:
        try:
            probe_cmd = [ffprobe_path, '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels', '-of', 'default=noprint_wrappers=1:nokey=1', filename]
            logger.debug(f"Probing audio channels with: {' '.join(probe_cmd)}")
            result = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                channels = result.stdout.strip()
                logger.debug(f"Detected channels: {channels}")
                if channels == '1':
                    is_mono = True
            else:
                logger.warning(f"ffprobe failed to detect channels: {result.stderr}")
        except Exception as e:
            logger.warning(f"Mono detection failed: {e}")
    else:
        logger.warning("ffprobe not found, will always force stereo conversion for non-Opus input.")
        is_mono = True  # Always force stereo if we can't check
    logger.info(f"Mono detected: {is_mono}, no_mono_conversion: {no_mono_conversion}")

    temp_path = None
    if keep_temp:
        temp_dir = os.path.join(tempfile.gettempdir(), "tonie_toolbox_temp")
        os.makedirs(temp_dir, exist_ok=True)
        base_filename = os.path.basename(filename)
        temp_path = os.path.join(temp_dir, f"{os.path.splitext(base_filename)[0]}_{bitrate}kbps.opus")
        logger.info("Creating persistent temporary file: %s", temp_path)
        
        logger.debug("Starting FFmpeg process")
        try:
            if is_mono and not no_mono_conversion:
                ffmpeg_cmd = [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav", "-ar", "48000", "-ac", "2", "-"]
                logger.info(f"Forcing stereo conversion for mono input: {' '.join(ffmpeg_cmd)}")
            else:
                ffmpeg_cmd = [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav", "-ar", "48000", "-"]
                logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            logger.trace("FFmpeg command: %s", ffmpeg_cmd)
            ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
        except FileNotFoundError:
            logger.error("Error opening input file %s", filename)
            raise RuntimeError(f"Error opening input file {filename}")
             
        logger.debug("Starting opusenc process")
        try:
            opusenc_cmd = [opus_binary, "--quiet", vbr_parameter, "--bitrate", f"{bitrate:d}", "-", temp_path]
            logger.trace("Opusenc command: %s", opusenc_cmd)
            opusenc_process = subprocess.Popen(
                opusenc_cmd, stdin=ffmpeg_process.stdout, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error("Opus encoding failed: %s", str(e))
            raise RuntimeError(f"Opus encoding failed: {str(e)}")
        
        ffmpeg_process.stdout.close()  # Allow ffmpeg to receive SIGPIPE if opusenc exits
        opusenc_return = opusenc_process.wait()
        ffmpeg_return = ffmpeg_process.wait()
        
        logger.debug("Process return codes - FFmpeg: %d, Opus: %d", ffmpeg_return, opusenc_return)
        
        if ffmpeg_return != 0:
            logger.error("FFmpeg processing failed with return code %d", ffmpeg_return)
            raise RuntimeError(f"FFmpeg processing failed with return code {ffmpeg_return}")
        
        if opusenc_return != 0:
            logger.error("Opus encoding failed with return code %d", opusenc_return)
            raise RuntimeError(f"Opus encoding failed with return code {opusenc_return}")
        
        logger.debug("Opening temporary file for reading: %s", temp_path)
        try:
            tmp_file = open(temp_path, "rb")
            logger.trace("Exiting get_opus_tempfile() with persistent temporary file")
            return tmp_file, temp_path
        except Exception as e:
            logger.error("Failed to open temporary file: %s", str(e))
            raise RuntimeError(f"Failed to open temporary file: {str(e)}")
    else:        
        logger.debug("Using in-memory temporary file")
        
        logger.debug("Starting FFmpeg process")
        try:
            if is_mono and not no_mono_conversion:
                ffmpeg_cmd = [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav", "-ar", "48000", "-ac", "2", "-"]
                logger.info(f"Forcing stereo conversion for mono input: {' '.join(ffmpeg_cmd)}")
            else:
                ffmpeg_cmd = [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav", "-ar", "48000", "-"]
                logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            logger.trace("FFmpeg command: %s", ffmpeg_cmd)
            ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
        except FileNotFoundError:
            logger.error("Error opening input file %s", filename)
            raise RuntimeError(f"Error opening input file {filename}")
             
        logger.debug("Starting opusenc process")
        try:
            opusenc_cmd = [opus_binary, "--quiet", vbr_parameter, "--bitrate", f"{bitrate:d}", "-", "-"]
            logger.trace("Opusenc command: %s", opusenc_cmd)
            opusenc_process = subprocess.Popen(
                opusenc_cmd, stdin=ffmpeg_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error("Opus encoding failed: %s", str(e))
            raise RuntimeError(f"Opus encoding failed: {str(e)}")

        ffmpeg_process.stdout.close()  # Allow ffmpeg to receive SIGPIPE if opusenc exits
        
        tmp_file = tempfile.SpooledTemporaryFile()
        bytes_written = 0
        
        logger.debug("Reading opusenc output")
        for chunk in iter(lambda: opusenc_process.stdout.read(4096), b""):
            tmp_file.write(chunk)
            bytes_written += len(chunk)
            if bytes_written % (1024 * 1024) == 0:  # Log every 1MB
                logger.trace("Written %d bytes so far", bytes_written)
        
        opusenc_return = opusenc_process.wait()
        ffmpeg_return = ffmpeg_process.wait()
        
        logger.debug("Process return codes - FFmpeg: %d, Opus: %d", ffmpeg_return, opusenc_return)
        
        if ffmpeg_return != 0:
            logger.error("FFmpeg processing failed with return code %d", ffmpeg_return)
            raise RuntimeError(f"FFmpeg processing failed with return code {ffmpeg_return}")
        
        if opusenc_return != 0:
            logger.error("Opus encoding failed with return code %d", opusenc_return)
            raise RuntimeError(f"Opus encoding failed with return code {opusenc_return}")
        
        logger.debug("Wrote %d bytes to temporary file", bytes_written)
        tmp_file.seek(0)
        
        logger.trace("Exiting get_opus_tempfile() with in-memory temporary file")
        return tmp_file, None


def filter_directories(glob_list: list[str]) -> list[str]:
    """
    Filter a list of glob results to include only audio files that can be handled by ffmpeg.
    
    Args:
        glob_list (list[str]): List of path names from glob.glob()
    Returns:
        list[str]: Filtered list containing only supported audio files
    """
    logger.trace("Entering filter_directories() with %d items", len(glob_list))
    logger.debug("Filtering %d glob results for supported audio files", len(glob_list))
    
    supported_extensions = SUPPORTED_EXTENSIONS
    logger.debug("Supported audio file extensions: %s", supported_extensions)
    
    filtered = []
    for name in glob_list:
        if os.path.isfile(name):
            ext = os.path.splitext(name)[1].lower()
            if ext in supported_extensions:
                filtered.append(name)
                logger.trace("Added supported audio file: %s", name)
            else:
                logger.trace("Skipping unsupported file: %s", name)
    
    logger.debug("Found %d supported audio files after filtering", len(filtered))
    logger.trace("Exiting filter_directories() with %d files", len(filtered))
    return filtered


def get_input_files(input_filename: str) -> list[str]:
    """
    Get a list of input files to process.
    
    Supports direct file paths, directory paths, glob patterns, and .lst files.
    
    Args:
        input_filename (str): Input file pattern or list file path
    Returns:
        list[str]: List of input file paths
    """
    logger.trace("Entering get_input_files(input_filename=%s)", input_filename)
    logger.debug("Getting input files for pattern: %s", input_filename)
    
    if input_filename.endswith(".lst"):
        logger.debug("Processing list file: %s", input_filename)
        list_dir = os.path.dirname(os.path.abspath(input_filename))
        input_files = []
        with open(input_filename, 'r', encoding='utf-8') as file_list:
            for line_num, line in enumerate(file_list, 1):
                fname = line.strip()
                if not fname or fname.startswith('#'):  # Skip empty lines and comments
                    logger.trace("Skipping empty line or comment at line %d", line_num)
                    continue
                
                # Remove any quote characters from path
                fname = fname.strip('"\'')
                    
                # Check if the path is absolute or has a drive letter (Windows)
                if os.path.isabs(fname) or (len(fname) > 1 and fname[1] == ':'):
                    full_path = fname  # Use as is if it's an absolute path
                    logger.trace("Using absolute path from line %d: %s", line_num, full_path)
                else:
                    full_path = os.path.join(list_dir, fname)
                    logger.trace("Using relative path from line %d: %s -> %s", line_num, fname, full_path)
                
                # Handle directory paths by finding all audio files in the directory
                if os.path.isdir(full_path):
                    logger.debug("Path is a directory, finding audio files in: %s", full_path)
                    dir_glob = os.path.join(full_path, "*")
                    dir_files = sorted(filter_directories(glob.glob(dir_glob)))
                    if dir_files:
                        input_files.extend(dir_files)
                        logger.debug("Found %d audio files in directory from line %d", len(dir_files), line_num)
                    else:
                        logger.warning("No audio files found in directory at line %d: %s", line_num, full_path)
                elif os.path.isfile(full_path):
                    input_files.append(full_path)
                    logger.trace("Added file from line %d: %s", line_num, full_path)
                else:
                    logger.warning("File not found at line %d: %s", line_num, full_path)
        
        logger.debug("Found %d files in list file", len(input_files))
    else:
        logger.debug("Processing input path: %s", input_filename)
        
        # Try the exact pattern first
        input_files = sorted(filter_directories(glob.glob(input_filename)))
        if input_files:
            logger.debug("Found %d files matching exact pattern", len(input_files))
        else:
            # If no extension is provided, try appending a wildcard for extension
            _, ext = os.path.splitext(input_filename)
            if not ext:
                wildcard_pattern = input_filename + ".*"
                logger.debug("No extension in pattern, trying with wildcard: %s", wildcard_pattern)
                input_files = sorted(filter_directories(glob.glob(wildcard_pattern)))
                
                # If still no files found, try treating it as a directory
                if not input_files and os.path.exists(os.path.dirname(input_filename)):
                    potential_dir = input_filename
                    if os.path.isdir(potential_dir):
                        logger.debug("Treating input as directory: %s", potential_dir)
                        dir_glob = os.path.join(potential_dir, "*")
                        input_files = sorted(filter_directories(glob.glob(dir_glob)))
                        if input_files:
                            logger.debug("Found %d audio files in directory", len(input_files))
                
                if input_files:
                    logger.debug("Found %d files after trying alternatives", len(input_files))
                else:
                    logger.warning("No files found for pattern %s even after trying alternatives", input_filename)
    
    logger.trace("Exiting get_input_files() with %d files", len(input_files))
    return input_files


def append_to_filename(output_filename: str, tag: str) -> str:
    """
    Append a tag to a filename, preserving the extension.
    
    Args:
        output_filename (str): Original filename
        tag (str): Tag to append (typically an 8-character hex value)
    Returns:
        str: Modified filename with tag
    """
    logger.trace("Entering append_to_filename(output_filename=%s, tag=%s)", output_filename, tag)
    logger.debug("Appending tag '%s' to filename: %s", tag, output_filename)
    pos = output_filename.rfind('.')
    if pos == -1:
        result = f"{output_filename}_{tag}"
        logger.debug("No extension found, result: %s", result)
        logger.trace("Exiting append_to_filename() with result=%s", result)
        return result
    else:
        result = f"{output_filename[:pos]}_{tag}{output_filename[pos:]}"
        logger.debug("Extension found, result: %s", result)
        logger.trace("Exiting append_to_filename() with result=%s", result)
        return result