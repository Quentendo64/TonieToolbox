"""
Audio conversion functionality for the TonieToolbox package
"""

import os
import glob
import subprocess
import tempfile
from .dependency_manager import get_ffmpeg_binary, get_opus_binary
from .logger import get_logger

logger = get_logger('audio_conversion')


def get_opus_tempfile(ffmpeg_binary=None, opus_binary=None, filename=None, bitrate=48, vbr=True, keep_temp=False, auto_download=False):
    """
    Convert an audio file to Opus format and return a temporary file handle.
    
    Args:
        ffmpeg_binary: Path to the ffmpeg binary. If None, will be auto-detected or downloaded.
        opus_binary: Path to the opusenc binary. If None, will be auto-detected or downloaded.
        filename: Path to the input audio file
        bitrate: Bitrate for the Opus encoding in kbps
        vbr: Whether to use variable bitrate encoding
        keep_temp: Whether to keep the temporary files for testing
        auto_download: Whether to automatically download dependencies if not found
        
    Returns:
        tuple: (file handle, temp_file_path) or (file handle, None) if keep_temp is False
    """
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

    temp_path = None
    if keep_temp:
        temp_dir = os.path.join(tempfile.gettempdir(), "tonie_toolbox_temp")
        os.makedirs(temp_dir, exist_ok=True)
        base_filename = os.path.basename(filename)
        temp_path = os.path.join(temp_dir, f"{os.path.splitext(base_filename)[0]}_{bitrate}kbps.opus")
        logger.info("Creating persistent temporary file: %s", temp_path)
        
        logger.debug("Starting FFmpeg process")
        ffmpeg_process = subprocess.Popen(
            [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav",
             "-ar", "48000", "-"], stdout=subprocess.PIPE)
             
        logger.debug("Starting opusenc process")
        opusenc_process = subprocess.Popen(
            [opus_binary, "--quiet", vbr_parameter, "--bitrate", f"{bitrate:d}", "-", temp_path],
            stdin=ffmpeg_process.stdout, stderr=subprocess.DEVNULL)
        
        opusenc_process.communicate()
        
        if opusenc_process.returncode != 0:
            logger.error("Opus encoding failed with return code %d", opusenc_process.returncode)
            raise RuntimeError(f"Opus encoding failed with return code {opusenc_process.returncode}")
        
        logger.debug("Opening temporary file for reading")
        tmp_file = open(temp_path, "rb")
        return tmp_file, temp_path
    else:        
        logger.debug("Using in-memory temporary file")
        
        logger.debug("Starting FFmpeg process")
        ffmpeg_process = subprocess.Popen(
            [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav",
             "-ar", "48000", "-"], stdout=subprocess.PIPE)
             
        logger.debug("Starting opusenc process")
        opusenc_process = subprocess.Popen(
            [opus_binary, "--quiet", vbr_parameter, "--bitrate", f"{bitrate:d}", "-", "-"],
            stdin=ffmpeg_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        tmp_file = tempfile.SpooledTemporaryFile()
        bytes_written = 0
        
        logger.debug("Reading opusenc output")
        for chunk in iter(lambda: opusenc_process.stdout.read(4096), b""):
            tmp_file.write(chunk)
            bytes_written += len(chunk)
        
        if opusenc_process.wait() != 0:
            logger.error("Opus encoding failed with return code %d", opusenc_process.returncode)
            raise RuntimeError(f"Opus encoding failed with return code {opusenc_process.returncode}")
        
        logger.debug("Wrote %d bytes to temporary file", bytes_written)
        tmp_file.seek(0)
        
        return tmp_file, None


def filter_directories(glob_list):
    """
    Filter a list of glob results to include only audio files that can be handled by ffmpeg.
    
    Args:
        glob_list: List of path names from glob.glob()
        
    Returns:
        list: Filtered list containing only supported audio files
    """
    logger.debug("Filtering %d glob results for supported audio files", len(glob_list))
    
    # Common audio file extensions supported by ffmpeg
    supported_extensions = [
        '.wav', '.mp3', '.aac', '.m4a', '.flac', '.ogg', '.opus',
        '.ape', '.wma', '.aiff', '.mp2', '.mp4', '.webm', '.mka'
    ]
    
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
    return filtered


def get_input_files(input_filename):
    """
    Get a list of input files to process.
    
    Supports direct file paths, directory paths, glob patterns, and .lst files.
    
    Args:
        input_filename: Input file pattern or list file path
        
    Returns:
        list: List of input file paths
    """
    logger.debug("Getting input files for pattern: %s", input_filename)
    
    if input_filename.endswith(".lst"):
        logger.debug("Processing list file: %s", input_filename)
        list_dir = os.path.dirname(os.path.abspath(input_filename))
        input_files = []
        with open(input_filename) as file_list:
            for line in file_list:
                fname = line.rstrip()
                full_path = os.path.join(list_dir, fname)
                input_files.append(full_path)
                logger.trace("Added file from list: %s", full_path)
        logger.debug("Found %d files in list file", len(input_files))
    else:
        logger.debug("Processing glob pattern: %s", input_filename)
        input_files = sorted(filter_directories(glob.glob(input_filename)))
        logger.debug("Found %d files matching pattern", len(input_files))
    
    return input_files


def append_to_filename(output_filename, tag):
    """
    Append a tag to a filename, preserving the extension.
    
    Args:
        output_filename: Original filename
        tag: Tag to append (typically an 8-character hex value)
        
    Returns:
        str: Modified filename with tag
    """
    logger.debug("Appending tag '%s' to filename: %s", tag, output_filename)
    pos = output_filename.rfind('.')
    if pos == -1:
        result = f"{output_filename}_{tag}"
        logger.debug("No extension found, result: %s", result)
        return result
    else:
        result = f"{output_filename[:pos]}_{tag}{output_filename[pos:]}"
        logger.debug("Extension found, result: %s", result)
        return result