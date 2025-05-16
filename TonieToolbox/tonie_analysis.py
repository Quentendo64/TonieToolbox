#!/usr/bin/python3
"""
Functions for analyzing Tonie files
"""

import datetime
import hashlib
import struct
import os
from  . import tonie_header_pb2
from .ogg_page import OggPage
from .logger import get_logger

logger = get_logger(__name__)

def format_time(ts: float) -> str:
    """
    Format a timestamp as a human-readable date and time string.
    
    Args:
        ts (float): Timestamp to format
        
    Returns:
        str: Formatted date and time string
    """
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def format_hex(data: bytes) -> str:
    """
    Format binary data as a hex string.
    
    Args:
        data (bytes): Binary data to format
        
    Returns:
        str: Formatted hex string
    """
    return "".join(format(x, "02X") for x in data)


def granule_to_time_string(granule: int, sample_rate: int = 1) -> str:
    """
    Convert a granule position to a time string.
    
    Args:
        granule (int): Granule position
        sample_rate (int): Sample rate in Hz
        
    Returns:
        str: Formatted time string (HH:MM:SS.FF)
    """
    total_seconds = granule / sample_rate
    hours = int(total_seconds / 3600)
    minutes = int((total_seconds - (hours * 3600)) / 60)
    seconds = int(total_seconds - (hours * 3600) - (minutes * 60))
    fraction = int((total_seconds * 100) % 100)
    return "{:02d}:{:02d}:{:02d}.{:02d}".format(hours, minutes, seconds, fraction)


def get_header_info(in_file) -> tuple:
    """
    Get header information from a Tonie file.
    
    Args:
        in_file: Input file handle
        
    Returns:
        tuple: Header size, Tonie header object, file size, audio size, SHA1 sum,
               Opus header found flag, Opus version, channel count, sample rate, bitstream serial number,
               Opus comments dictionary
               
    Raises:
        RuntimeError: If OGG pages cannot be found
    """
    logger.debug("Reading Tonie header information")
    
    tonie_header = tonie_header_pb2.TonieHeader()
    header_size = struct.unpack(">L", in_file.read(4))[0]
    logger.debug("Header size: %d bytes", header_size)
    
    tonie_header = tonie_header.FromString(in_file.read(header_size))
    logger.debug("Read Tonie header with %d chapter pages", len(tonie_header.chapterPages))

    sha1sum = hashlib.sha1(in_file.read())
    logger.debug("Calculated SHA1: %s", sha1sum.hexdigest())

    file_size = in_file.tell()
    in_file.seek(4 + header_size)
    audio_size = file_size - in_file.tell()
    logger.debug("File size: %d bytes, Audio size: %d bytes", file_size, audio_size)

    found = OggPage.seek_to_page_header(in_file)
    if not found:
        logger.error("First OGG page not found")
        raise RuntimeError("First ogg page not found")
    
    first_page = OggPage(in_file)
    logger.debug("Read first OGG page")

    unpacked = struct.unpack("<8sBBHLH", first_page.segments[0].data[0:18])
    opus_head_found = unpacked[0] == b"OpusHead"
    opus_version = unpacked[1]
    channel_count = unpacked[2]
    sample_rate = unpacked[4]
    bitstream_serial_no = first_page.serial_no
    
    logger.debug("Opus header found: %s, Version: %d, Channels: %d, Sample rate: %d Hz, Serial: %d", 
                opus_head_found, opus_version, channel_count, sample_rate, bitstream_serial_no)
    opus_comments = {}
    found = OggPage.seek_to_page_header(in_file)
    if not found:
        logger.error("Second OGG page not found")
        raise RuntimeError("Second ogg page not found")
    
    second_page = OggPage(in_file)
    logger.debug("Read second OGG page")
    
    try:
        comment_data = bytearray()
        for segment in second_page.segments:
            comment_data.extend(segment.data)
        
        if comment_data.startswith(b"OpusTags"):
            pos = 8  # Skip "OpusTags"
            # Extract vendor string
            if pos + 4 <= len(comment_data):
                vendor_length = struct.unpack("<I", comment_data[pos:pos+4])[0]
                pos += 4
                if pos + vendor_length <= len(comment_data):
                    vendor = comment_data[pos:pos+vendor_length].decode('utf-8', errors='replace')
                    opus_comments["vendor"] = vendor
                    pos += vendor_length
                    
                    # Extract comments count
                    if pos + 4 <= len(comment_data):
                        comments_count = struct.unpack("<I", comment_data[pos:pos+4])[0]
                        pos += 4
                        
                        # Extract individual comments
                        for i in range(comments_count):
                            if pos + 4 <= len(comment_data):
                                comment_length = struct.unpack("<I", comment_data[pos:pos+4])[0]
                                pos += 4
                                if pos + comment_length <= len(comment_data):
                                    comment = comment_data[pos:pos+comment_length].decode('utf-8', errors='replace')
                                    pos += comment_length
                                    
                                    # Split comment into key/value if possible
                                    if "=" in comment:
                                        key, value = comment.split("=", 1)
                                        opus_comments[key] = value
                                    else:
                                        opus_comments[f"comment_{i}"] = comment
                                else:
                                    break
                            else:
                                break
    except Exception as e:
        logger.error("Failed to parse Opus comments: %s", str(e))

    return (
        header_size, tonie_header, file_size, audio_size, sha1sum,
        opus_head_found, opus_version, channel_count, sample_rate, bitstream_serial_no,
        opus_comments
    )


