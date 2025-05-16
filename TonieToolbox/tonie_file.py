#!/usr/bin/python3
"""
Tonie file operations module
"""

import datetime
import hashlib
import math
import struct
import time
import os

from  . import tonie_header_pb2
from .opus_packet import OpusPacket
from .ogg_page import OggPage
from .constants import OPUS_TAGS, SAMPLE_RATE_KHZ, TIMESTAMP_DEDUCT
from .logger import get_logger

logger = get_logger(__name__)


def toniefile_comment_add(buffer: bytearray, length: int, comment_str: str) -> int:
    """
    Add a comment string to an Opus comment packet buffer.
    
    Args:
        buffer (bytearray): Bytearray buffer to add comment to
        length (int): Current position in the buffer
        comment_str (str): Comment string to add
        
    Returns:
        int: New position in the buffer after adding comment
    """
    logger.debug("Adding comment: %s", comment_str)
    
    # Add 4-byte length prefix
    str_length = len(comment_str)
    buffer[length:length+4] = struct.pack("<I", str_length)
    length += 4
    
    buffer[length:length+str_length] = comment_str.encode('utf-8')
    length += str_length
    
    logger.trace("Added comment of length %d, new buffer position: %d", str_length, length)
    return length


def check_identification_header(page) -> None:
    """
    Check if a page contains a valid Opus identification header.
    
    Args:
        page: OggPage to check
        
    Raises:
        RuntimeError: If the header is invalid or unsupported
    """
    segment = page.segments[0]
    unpacked = struct.unpack("<8sBBHLH", segment.data[0:18])
    logger.debug("Checking Opus identification header")
    
    if unpacked[0] != b"OpusHead":
        logger.error("Invalid opus file: OpusHead signature not found")
        raise RuntimeError("Invalid opus file: OpusHead signature not found")
    
    if unpacked[1] != 1:
        logger.error("Invalid opus file: Version mismatch")
        raise RuntimeError("Invalid opus file: Opus version mismatch")
    
    if unpacked[2] != 2:
        logger.error("Only stereo tracks are supported, found channel count: %d", unpacked[2])
        raise RuntimeError(f"Only stereo tracks (2 channels) are supported. Found {unpacked[2]} channel(s). Please convert your audio to stereo format.")
    
    if unpacked[4] != SAMPLE_RATE_KHZ * 1000:
        logger.error("Sample rate needs to be 48 kHz, found: %d Hz", unpacked[4])
        raise RuntimeError(f"Sample rate needs to be 48 kHz. Found {unpacked[4]} Hz.")
    
    logger.debug("Opus identification header is valid")


