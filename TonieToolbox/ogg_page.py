#!/usr/bin/python3
"""
Classes and functions for handling OGG container pages
"""

import struct
import math

from .opus_packet import OpusPacket
from .constants import (
    ONLY_CONVERT_FRAMEPACKING,
    OTHER_PACKET_NEEDED,
    DO_NOTHING,
    TOO_MANY_SEGMENTS
)
from .logger import get_logger

logger = get_logger(__name__)


def create_crc_table() -> list[int]:
    """
    Create a CRC lookup table for OGG page checksums.
    
    Returns:
        list[int]: CRC32 lookup table for OGG pages
    """
    logger.debug("Creating CRC table for OGG page checksums")
    table = []
    for i in range(256):
        k = i << 24
        for _ in range(8):
            k = (k << 1) ^ 0x04c11db7 if k & 0x80000000 else k << 1
        table.append(k & 0xffffffff)
    return table


# Global CRC table for OGG checksums
CRC_TABLE = create_crc_table()


def crc32(bytestream: bytes) -> int:
    """
    Calculate a CRC32 checksum for the given bytestream.
    
    Args:
        bytestream (bytes): Bytes to calculate the CRC for
        
    Returns:
        int: CRC32 checksum
    """
    crc = 0
    for byte in bytestream:
        lookup_index = ((crc >> 24) ^ byte) & 0xff
        crc = ((crc & 0xffffff) << 8) ^ CRC_TABLE[lookup_index]
    return crc