def get_audio_info(in_file, sample_rate: int, tonie_header, header_size: int) -> tuple:
    """
    Get audio information from a Tonie file.
    
    Args:
        in_file: Input file handle
        sample_rate (int): Sample rate in Hz
        tonie_header: Tonie header object
        header_size (int): Header size in bytes
        
    Returns:
        tuple: Page count, alignment OK flag, page size OK flag, total time, chapter times
    """
    logger.debug("Reading audio information")
    
    chapter_granules = []
    if 0 in tonie_header.chapterPages:
        chapter_granules.append(0)
        logger.trace("Added chapter at granule position 0")

    alignment_okay = in_file.tell() == (512 + 4 + header_size)
    logger.debug("Initial alignment OK: %s (position: %d)", alignment_okay, in_file.tell())
    
    page_size_okay = True
    page_count = 2

    page = None
    found = OggPage.seek_to_page_header(in_file)
    while found:
        page_count = page_count + 1
        page = OggPage(in_file)
        logger.trace("Read page #%d with granule position %d", page.page_no, page.granule_position)

        found = OggPage.seek_to_page_header(in_file)
        if found and in_file.tell() % 0x1000 != 0:
            alignment_okay = False
            logger.debug("Page alignment not OK at position %d", in_file.tell())

        if page_size_okay and page_count > 3 and page.get_page_size() != 0x1000 and found:
            page_size_okay = False
            logger.debug("Page size not OK for page #%d (size: %d)", page.page_no, page.get_page_size())
            
        if page.page_no in tonie_header.chapterPages:
            chapter_granules.append(page.granule_position)
            logger.trace("Added chapter at granule position %d from page #%d", 
                        page.granule_position, page.page_no)

    chapter_granules.append(page.granule_position)
    logger.debug("Found %d chapters", len(chapter_granules) - 1)

    chapter_times = []
    for i in range(1, len(chapter_granules)):
        length = chapter_granules[i] - chapter_granules[i - 1]
        time_str = granule_to_time_string(length, sample_rate)
        chapter_times.append(time_str)
        logger.debug("Chapter %d duration: %s", i, time_str)

    total_time = page.granule_position / sample_rate
    logger.debug("Total time: %f seconds (%s)", total_time, 
                granule_to_time_string(page.granule_position, sample_rate))

    return page_count, alignment_okay, page_size_okay, total_time, chapter_times