def prepare_opus_tags(page, custom_tags: bool = False, bitrate: int = 64, vbr: bool = True, opus_binary: str = None) -> OggPage:
    """
    Prepare standard Opus tags for a Tonie file.
    
    Args:
        page: OggPage to modify
        custom_tags (bool): Whether to use custom TonieToolbox tags instead of default ones
        bitrate (int): Actual bitrate used for encoding
        vbr (bool): Whether variable bitrate was used
        opus_binary (str | None): Path to opusenc binary for version detection
        
    Returns:
        OggPage: Modified page with Tonie-compatible Opus tags
    """
    logger.debug("Preparing Opus tags for Tonie compatibility")
    page.segments.clear()
    
    if not custom_tags:
        # Use the default hardcoded tags for backward compatibility
        segment = OpusPacket(None)
        segment.size = len(OPUS_TAGS[0])
        segment.data = bytearray(OPUS_TAGS[0])
        segment.spanning_packet = True
        segment.first_packet = True
        page.segments.append(segment)

        segment = OpusPacket(None)
        segment.size = len(OPUS_TAGS[1])
        segment.data = bytearray(OPUS_TAGS[1])
        segment.spanning_packet = False
        segment.first_packet = False
        page.segments.append(segment)
    else:
        # Use custom tags for TonieToolbox
        # Create buffer for opus tags (similar to teddyCloud implementation)
        logger.debug("Creating custom Opus tags")
        comment_data = bytearray(0x1B4)
        comment_data_pos = 0
        comment_data[comment_data_pos:comment_data_pos+8] = b"OpusTags"
        comment_data_pos += 8        
        # Vendor string
        comment_data_pos = toniefile_comment_add(comment_data, comment_data_pos, "TonieToolbox")        
        # Number of comments (3 comments: version, encoder info, and encoder options)
        comments_count = 3
        comment_data[comment_data_pos:comment_data_pos+4] = struct.pack("<I", comments_count)
        comment_data_pos += 4        
        # Add version information
        from . import __version__
        version_str = f"version={__version__}"
        comment_data_pos = toniefile_comment_add(comment_data, comment_data_pos, version_str)        
        # Get actual opusenc version
        from .dependency_manager import get_opus_version
        encoder_info = get_opus_version(opus_binary)
        comment_data_pos = toniefile_comment_add(comment_data, comment_data_pos, f"encoder={encoder_info}")        
        # Create encoder options string with actual settings
        vbr_opt = "--vbr" if vbr else "--cbr"
        encoder_options = f"encoder_options=--bitrate {bitrate} {vbr_opt}"
        comment_data_pos = toniefile_comment_add(comment_data, comment_data_pos, encoder_options)        
        # Add padding
        remain = len(comment_data) - comment_data_pos - 4
        comment_data[comment_data_pos:comment_data_pos+4] = struct.pack("<I", remain)
        comment_data_pos += 4
        comment_data[comment_data_pos:comment_data_pos+4] = b"pad="        
        # Create segments - handle data in chunks of 255 bytes maximum
        comment_data = comment_data[:comment_data_pos + remain]  # Trim to actual used size        
        # Split large data into smaller segments (each <= 255 bytes)
        remaining_data = comment_data
        first_segment = True        
        while remaining_data:
            chunk_size = min(255, len(remaining_data))
            segment = OpusPacket(None)
            segment.size = chunk_size
            segment.data = remaining_data[:chunk_size]
            segment.spanning_packet = len(remaining_data) > chunk_size  # More data follows
            segment.first_packet = first_segment
            page.segments.append(segment)
            
            remaining_data = remaining_data[chunk_size:]
            first_segment = False
        
    page.correct_values(0)
    logger.trace("Opus tags prepared with %d segments", len(page.segments))
    return page


def copy_first_and_second_page(
    in_file,
    out_file,
    timestamp: int,
    sha,
    use_custom_tags: bool = True,
    bitrate: int = 64,
    vbr: bool = True,
    opus_binary: str = None
) -> None:
    """
    Copy and modify the first two pages of an Opus file for a Tonie file.
    
    Args:
        in_file: Input file handle
        out_file: Output file handle
        timestamp (int): Timestamp to use for the Tonie file
        sha: SHA1 hash object to update with written data
        use_custom_tags (bool): Whether to use custom TonieToolbox tags
        bitrate (int): Actual bitrate used for encoding
        vbr (bool): Whether VBR was used
        opus_binary (str | None): Path to opusenc binary
    """
    logger.debug("Copying first and second pages with timestamp %d", timestamp)
    found = OggPage.seek_to_page_header(in_file)
    if not found:
        logger.error("First OGG page not found in input file")
        raise RuntimeError("First ogg page not found")
    
    page = OggPage(in_file)
    page.serial_no = timestamp
    page.checksum = page.calc_checksum()
    check_identification_header(page)
    page.write_page(out_file, sha)
    logger.debug("First page written successfully")

    found = OggPage.seek_to_page_header(in_file)
    if not found:
        logger.error("Second OGG page not found in input file")
        raise RuntimeError("Second ogg page not found")
    
    page = OggPage(in_file)
    page.serial_no = timestamp
    page.checksum = page.calc_checksum()
    page = prepare_opus_tags(page, use_custom_tags, bitrate, vbr, opus_binary)
    page.write_page(out_file, sha)
    logger.debug("Second page written successfully")


