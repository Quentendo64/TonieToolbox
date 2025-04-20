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
        try:
            ffmpeg_process = subprocess.Popen(
                [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav",
                 "-ar", "48000", "-"], stdout=subprocess.PIPE)
        except FileNotFoundError:
            logger.error("Error opening input file %s", filename)
            raise RuntimeError(f"Error opening input file {filename}")
             
        logger.debug("Starting opusenc process")
        try:
            opusenc_process = subprocess.Popen(
                [opus_binary, "--quiet", vbr_parameter, "--bitrate", f"{bitrate:d}", "-", temp_path],
                stdin=ffmpeg_process.stdout, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error("Opus encoding failed: %s", str(e))
            raise RuntimeError(f"Opus encoding failed: {str(e)}")
        
        ffmpeg_process.stdout.close()  # Allow ffmpeg to receive SIGPIPE if opusenc exits
        opusenc_return = opusenc_process.wait()
        ffmpeg_return = ffmpeg_process.wait()
        
        if ffmpeg_return != 0:
            logger.error("FFmpeg processing failed with return code %d", ffmpeg_return)
            raise RuntimeError(f"FFmpeg processing failed with return code {ffmpeg_return}")
        
        if opusenc_return != 0:
            logger.error("Opus encoding failed with return code %d", opusenc_return)
            raise RuntimeError(f"Opus encoding failed with return code {opusenc_return}")
        
        logger.debug("Opening temporary file for reading")
        try:
            tmp_file = open(temp_path, "rb")
            return tmp_file, temp_path
        except Exception as e:
            logger.error("Failed to open temporary file: %s", str(e))
            raise RuntimeError(f"Failed to open temporary file: {str(e)}")
    else:        
        logger.debug("Using in-memory temporary file")
        
        logger.debug("Starting FFmpeg process")
        try:
            ffmpeg_process = subprocess.Popen(
                [ffmpeg_binary, "-hide_banner", "-loglevel", "warning", "-i", filename, "-f", "wav",
                 "-ar", "48000", "-"], stdout=subprocess.PIPE)
        except FileNotFoundError:
            logger.error("Error opening input file %s", filename)
            raise RuntimeError(f"Error opening input file {filename}")
             
        logger.debug("Starting opusenc process")
        try:
            opusenc_process = subprocess.Popen(
                [opus_binary, "--quiet", vbr_parameter, "--bitrate", f"{bitrate:d}", "-", "-"],
                stdin=ffmpeg_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
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
        
        opusenc_return = opusenc_process.wait()
        ffmpeg_return = ffmpeg_process.wait()
        
        if ffmpeg_return != 0:
            logger.error("FFmpeg processing failed with return code %d", ffmpeg_return)
            raise RuntimeError(f"FFmpeg processing failed with return code {ffmpeg_return}")
        
        if opusenc_return != 0:
            logger.error("Opus encoding failed with return code %d", opusenc_return)
            raise RuntimeError(f"Opus encoding failed with return code {opusenc_return}")
        
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
        with open(input_filename, 'r', encoding='utf-8') as file_list:
            for line_num, line in enumerate(file_list, 1):
                fname = line.strip()
                if not fname or fname.startswith('#'):  # Skip empty lines and comments
                    continue
                
                # Remove any quote characters from path
                fname = fname.strip('"\'')
                    
                # Check if the path is absolute or has a drive letter (Windows)
                if os.path.isabs(fname) or (len(fname) > 1 and fname[1] == ':'):
                    full_path = fname  # Use as is if it's an absolute path
                    logger.trace("Using absolute path from list: %s", full_path)
                else:
                    full_path = os.path.join(list_dir, fname)
                    logger.trace("Using relative path from list: %s", full_path)
                
                # Handle directory paths by finding all audio files in the directory
                if os.path.isdir(full_path):
                    logger.debug("Path is a directory, finding audio files in: %s", full_path)
                    dir_glob = os.path.join(full_path, "*")
                    dir_files = sorted(filter_directories(glob.glob(dir_glob)))
                    if dir_files:
                        input_files.extend(dir_files)
                        logger.debug("Found %d audio files in directory", len(dir_files))
                    else:
                        logger.warning("No audio files found in directory at line %d: %s", line_num, full_path)
                elif os.path.isfile(full_path):
                    input_files.append(full_path)
                else:
                    logger.warning("File not found at line %d: %s", line_num, full_path)
        
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