def check_tonie_file(filename: str) -> bool:
    """
    Check if a file is a valid Tonie file and display information about it.
    
    Args:
        filename (str): Path to the file to check
        
    Returns:
        bool: True if the file is valid, False otherwise
    """
    logger.info("Checking Tonie file: %s", filename)
    
    with open(filename, "rb") as in_file:
        header_size, tonie_header, file_size, audio_size, sha1, opus_head_found, \
        opus_version, channel_count, sample_rate, bitstream_serial_no, opus_comments = get_header_info(in_file)

        page_count, alignment_okay, page_size_okay, total_time, \
        chapters = get_audio_info(in_file, sample_rate, tonie_header, header_size)

    hash_ok = tonie_header.dataHash == sha1.digest()
    timestamp_ok = tonie_header.timestamp == bitstream_serial_no
    audio_size_ok = tonie_header.dataLength == audio_size
    opus_ok = opus_head_found and \
              opus_version == 1 and \
              (sample_rate == 48000 or sample_rate == 44100) and \
              channel_count == 2

    all_ok = hash_ok and \
             timestamp_ok and \
             opus_ok and \
             alignment_okay and \
             page_size_okay

    logger.debug("Validation results:")
    logger.debug("  Hash OK: %s", hash_ok)
    logger.debug("  Timestamp OK: %s", timestamp_ok)
    logger.debug("  Audio size OK: %s", audio_size_ok)
    logger.debug("  Opus OK: %s", opus_ok)
    logger.debug("  Alignment OK: %s", alignment_okay)
    logger.debug("  Page size OK: %s", page_size_okay)
    logger.debug("  All OK: %s", all_ok)

    print("[{}] SHA1 hash: 0x{}".format("OK" if hash_ok else "NOT OK", format_hex(tonie_header.dataHash)))
    if not hash_ok:
        print("            actual: 0x{}".format(sha1.hexdigest().upper()))
    print("[{}] Timestamp: [0x{:X}] {}".format("OK" if timestamp_ok else "NOT OK", tonie_header.timestamp,
                                               format_time(tonie_header.timestamp)))
    if not timestamp_ok:
        print("   bitstream serial: 0x{:X}".format(bitstream_serial_no))
    print("[{}] Opus data length: {} bytes (~{:2.0f} kbps)".format("OK" if audio_size_ok else "NOT OK",
                                                                   tonie_header.dataLength,
                                                                   (audio_size * 8) / 1024 / total_time))
    if not audio_size_ok:
        print("     actual: {} bytes".format(audio_size))

    print("[{}] Opus header {}OK || {} channels || {:2.1f} kHz || {} Ogg pages"
          .format("OK" if opus_ok else "NOT OK", "" if opus_head_found and opus_version == 1 else "NOT ",
                  channel_count, sample_rate / 1000, page_count))
    print("[{}] Page alignment {}OK and size {}OK"
          .format("OK" if alignment_okay and page_size_okay else "NOT OK", "" if alignment_okay else "NOT ",
                  "" if page_size_okay else "NOT "))
    print("")
    print("[{}] File is {}valid".format("OK" if all_ok else "NOT OK", "" if all_ok else "NOT "))
    print("")
    
    # Display Opus comments if available
    if opus_comments:
        print("[ii] Opus Comments:")
        if "vendor" in opus_comments:
            print("  Vendor: {}".format(opus_comments["vendor"]))
            # Remove vendor from dict to avoid showing it twice
            vendor = opus_comments.pop("vendor")
            
        # Sort remaining comments for consistent display
        for key in sorted(opus_comments.keys()):
            print("  {}: {}".format(key, opus_comments[key]))
        print("")
        
    print("[ii] Total runtime: {}".format(granule_to_time_string(total_time)))
    print("[ii] {} Tracks:".format(len(chapters)))
    for i in range(0, len(chapters)):
        print("  Track {:02d}: {}".format(i + 1, chapters[i]))
    
    logger.info("File validation complete. Result: %s", "Valid" if all_ok else "Invalid")
    return all_ok