def skip_first_two_pages(in_file) -> None:
    """
    Skip the first two pages of an Opus file.
    
    Args:
        in_file: Input file handle
        
    Raises:
        RuntimeError: If OGG pages cannot be found or are invalid
    """
    logger.debug("Skipping first two pages")
    found = OggPage.seek_to_page_header(in_file)
    if not found:
        logger.error("First OGG page not found in input file")
        raise RuntimeError("First OGG page not found in input file")
    
    try:
        page = OggPage(in_file)
        check_identification_header(page)
    except RuntimeError as e:
        # The check_identification_header function already logs errors
        # Just re-raise with the same message
        raise RuntimeError(str(e))

    found = OggPage.seek_to_page_header(in_file)
    if not found:
        logger.error("Second OGG page not found in input file")
        raise RuntimeError("Second OGG page not found in input file")
    
    OggPage(in_file)
    logger.debug("First two pages skipped successfully")


def read_all_remaining_pages(in_file) -> list:
    """
    Read all remaining OGG pages from an input file.
    
    Args:
        in_file: Input file handle
        
    Returns:
        list: List of OggPage objects
    """
    logger.debug("Reading all remaining OGG pages")
    remaining_pages = []

    found = OggPage.seek_to_page_header(in_file)
    page_count = 0
    
    while found:
        remaining_pages.append(OggPage(in_file))
        page_count += 1
        found = OggPage.seek_to_page_header(in_file)
    
    logger.debug("Read %d remaining OGG pages", page_count)
    return remaining_pages


def resize_pages(
    old_pages: list,
    max_page_size: int,
    first_page_size: int,
    template_page,
    last_granule: int = 0,
    start_no: int = 2,
    set_last_page_flag: bool = False
) -> list:
    """
    Resize OGG pages to fit Tonie requirements.
    
    Args:
        old_pages (list): List of original OggPage objects
        max_page_size (int): Maximum size for pages
        first_page_size (int): Size for the first page
        template_page: Template OggPage to use for creating new pages
        last_granule (int): Last granule position
        start_no (int): Starting page number
        set_last_page_flag (bool): Whether to set the last page flag
        
    Returns:
        list: List of resized OggPage objects
    """
    logger.debug("Resizing %d OGG pages (max_size=%d, first_size=%d, start_no=%d)", 
                len(old_pages), max_page_size, first_page_size, start_no)
    
    new_pages = []
    page = None
    page_no = start_no
    max_size = first_page_size

    new_page = OggPage.from_page(template_page)
    new_page.page_no = page_no

    while len(old_pages) or not (page is None):
        if page is None:
            page = old_pages.pop(0)

        size = page.get_size_of_first_opus_packet()
        seg_count = page.get_segment_count_of_first_opus_packet()

        if (size + seg_count + new_page.get_page_size() <= max_size) and (len(new_page.segments) + seg_count < 256):
            for i in range(seg_count):
                new_page.segments.append(page.segments.pop(0))
            if not len(page.segments):
                page = None
        else:
            new_page.pad(max_size)
            new_page.correct_values(last_granule)
            last_granule = new_page.granule_position
            new_pages.append(new_page)
            logger.trace("Created new page #%d with %d segments", page_no, len(new_page.segments))

            new_page = OggPage.from_page(template_page)
            page_no = page_no + 1
            new_page.page_no = page_no
            max_size = max_page_size

    if len(new_page.segments):
        if set_last_page_flag:
            new_page.page_type = 4
            logger.debug("Setting last page flag on page #%d", page_no)
            
        new_page.pad(max_size)
        new_page.correct_values(last_granule)
        new_pages.append(new_page)
        logger.trace("Created final page #%d with %d segments", page_no, len(new_page.segments))

    logger.debug("Resized to %d OGG pages", len(new_pages))
    return new_pages