class OggPage:
    """
    Represents an OGG container page.
    
    This class provides methods to parse, modify, and write OGG pages,
    with particular focus on features needed for Tonie compatibility.
    """
    
    def __init__(self, filehandle) -> None:
        """
        Initialize a new OggPage.
        
        Args:
            filehandle: File handle to read the page data from, or None to create an empty page
        """
        self.version = None
        self.page_type = None
        self.granule_position = None
        self.serial_no = None
        self.page_no = None
        self.checksum = None
        self.segment_count = None
        self.segments = None

        if filehandle is None:
            logger.trace("Creating empty OggPage")
            return
            
        logger.trace("Initializing OggPage from file handle")
        self.parse_header(filehandle)
        self.parse_segments(filehandle)

    def parse_header(self, filehandle) -> None:
        """
        Parse the OGG page header.
        
        Args:
            filehandle: File handle to read the header from
        """
        header = filehandle.read(27)
        unpacked = struct.unpack("<BBQLLLB", header[4:27])
        self.version = unpacked[0]
        self.page_type = unpacked[1]
        self.granule_position = unpacked[2]
        self.serial_no = unpacked[3]
        self.page_no = unpacked[4]
        self.checksum = unpacked[5]
        self.segment_count = unpacked[6]
        
        logger.trace("Parsed OGG header - Page #%d, Type: %d, Granule: %d, Serial: %d, Segments: %d",
                   self.page_no, self.page_type, self.granule_position, self.serial_no, self.segment_count)

    def parse_segments(self, filehandle) -> None:
        """
        Parse the segments in this OGG page.
        
        Args:
            filehandle: File handle to read the segments from
            
        Raises:
            RuntimeError: If an opus packet spans multiple OGG pages
        """
        logger.trace("Parsing %d segments in OGG page #%d", self.segment_count, self.page_no)
        table = filehandle.read(self.segment_count)
        self.segments = []
        last_length = -1
        dont_parse_info = (self.page_no == 0) or (self.page_no == 1)

        for length in table:
            segment = OpusPacket(filehandle, length, last_length, dont_parse_info)
            last_length = length
            self.segments.append(segment)

        if self.segments and self.segments[len(self.segments) - 1].spanning_packet:
            logger.error("Found an opus packet spanning OGG pages, which is not supported")
            raise RuntimeError("Found an opus packet spanning ogg pages. This is not supported yet.")

    def correct_values(self, last_granule: int) -> None:
        """
        Correct the granule position and checksum for this page.
        
        Args:
            last_granule (int): Last granule position
            
        Raises:
            RuntimeError: If there are too many segments in the page
        """
        if len(self.segments) > 255:
            logger.error("Too many segments in page: %d (max 255 allowed)", len(self.segments))
            raise RuntimeError(f"Too many segments: {len(self.segments)} - max 255 allowed")
            
        granule = 0
        if not (self.page_no == 0) and not (self.page_no == 1):
            for segment in self.segments:
                if segment.first_packet:
                    granule = granule + segment.granule
                    
        self.granule_position = last_granule + granule
        self.segment_count = len(self.segments)
        self.checksum = self.calc_checksum()
        
        logger.trace("Corrected OGG page values: Page #%d, Segments: %d, Granule: %d", 
                   self.page_no, self.segment_count, self.granule_position)

    def calc_checksum(self) -> int:
        """
        Calculate the checksum for this page.
        
        Returns:
            int: CRC32 checksum
        """
        data = b"OggS" + struct.pack("<BBQLLLB", self.version, self.page_type, self.granule_position, self.serial_no,
                                     self.page_no, 0, self.segment_count)
        for segment in self.segments:
            data = data + struct.pack("<B", segment.size)
        for segment in self.segments:
            data = data + segment.data

        checksum = crc32(data)
        logger.trace("Calculated checksum for page #%d: 0x%X", self.page_no, checksum)
        return checksum

    def get_page_size(self) -> int:
        """
        Get the total size of this page in bytes.
        
        Returns:
            int: Page size in bytes
        """
        size = 27 + len(self.segments)
        for segment in self.segments:
            size = size + len(segment.data)
        return size

    def get_size_of_first_opus_packet(self) -> int:
        """
        Get the size of the first opus packet in bytes.
        
        Returns:
            int: Size of first opus packet in bytes
        """
        if not len(self.segments):
            return 0
        segment_size = self.segments[0].size
        size = segment_size
        i = 1
        while (segment_size == 255) and (i < len(self.segments)):
            segment_size = self.segments[i].size
            size = size + segment_size
            i = i + 1
        return size

    def get_segment_count_of_first_opus_packet(self) -> int:
        """
        Get the number of segments in the first opus packet.
        
        Returns:
            int: Number of segments
        """
        if not len(self.segments):
            return 0
        segment_size = self.segments[0].size
        count = 1
        while (segment_size == 255) and (count < len(self.segments)):
            segment_size = self.segments[count].size
            count = count + 1
        return count

    def insert_empty_segment(self, index_after: int, spanning_packet: bool = False, first_packet: bool = False) -> None:
        """
        Insert an empty segment after the specified index.
        
        Args:
            index_after (int): Index to insert the segment after
            spanning_packet (bool): Whether this segment belongs to a packet that spans pages
            first_packet (bool): Whether this is the first segment of a packet
        """
        logger.trace("Inserting empty segment after index %d (spanning: %s, first: %s)",
                   index_after, spanning_packet, first_packet)
        segment = OpusPacket(None)
        segment.first_packet = first_packet
        segment.spanning_packet = spanning_packet
        segment.size = 0
        segment.data = bytes()
        self.segments.insert(index_after + 1, segment)

    def get_opus_packet_size(self, seg_start: int) -> int:
        """
        Get the size of the opus packet starting at the specified segment index.
        
        Args:
            seg_start (int): Starting segment index
            
        Returns:
            int: Size of the opus packet in bytes
        """
        size = len(self.segments[seg_start].data)
        seg_start = seg_start + 1
        while (seg_start < len(self.segments)) and not self.segments[seg_start].first_packet:
            size = size + self.segments[seg_start].size
            seg_start = seg_start + 1
        return size

    def get_segment_count_of_packet_at(self, seg_start: int) -> int:
        """
        Get the number of segments in the packet starting at the specified segment index.
        
        Args:
            seg_start (int): Starting segment index
            
        Returns:
            int: Number of segments
        """
        seg_end = seg_start + 1
        while (seg_end < len(self.segments)) and not self.segments[seg_end].first_packet:
            seg_end = seg_end + 1
        return seg_end - seg_start

    def redistribute_packet_data_at(self, seg_start: int, pad_count: int) -> None:
        """
        Redistribute packet data starting at the specified segment index.
        
        Args:
            seg_start (int): Starting segment index
            pad_count (int): Number of padding bytes to add
        """
        logger.trace("Redistributing packet data at segment %d with %d padding bytes", 
                   seg_start, pad_count)
        seg_count = self.get_segment_count_of_packet_at(seg_start)
        full_data = bytes()
        for i in range(0, seg_count):
            full_data = full_data + self.segments[seg_start + i].data
        full_data = full_data + bytes(pad_count)
        size = len(full_data)

        if size < 255:
            self.segments[seg_start].size = size
            self.segments[seg_start].data = full_data
            logger.trace("Data fits in a single segment (size: %d)", size)
            return

        needed_seg_count = math.ceil(size / 255)
        if (size % 255) == 0:
            needed_seg_count = needed_seg_count + 1
        segments_to_create = needed_seg_count - seg_count
        
        if segments_to_create > 0:
            logger.trace("Need to create %d new segments", segments_to_create)
            for i in range(0, segments_to_create):
                self.insert_empty_segment(seg_start + seg_count + i, i != (segments_to_create - 1))
            seg_count = needed_seg_count

        for i in range(0, seg_count):
            self.segments[seg_start + i].data = full_data[:255]
            self.segments[seg_start + i].size = len(self.segments[seg_start + i].data)
            full_data = full_data[255:]
            
        logger.trace("Redistribution complete, %d segments used", seg_count)
        assert len(full_data) == 0

    def convert_packet_to_framepacking_three_and_pad(self, seg_start: int, pad: bool = False, count: int = 0) -> None:
        """
        Convert the packet to framepacking three mode and add padding if required.
        
        Args:
            seg_start (int): Starting segment index
            pad (bool): Whether to add padding
            count (int): Number of padding bytes to add
            
        Raises:
            AssertionError: If the segment is not the first packet
        """
        logger.trace("Converting packet at segment %d to framepacking three (pad: %s, count: %d)",
                   seg_start, pad, count)
        assert self.segments[seg_start].first_packet is True
        self.segments[seg_start].convert_to_framepacking_three()
        if pad:
            self.segments[seg_start].set_pad_count(count)
        self.redistribute_packet_data_at(seg_start, count)

    def calc_actual_padding_value(self, seg_start: int, bytes_needed: int) -> int:
        """
        Calculate the actual padding value needed for the packet.
        
        Args:
            seg_start (int): Starting segment index
            bytes_needed (int): Number of bytes needed for padding
            
        Returns:
            int: Actual padding value or a special return code
            
        Raises:
            AssertionError: If bytes_needed is negative
        """
        if bytes_needed < 0:
            logger.error("Page is already too large! Something went wrong. Bytes needed: %d", 
                       bytes_needed)
        assert bytes_needed >= 0, "Page is already too large! Something went wrong."

        seg_end = seg_start + self.get_segment_count_of_packet_at(seg_start)
        size_of_last_segment = self.segments[seg_end - 1].size
        convert_framepacking_needed = self.segments[seg_start].framepacking != 3
        
        logger.trace("Calculating padding for segment %d, bytes needed: %d, last segment size: %d",
                   seg_start, bytes_needed, size_of_last_segment)

        if bytes_needed == 0:
            logger.trace("No padding needed")
            return DO_NOTHING

        if (bytes_needed + size_of_last_segment) % 255 == 0:
            logger.trace("Need another packet (would end exactly on segment boundary)")
            return OTHER_PACKET_NEEDED

        if bytes_needed == 1:
            if convert_framepacking_needed:
                logger.trace("Only need to convert framepacking")
                return ONLY_CONVERT_FRAMEPACKING
            else:
                logger.trace("Already using framepacking three, can pad with 0")
                return 0

        new_segments_needed = 0
        if bytes_needed + size_of_last_segment >= 255:
            tmp_count = bytes_needed + size_of_last_segment - 255
            while tmp_count >= 0:
                tmp_count = tmp_count - 255 - 1
                new_segments_needed = new_segments_needed + 1
            logger.trace("Need %d new segments", new_segments_needed)

        if new_segments_needed + len(self.segments) > 255:
            logger.warning("Too many segments would be needed: %d", 
                         new_segments_needed + len(self.segments))
            return TOO_MANY_SEGMENTS

        if (bytes_needed + size_of_last_segment) % 255 == (new_segments_needed - 1):
            logger.trace("Need another packet (would end with empty segment)")
            return OTHER_PACKET_NEEDED

        packet_bytes_needed = bytes_needed - new_segments_needed
        logger.trace("Packet bytes needed: %d", packet_bytes_needed)

        if packet_bytes_needed == 1:
            if convert_framepacking_needed:
                logger.trace("Need to convert framepacking only")
                return ONLY_CONVERT_FRAMEPACKING
            else:
                logger.trace("Already using framepacking three, can pad with 0")
                return 0

        if convert_framepacking_needed:
            packet_bytes_needed = packet_bytes_needed - 1  # frame_count_byte
            logger.trace("Need to convert framepacking, adjusted bytes needed: %d", 
                       packet_bytes_needed)
            
        packet_bytes_needed = packet_bytes_needed - 1  # padding_count_data is at least 1 byte
        size_of_padding_count_data = max(1, math.ceil(packet_bytes_needed / 254))
        check_size = math.ceil((packet_bytes_needed - size_of_padding_count_data + 1) / 254)
        
        logger.trace("Padding size check: needed=%d, check_size=%d", 
                   size_of_padding_count_data, check_size)

        if check_size != size_of_padding_count_data:
            logger.trace("Need another packet (padding size calculation mismatch)")
            return OTHER_PACKET_NEEDED
        else:
            result = packet_bytes_needed - size_of_padding_count_data + 1
            logger.trace("Calculated actual padding value: %d", result)
            return result

    def pad(self, pad_to: int, idx_offset: int = -1) -> None:
        """
        Pad the page to the specified size.
        
        Args:
            pad_to (int): Target size to pad to
            idx_offset (int): Index offset to start from, defaults to last segment
            
        Raises:
            RuntimeError: If beginning of last packet cannot be found
            AssertionError: If the actual page size after padding does not match the target
        """
        logger.debug("Padding page #%d to size %d (current size: %d)", 
                   self.page_no, pad_to, self.get_page_size())
        
        if idx_offset == -1:
            idx = len(self.segments) - 1
        else:
            idx = idx_offset
        
        logger.trace("Starting from segment index %d", idx)

        while not self.segments[idx].first_packet:
            idx = idx - 1
            if idx < 0:
                logger.error("Could not find beginning of last packet")
                raise RuntimeError("Could not find begin of last packet!")
                
        logger.trace("Found beginning of packet at segment index %d", idx)

        pad_count = pad_to - self.get_page_size()
        logger.trace("Need to add %d bytes of padding", pad_count)
        
        actual_padding = self.calc_actual_padding_value(idx, pad_count)
        logger.trace("Actual padding value: %d", actual_padding)

        if actual_padding == DO_NOTHING:
            logger.debug("No padding needed")
            return
        if actual_padding == ONLY_CONVERT_FRAMEPACKING:
            logger.debug("Only need to convert framepacking")
            self.convert_packet_to_framepacking_three_and_pad(idx)
            return
        if actual_padding == OTHER_PACKET_NEEDED:
            logger.debug("Padding with one byte first, then recalculating")
            self.pad_one_byte()
            self.pad(pad_to)
            return
        if actual_padding == TOO_MANY_SEGMENTS:
            logger.debug("Too many segments would be needed, padding previous packet first")
            self.pad(pad_to - (pad_count // 2), idx - 1)
            self.pad(pad_to)
            return

        logger.debug("Converting packet to framepacking three and adding %d bytes of padding", 
                   actual_padding)
        self.convert_packet_to_framepacking_three_and_pad(idx, True, actual_padding)
        
        final_size = self.get_page_size()
        if final_size != pad_to:
            logger.error("Page size after padding (%d) doesn't match target size (%d)", 
                       final_size, pad_to)
        assert final_size == pad_to

    def pad_one_byte(self) -> None:
        """
        Add one byte of padding to the page.
        
        Raises:
            RuntimeError: If the page seems impossible to pad correctly
        """
        logger.debug("Adding one byte of padding to page #%d", self.page_no)
        i = 0
        while not (self.segments[i].first_packet and not self.segments[i].padding
                   and self.get_opus_packet_size(i) % 255 < 254):
            i = i + 1
            if i >= len(self.segments):
                logger.error("Page seems impossible to pad correctly")
                raise RuntimeError("Page seems impossible to pad correctly")
                
        logger.trace("Found suitable packet at segment index %d", i)

        if self.segments[i].framepacking == 3:
            logger.trace("Packet already has framepacking 3, adding 0 bytes of padding")
            self.convert_packet_to_framepacking_three_and_pad(i, True, 0)
        else:
            logger.trace("Converting packet to framepacking 3")
            self.convert_packet_to_framepacking_three_and_pad(i)

    def write_page(self, filehandle, sha1=None) -> None:
        """
        Write the page to a file handle.
        
        Args:
            filehandle: File handle to write to
            sha1: Optional SHA1 hash object to update with the written data
        """
        logger.trace("Writing OGG page #%d to file (segments: %d)", self.page_no, len(self.segments))
        data = b"OggS" + struct.pack("<BBQLLLB", self.version, self.page_type, self.granule_position, self.serial_no,
                                     self.page_no, self.checksum, self.segment_count)
        for segment in self.segments:
            data = data + struct.pack("<B", segment.size)
        if sha1 is not None:
            sha1.update(data)
        filehandle.write(data)
        for segment in self.segments:
            if sha1 is not None:
                sha1.update(segment.data)
            segment.write(filehandle)

    @staticmethod
    def from_page(other_page: 'OggPage') -> 'OggPage':
        """
        Create a new OggPage based on another page.
        
        Args:
            other_page (OggPage): Source page to copy from
            
        Returns:
            OggPage: New page with copied properties
        """
        logger.trace("Creating new OGG page from existing page #%d", other_page.page_no)
        new_page = OggPage(None)
        new_page.version = other_page.version
        new_page.page_type = other_page.page_type
        new_page.granule_position = other_page.granule_position
        new_page.serial_no = other_page.serial_no
        new_page.page_no = other_page.page_no
        new_page.checksum = 0
        new_page.segment_count = 0
        new_page.segments = []
        return new_page

    @staticmethod
    def seek_to_page_header(filehandle) -> bool:
        """
        Seek to the next OGG page header in a file.
        
        Args:
            filehandle: File handle to seek in
            
        Returns:
            bool: True if a page header was found, False otherwise
        """
        logger.trace("Seeking to next OGG page header in file")
        current_pos = filehandle.tell()
        filehandle.seek(0, 2)
        size = filehandle.tell()
        filehandle.seek(current_pos, 0)
        five_bytes = filehandle.read(5)
        while five_bytes and (filehandle.tell() + 5 < size):
            if five_bytes == b"OggS\x00":
                filehandle.seek(-5, 1)
                logger.trace("Found OGG page header at position %d", filehandle.tell())
                return True
            filehandle.seek(-4, 1)
            five_bytes = filehandle.read(5)
            
        logger.trace("No OGG page header found")
        return False