def split_to_opus_files(filename: str, output: str = None) -> None:
    """
    Split a Tonie file into individual Opus files.
    
    Args:
        filename (str): Path to the Tonie file
        output (str | None): Output directory path (optional)
    """
    logger.info("Splitting Tonie file into individual Opus tracks: %s", filename)
    
    with open(filename, "rb") as in_file:
        tonie_header = tonie_header_pb2.TonieHeader()
        header_size = struct.unpack(">L", in_file.read(4))[0]
        logger.debug("Header size: %d bytes", header_size)
        
        tonie_header = tonie_header.FromString(in_file.read(header_size))
        logger.debug("Read Tonie header with %d chapter pages", len(tonie_header.chapterPages))

        abs_path = os.path.abspath(filename)
        if output:
            if not os.path.exists(output):
                logger.debug("Creating output directory: %s", output)
                os.makedirs(output)
            path = output
        else:
            path = os.path.dirname(abs_path)
            
        logger.debug("Output path: %s", path)
        
        name = os.path.basename(abs_path)
        pos = name.rfind('.')
        if pos == -1:
            name = name + ".opus"
        else:
            name = name[:pos] + ".opus"
            
        filename_template = "{{:02d}}_{}".format(name)
        out_path = "{}{}".format(path, os.path.sep)
        logger.debug("Output filename template: %s", out_path + filename_template)

        found = OggPage.seek_to_page_header(in_file)
        if not found:
            logger.error("First OGG page not found")
            raise RuntimeError("First ogg page not found")
            
        first_page = OggPage(in_file)
        logger.debug("Read first OGG page")

        found = OggPage.seek_to_page_header(in_file)
        if not found:
            logger.error("Second OGG page not found")
            raise RuntimeError("Second ogg page not found")
            
        second_page = OggPage(in_file)
        logger.debug("Read second OGG page")

        found = OggPage.seek_to_page_header(in_file)
        page = OggPage(in_file)
        logger.debug("Read third OGG page")

        import math
        
        pad_len = math.ceil(math.log(len(tonie_header.chapterPages) + 1, 10))
        format_string = "[{{:0{}d}}/{:0{}d}] {{}}".format(pad_len, len(tonie_header.chapterPages), pad_len)

        for i in range(0, len(tonie_header.chapterPages)):
            if (i + 1) < len(tonie_header.chapterPages):
                end_page = tonie_header.chapterPages[i + 1]
            else:
                end_page = 0
                
            granule = 0
            output_filename = filename_template.format(i + 1)
            print(format_string.format(i + 1, output_filename))
            logger.info("Creating track %d: %s (end page: %d)", i + 1, out_path + output_filename, end_page)
            
            with open("{}{}".format(out_path, output_filename), "wb") as out_file:
                first_page.write_page(out_file)
                second_page.write_page(out_file)
                page_count = 0
                
                while found and ((page.page_no < end_page) or (end_page == 0)):
                    page.correct_values(granule)
                    granule = page.granule_position
                    page.write_page(out_file)
                    page_count += 1
                    
                    found = OggPage.seek_to_page_header(in_file)
                    if found:
                        page = OggPage(in_file)
                
                logger.debug("Track %d: Wrote %d pages, final granule position: %d", 
                            i + 1, page_count, granule)
        
        logger.info("Successfully split Tonie file into %d individual tracks", len(tonie_header.chapterPages))