def fix_tonie_header(out_file, chapters: list, timestamp: int, sha) -> None:
    """
    Fix the Tonie header in a file.
    
    Args:
        out_file: Output file handle
        chapters (list): List of chapter page numbers
        timestamp (int): Timestamp for the Tonie file
        sha: SHA1 hash object with file content
    """
    logger.info("Writing Tonie header with %d chapters and timestamp %d", len(chapters), timestamp)
    tonie_header = tonie_header_pb2.TonieHeader()

    tonie_header.dataHash = sha.digest()
    data_length = out_file.seek(0, 1) - 0x1000
    tonie_header.dataLength = data_length
    tonie_header.timestamp = timestamp
    logger.debug("Data length: %d bytes, SHA1: %s", data_length, sha.hexdigest())

    for chapter in chapters:
        tonie_header.chapterPages.append(chapter)
        logger.trace("Added chapter at page %d", chapter)

    tonie_header.padding = bytes(0x100)

    header = tonie_header.SerializeToString()
    pad = 0xFFC - len(header) + 0x100
    tonie_header.padding = bytes(pad)
    header = tonie_header.SerializeToString()

    out_file.seek(0)
    out_file.write(struct.pack(">L", len(header)))
    out_file.write(header)
    logger.debug("Tonie header written successfully (size: %d bytes)", len(header))