def compare_taf_files(file1: str, file2: str, detailed: bool = False) -> bool:
    """
    Compare two .taf files for debugging purposes.
    
    Args:
        file1 (str): Path to the first .taf file
        file2 (str): Path to the second .taf file
        detailed (bool): Whether to show detailed comparison results
        
    Returns:
        bool: True if files are equivalent, False otherwise
    """
    logger.info("Comparing .taf files:")
    logger.info("  File 1: %s", file1)
    logger.info("  File 2: %s", file2)
    
    if not os.path.exists(file1):
        logger.error("File 1 does not exist: %s", file1)
        return False
        
    if not os.path.exists(file2):
        logger.error("File 2 does not exist: %s", file2)
        return False
    
    # Compare file sizes
    size1 = os.path.getsize(file1)
    size2 = os.path.getsize(file2)
    
    if size1 != size2:
        logger.info("Files have different sizes: %d vs %d bytes", size1, size2)
        print("Files have different sizes:")
        print(f"  File 1: {size1} bytes")
        print(f"  File 2: {size2} bytes")
    else:
        logger.info("Files have the same size: %d bytes", size1)
        print(f"Files have the same size: {size1} bytes")
    
    differences = []
    
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        # Read and compare header sizes
        header_size1 = struct.unpack(">L", f1.read(4))[0]
        header_size2 = struct.unpack(">L", f2.read(4))[0]
        
        if header_size1 != header_size2:
            differences.append(f"Header sizes differ: {header_size1} vs {header_size2} bytes")
            logger.info("Header sizes differ: %d vs %d bytes", header_size1, header_size2)
        
        # Read and parse headers
        tonie_header1 = tonie_header_pb2.TonieHeader()
        tonie_header2 = tonie_header_pb2.TonieHeader()
        
        tonie_header1 = tonie_header1.FromString(f1.read(header_size1))
        tonie_header2 = tonie_header2.FromString(f2.read(header_size2))
        
        # Compare timestamps
        if tonie_header1.timestamp != tonie_header2.timestamp:
            differences.append(f"Timestamps differ: {tonie_header1.timestamp} vs {tonie_header2.timestamp}")
            logger.info("Timestamps differ: %d vs %d", tonie_header1.timestamp, tonie_header2.timestamp)
        
        # Compare data lengths
        if tonie_header1.dataLength != tonie_header2.dataLength:
            differences.append(f"Data lengths differ: {tonie_header1.dataLength} vs {tonie_header2.dataLength} bytes")
            logger.info("Data lengths differ: %d vs %d bytes", tonie_header1.dataLength, tonie_header2.dataLength)
        
        # Compare data hashes
        hash1_hex = format_hex(tonie_header1.dataHash)
        hash2_hex = format_hex(tonie_header2.dataHash)
        if tonie_header1.dataHash != tonie_header2.dataHash:
            differences.append(f"Data hashes differ: 0x{hash1_hex} vs 0x{hash2_hex}")
            logger.info("Data hashes differ: 0x%s vs 0x%s", hash1_hex, hash2_hex)
        
        # Compare chapter pages
        ch1 = list(tonie_header1.chapterPages)
        ch2 = list(tonie_header2.chapterPages)
        
        if ch1 != ch2:
            differences.append(f"Chapter pages differ: {ch1} vs {ch2}")
            logger.info("Chapter pages differ: %s vs %s", ch1, ch2)
            
            if len(ch1) != len(ch2):
                differences.append(f"Number of chapters differ: {len(ch1)} vs {len(ch2)}")
                logger.info("Number of chapters differ: %d vs %d", len(ch1), len(ch2))
        
        # Compare audio content
        # Reset file positions to after headers
        f1.seek(4 + header_size1)
        f2.seek(4 + header_size2)
        
        # Compare Ogg pages
        ogg_differences = []
        page_count = 0
        
        # Find first Ogg page in each file
        found1 = OggPage.seek_to_page_header(f1)
        found2 = OggPage.seek_to_page_header(f2)
        
        if not found1 or not found2:
            if not found1:
                differences.append("First file: First OGG page not found")
            if not found2:
                differences.append("Second file: First OGG page not found")
        else:
            # Compare Ogg pages
            while found1 and found2:
                page_count += 1
                page1 = OggPage(f1)
                page2 = OggPage(f2)
                
                # Compare key page attributes
                if page1.serial_no != page2.serial_no:
                    ogg_differences.append(f"Page {page_count}: Serial numbers differ: {page1.serial_no} vs {page2.serial_no}")
                
                if page1.page_no != page2.page_no:
                    ogg_differences.append(f"Page {page_count}: Page numbers differ: {page1.page_no} vs {page2.page_no}")
                
                if page1.granule_position != page2.granule_position:
                    ogg_differences.append(f"Page {page_count}: Granule positions differ: {page1.granule_position} vs {page2.granule_position}")
                
                if page1.get_page_size() != page2.get_page_size():
                    ogg_differences.append(f"Page {page_count}: Page sizes differ: {page1.get_page_size()} vs {page2.get_page_size()}")
                
                # Check for more pages
                found1 = OggPage.seek_to_page_header(f1)
                found2 = OggPage.seek_to_page_header(f2)
            
            # Check if one file has more pages than the other
            if found1 and not found2:
                extra_pages1 = 1
                while OggPage.seek_to_page_header(f1):
                    OggPage(f1)
                    extra_pages1 += 1
                ogg_differences.append(f"File 1 has {extra_pages1} more pages than File 2")
                
            elif found2 and not found1:
                extra_pages2 = 1
                while OggPage.seek_to_page_header(f2):
                    OggPage(f2)
                    extra_pages2 += 1
                ogg_differences.append(f"File 2 has {extra_pages2} more pages than File 1")
        
        # Add Ogg differences to main differences list if detailed flag is set
        if detailed and ogg_differences:
            differences.extend(ogg_differences)
        elif ogg_differences:
            differences.append(f"Found {len(ogg_differences)} differences in Ogg pages")
            logger.info("Found %d differences in Ogg pages", len(ogg_differences))

    # Print summary
    if differences:
        print("\nFiles are different:")
        for diff in differences:
            print(f"  - {diff}")
        logger.info("Files comparison result: Different (%d differences found)", len(differences))
        return False
    else:
        print("\nFiles are equivalent")
        logger.info("Files comparison result: Equivalent")
        return True

def get_header_info_cli(in_file) -> tuple:
    """
    Get header information from a Tonie file.
    
    Args:
        in_file: Input file handle
        
    Returns:
        tuple: Header size, Tonie header object, file size, audio size, SHA1 sum,
               Opus header found flag, Opus version, channel count, sample rate, bitstream serial number,
               Opus comments dictionary, valid flag
               
    Note:
        Instead of raising exceptions, this function returns default values and a valid flag
    """
    logger.debug("Reading Tonie header information")
    
    try:
        tonie_header = tonie_header_pb2.TonieHeader()
        header_size = struct.unpack(">L", in_file.read(4))[0]
        logger.debug("Header size: %d bytes", header_size)
        
        tonie_header = tonie_header.FromString(in_file.read(header_size))
        logger.debug("Read Tonie header with %d chapter pages", len(tonie_header.chapterPages))

        sha1sum = hashlib.sha1(in_file.read())
        logger.debug("Calculated SHA1: %s", sha1sum.hexdigest())

        file_size = in_file.tell()
        in_file.seek(4 + header_size)
        audio_size = file_size - in_file.tell()
        logger.debug("File size: %d bytes, Audio size: %d bytes", file_size, audio_size)

        found = OggPage.seek_to_page_header(in_file)
        if not found:
            logger.error("First OGG page not found")
            return (header_size, tonie_header, file_size, audio_size, sha1sum,
                    False, 0, 0, 0, 0, {}, False)
        
        first_page = OggPage(in_file)
        logger.debug("Read first OGG page")

        unpacked = struct.unpack("<8sBBHLH", first_page.segments[0].data[0:18])
        opus_head_found = unpacked[0] == b"OpusHead"
        opus_version = unpacked[1]
        channel_count = unpacked[2]
        sample_rate = unpacked[4]
        bitstream_serial_no = first_page.serial_no
        
        logger.debug("Opus header found: %s, Version: %d, Channels: %d, Sample rate: %d Hz, Serial: %d", 
                    opus_head_found, opus_version, channel_count, sample_rate, bitstream_serial_no)
        opus_comments = {}
        found = OggPage.seek_to_page_header(in_file)
        if not found:
            logger.error("Second OGG page not found")
            return (header_size, tonie_header, file_size, audio_size, sha1sum,
                   opus_head_found, opus_version, channel_count, sample_rate, bitstream_serial_no, {}, False)
        
        second_page = OggPage(in_file)
        logger.debug("Read second OGG page")
        
        try:
            comment_data = bytearray()
            for segment in second_page.segments:
                comment_data.extend(segment.data)
            
            if comment_data.startswith(b"OpusTags"):
                pos = 8  # Skip "OpusTags"
                # Extract vendor string
                if pos + 4 <= len(comment_data):
                    vendor_length = struct.unpack("<I", comment_data[pos:pos+4])[0]
                    pos += 4
                    if pos + vendor_length <= len(comment_data):
                        vendor = comment_data[pos:pos+vendor_length].decode('utf-8', errors='replace')
                        opus_comments["vendor"] = vendor
                        pos += vendor_length
                        
                        # Extract comments count
                        if pos + 4 <= len(comment_data):
                            comments_count = struct.unpack("<I", comment_data[pos:pos+4])[0]
                            pos += 4
                            
                            # Extract individual comments
                            for i in range(comments_count):
                                if pos + 4 <= len(comment_data):
                                    comment_length = struct.unpack("<I", comment_data[pos:pos+4])[0]
                                    pos += 4
                                    if pos + comment_length <= len(comment_data):
                                        comment = comment_data[pos:pos+comment_length].decode('utf-8', errors='replace')
                                        pos += comment_length
                                        
                                        # Split comment into key/value if possible
                                        if "=" in comment:
                                            key, value = comment.split("=", 1)
                                            opus_comments[key] = value
                                        else:
                                            opus_comments[f"comment_{i}"] = comment
                                    else:
                                        break
                                else:
                                    break
        except Exception as e:
            logger.error("Failed to parse Opus comments: %s", str(e))

        return (
            header_size, tonie_header, file_size, audio_size, sha1sum,
            opus_head_found, opus_version, channel_count, sample_rate, bitstream_serial_no,
            opus_comments, True
        )
    except Exception as e:
        logger.error("Error processing Tonie file: %s", str(e))
        # Return default values with valid=False
        return (0, tonie_header_pb2.TonieHeader(), 0, 0, None, False, 0, 0, 0, 0, {}, False)