def create_tonie_file(
    output_file: str,
    input_files: list[str],
    no_tonie_header: bool = False,
    user_timestamp: str = None,
    bitrate: int = 96,
    vbr: bool = True,
    ffmpeg_binary: str = None,
    opus_binary: str = None,
    keep_temp: bool = False,
    auto_download: bool = False,
    use_custom_tags: bool = True,
    no_mono_conversion: bool = False
) -> None:
    """
    Create a Tonie file from input files.
    
    Args:
        output_file (str): Output file path
        input_files (list[str]): List of input file paths
        no_tonie_header (bool): Whether to omit the Tonie header
        user_timestamp (str | None): Custom timestamp to use
        bitrate (int): Bitrate for encoding in kbps
        vbr (bool): Whether to use variable bitrate encoding (True) or constant (False)
        ffmpeg_binary (str | None): Path to ffmpeg binary
        opus_binary (str | None): Path to opusenc binary
        keep_temp (bool): Whether to keep temporary opus files for testing
        auto_download (bool): Whether to automatically download dependencies if not found
        use_custom_tags (bool): Whether to use dynamic comment tags generated with toniefile_comment_add
        no_mono_conversion (bool): Whether to skip mono conversion during audio processing
    """
    from .audio_conversion import get_opus_tempfile
    
    logger.trace("Entering create_tonie_file(output_file=%s, input_files=%s, no_tonie_header=%s, user_timestamp=%s, "
                "bitrate=%d, vbr=%s, ffmpeg_binary=%s, opus_binary=%s, keep_temp=%s, auto_download=%s, use_custom_tags=%s, no_mono_conversion=%s)",
                output_file, input_files, no_tonie_header, user_timestamp, bitrate, vbr, ffmpeg_binary, 
                opus_binary, keep_temp, auto_download, use_custom_tags, no_mono_conversion)
    
    logger.info("Creating Tonie file from %d input files", len(input_files))
    logger.debug("Output file: %s, Bitrate: %d kbps, VBR: %s, No header: %s", 
                output_file, bitrate, vbr, no_tonie_header)
    
    temp_files = []  # Keep track of temporary files created
    
    with open(output_file, "wb") as out_file:
        if not no_tonie_header:
            logger.debug("Reserving space for Tonie header (0x1000 bytes)")
            out_file.write(bytearray(0x1000))

        if user_timestamp is not None:
            if os.path.isfile(user_timestamp) and user_timestamp.lower().endswith('.taf'):
                logger.debug("Extracting timestamp from Tonie file: %s", user_timestamp)
                from .tonie_analysis import get_header_info
                try:
                    with open(user_timestamp, "rb") as taf_file:
                        _, tonie_header, _, _, _, _, _, _, _, bitstream_serial_no = get_header_info(taf_file)
                        timestamp = bitstream_serial_no
                        logger.debug("Extracted timestamp from Tonie file: %d", timestamp)
                except Exception as e:
                    logger.error("Failed to extract timestamp from Tonie file: %s", str(e))
                    timestamp = int(time.time())
                    logger.debug("Falling back to current timestamp: %d", timestamp)
            elif user_timestamp.startswith("0x"):
                timestamp = int(user_timestamp, 16)
                logger.debug("Using user-provided hexadecimal timestamp: %d", timestamp)
            else:
                try:
                    timestamp = int(user_timestamp)
                    logger.debug("Using user-provided decimal timestamp: %d", timestamp)
                except ValueError:
                    logger.error("Invalid timestamp format: %s", user_timestamp)
                    timestamp = int(time.time())
                    logger.debug("Falling back to current timestamp: %d", timestamp)
        else:
            timestamp = int(time.time()-TIMESTAMP_DEDUCT)
            logger.debug("Using current timestamp - 0x50000000: %d", timestamp)

        sha1 = hashlib.sha1()

        template_page = None
        chapters = []
        total_granule = 0
        next_page_no = 2
        max_size = 0x1000
        other_size = 0xE00
        last_track = False

        pad_len = math.ceil(math.log(len(input_files) + 1, 10))
        format_string = "[{{:0{}d}}/{:0{}d}] {{}}".format(pad_len, len(input_files), pad_len)

        for index in range(len(input_files)):
            fname = input_files[index]
            logger.info(format_string.format(index + 1, fname))
            if index == len(input_files) - 1:
                last_track = True
                logger.debug("Processing last track")

            if fname.lower().endswith(".opus"):
                logger.debug("Input is already in Opus format")
                handle = open(fname, "rb")
                temp_file_path = None
            else:
                logger.debug("Converting %s to Opus format (bitrate: %d kbps, VBR: %s, no_mono_conversion: %s)", 
                            fname, bitrate, vbr, no_mono_conversion)
                handle, temp_file_path = get_opus_tempfile(ffmpeg_binary, opus_binary, fname, bitrate, vbr, keep_temp, auto_download, no_mono_conversion=no_mono_conversion)
                if temp_file_path:
                    temp_files.append(temp_file_path)
                    logger.debug("Temporary opus file saved to: %s", temp_file_path)

            try:
                if next_page_no == 2:
                    logger.debug("Processing first file: copying first and second page")
                    copy_first_and_second_page(handle, out_file, timestamp, sha1, use_custom_tags, bitrate, vbr, opus_binary)
                else:
                    logger.debug("Processing subsequent file: skipping first and second page")
                    other_size = max_size
                    skip_first_two_pages(handle)

                logger.debug("Reading remaining pages from file")
                pages = read_all_remaining_pages(handle)
                logger.debug("Read %d pages from file", len(pages))

                if template_page is None:
                    template_page = OggPage.from_page(pages[0])
                    template_page.serial_no = timestamp
                    logger.debug("Created template page with serial no %d", timestamp)

                if next_page_no == 2:
                    chapters.append(0)
                    logger.debug("Added first chapter at page 0")
                else:
                    chapters.append(next_page_no)
                    logger.debug("Added chapter at page %d", next_page_no)

                logger.debug("Resizing pages for track %d", index + 1)
                new_pages = resize_pages(pages, max_size, other_size, template_page,
                                        total_granule, next_page_no, last_track)
                logger.debug("Resized to %d pages for track %d", len(new_pages), index + 1)

                for i, new_page in enumerate(new_pages):
                    logger.trace("Writing page %d/%d (page number: %d)", i+1, len(new_pages), new_page.page_no)
                    new_page.write_page(out_file, sha1)
                
                last_page = new_pages[len(new_pages) - 1]
                total_granule = last_page.granule_position
                next_page_no = last_page.page_no + 1
                logger.debug("Track %d processed, next page no: %d, total granule: %d", 
                            index + 1, next_page_no, total_granule)
            except Exception as e:
                logger.error("Error processing file %s: %s", fname, str(e))
                raise
            finally:
                handle.close()

        if not no_tonie_header:
            logger.debug("Writing Tonie header")
            fix_tonie_header(out_file, chapters, timestamp, sha1)
            
    if keep_temp and temp_files:
        logger.info("Kept %d temporary opus files in %s", len(temp_files), os.path.dirname(temp_files[0]))
    
    logger.trace("Exiting create_tonie_file() successfully")
    logger.info("Successfully created Tonie file: %s", output_file)