def check_tonie_file_cli(filename: str) -> bool:
    """
    Check if a file is a valid Tonie file
    
    Args:
        filename (str): Path to the file to check
        
    Returns:
        bool: True if the file is valid, False otherwise
    """
    logger.info("Checking Tonie file: %s", filename)
    
    try:
        with open(filename, "rb") as in_file:
            header_size, tonie_header, file_size, audio_size, sha1, opus_head_found, \
            opus_version, channel_count, sample_rate, bitstream_serial_no, opus_comments, valid = get_header_info_cli(in_file)

            if not valid:
                logger.error("Invalid Tonie file: %s", filename)
                return False

            try:
                page_count, alignment_okay, page_size_okay, total_time, \
                chapters = get_audio_info(in_file, sample_rate, tonie_header, header_size)
            except Exception as e:
                logger.error("Error analyzing audio data: %s", str(e))
                return False

        hash_ok = tonie_header.dataHash == sha1.digest()
        timestamp_ok = tonie_header.timestamp == bitstream_serial_no
        audio_size_ok = tonie_header.dataLength == audio_size
        opus_ok = opus_head_found and \
                opus_version == 1 and \
                (sample_rate == 48000 or sample_rate == 44100) and \
                channel_count == 2

        all_ok = hash_ok and \
                timestamp_ok and \
                opus_ok and \
                alignment_okay and \
                page_size_okay

        logger.debug("Validation results:")
        logger.debug("  Hash OK: %s", hash_ok)
        logger.debug("  Timestamp OK: %s", timestamp_ok)
        logger.debug("  Audio size OK: %s", audio_size_ok)
        logger.debug("  Opus OK: %s", opus_ok)
        logger.debug("  Alignment OK: %s", alignment_okay)
        logger.debug("  Page size OK: %s", page_size_okay)
        logger.debug("  All OK: %s", all_ok)

        return all_ok
    except Exception as e:
        logger.error("Error checking Tonie file: %s", str(e))
        return False