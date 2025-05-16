#!/usr/bin/python3
"""
Classes and functions for handling Opus audio packets
"""

import struct
from .constants import SAMPLE_RATE_KHZ
from .logger import get_logger

logger = get_logger(__name__)


class OpusPacket:
    """
    Represents an Opus audio packet in an Ogg container.
    
    This class provides methods to parse, modify, and write Opus packets,
    with particular focus on features needed for Tonie compatibility.
    """
    
    def __init__(self, filehandle, size: int = -1, last_size: int = -1, dont_parse_info: bool = False) -> None:
        """
        Initialize a new OpusPacket.
        
        Args:
            filehandle: File handle to read the packet data from, or None to create an empty packet
            size (int): Size of the packet in bytes
            last_size (int): Size of the previous packet in bytes
            dont_parse_info (bool): If True, don't parse the packet information even if this is a first packet
        """
        self.config_value = None
        self.stereo = None
        self.framepacking = None
        self.padding = None
        self.frame_count = None
        self.frame_size = None
        self.granule = None

        if filehandle is None:
            logger.trace("Creating empty opus packet")
            return
            
        self.size = size
        self.data = filehandle.read(self.size)
        self.spanning_packet = size == 255
        self.first_packet = last_size != 255
        
        logger.trace("Created opus packet: size=%d, spanning=%s, first=%s", 
                   self.size, self.spanning_packet, self.first_packet)

        if self.first_packet and not dont_parse_info:
            self.parse_segment_info()

    def get_frame_count(self) -> int:
        """
        Get the number of frames in this packet based on its framepacking.
        
        Returns:
            int: Number of frames in the packet
        """
        if self.framepacking == 0:
            return 1
        elif self.framepacking == 1:
            return 2
        elif self.framepacking == 2:
            return 2
        elif self.framepacking == 3:
            unpacked = struct.unpack("<B", self.data[1:2])
            return unpacked[0] & 63

    def get_padding(self) -> int:
        """
        Get the padding count for this packet.
        
        Returns:
            int: Number of padding bytes
        """
        if self.framepacking != 3:
            return 0
            
        unpacked = struct.unpack("<BB", self.data[1:3])
        is_padded = (unpacked[0] >> 6) & 1
        if not is_padded:
            return 0

        padding = unpacked[1]
        total_padding = padding
        i = 3
        while padding == 255:
            padding = struct.unpack("<B", self.data[i:i + 1])
            total_padding = total_padding + padding[0] - 1
            i = i + 1
            
        logger.trace("Packet has %d bytes of padding", total_padding)
        return total_padding

    def get_frame_size(self) -> float:
        """
        Get the frame size in milliseconds based on the config value.
        
        Returns:
            float: Frame size in milliseconds
            
        Raises:
            RuntimeError: If the config value indicates a non-CELT encoding
        """
        if self.config_value in [16, 20, 24, 28]:
            return 2.5
        elif self.config_value in [17, 21, 25, 29]:
            return 5
        elif self.config_value in [18, 22, 26, 30]:
            return 10
        elif self.config_value in [19, 23, 27, 31]:
            return 20
        else:
            error_msg = (
                "Found config value {} in opus packet, but CELT-only encodings (16-31) are required by the box.\n"
                "Please encode your input files accordingly or fix your encoding pipeline to do so.\n"
                "Did you built libopus with custom modes support?".format(self.config_value)
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def calc_granule(self) -> float:
        """
        Calculate the granule position for this packet.
        
        Returns:
            float: Granule position
        """
        granule = self.frame_size * self.frame_count * SAMPLE_RATE_KHZ
        logger.trace("Calculated granule: %f (frame_size=%f, frame_count=%d)", 
                   granule, self.frame_size, self.frame_count)
        return granule

    def parse_segment_info(self) -> None:
        """Parse the segment information from the packet data."""
        logger.trace("Parsing segment info from packet data")
        byte = struct.unpack("<B", self.data[0:1])[0]
        self.config_value = byte >> 3
        self.stereo = (byte & 4) >> 2
        self.framepacking = byte & 3
        self.padding = self.get_padding()
        self.frame_count = self.get_frame_count()
        self.frame_size = self.get_frame_size()
        self.granule = self.calc_granule()
        
        logger.trace("Packet info: config=%d, stereo=%d, framepacking=%d, frame_count=%d, frame_size=%f",
                   self.config_value, self.stereo, self.framepacking, self.frame_count, self.frame_size)

    def write(self, filehandle) -> None:
        """
        Write the packet data to a file.
        
        Args:
            filehandle: File handle to write the data to
        """
        if len(self.data):
            logger.trace("Writing %d bytes of packet data to file", len(self.data))
            filehandle.write(self.data)

    def convert_to_framepacking_three(self) -> None:
        """
        Convert the packet to use framepacking mode 3.
        
        This is needed for proper padding in Tonie files.
        """
        if self.framepacking == 3:
            logger.trace("Packet already uses framepacking mode 3, no conversion needed")
            return

        logger.debug("Converting packet from framepacking mode %d to mode 3", self.framepacking)
        toc_byte = struct.unpack("<B", self.data[0:1])[0]
        toc_byte = toc_byte | 0b11

        frame_count_byte = self.frame_count
        if self.framepacking == 2:
            frame_count_byte = frame_count_byte | 0b10000000  # vbr
            logger.trace("Setting VBR flag in frame count byte")

        self.data = struct.pack("<BB", toc_byte, frame_count_byte) + self.data[1:]
        self.framepacking = 3
        logger.debug("Packet successfully converted to framepacking mode 3")

    def set_pad_count(self, count: int) -> None:
        """
        Set the padding count for this packet.
        
        Args:
            count (int): Number of padding bytes to add
            
        Raises:
            AssertionError: If the packet is not using framepacking mode 3 or is already padded
        """
        logger.debug("Setting padding count to %d bytes", count)
        
        if self.framepacking != 3:
            logger.error("Cannot set padding on a packet with framepacking mode %d", self.framepacking)
        assert self.framepacking == 3, "Only code 3 packets can contain padding!"
        
        if self.padding != 0:
            logger.error("Packet already has %d bytes of padding", self.padding)
        assert self.padding == 0, "Packet already padded. Not supported yet!"

        frame_count_byte = struct.unpack("<B", self.data[1:2])[0]
        frame_count_byte = frame_count_byte | 0b01000000
        logger.trace("Setting padding flag in frame count byte")

        pad_count_data = bytes()
        val = count
        while val > 254:
            pad_count_data = pad_count_data + b"\xFF"
            val = val - 254
            logger.trace("Added padding byte 0xFF (254 bytes)")
        pad_count_data = pad_count_data + struct.pack("<B", val)
        logger.trace("Added final padding byte %d", val)

        self.data = self.data[0:1] + struct.pack("<B", frame_count_byte) + pad_count_data + self.data[2:]
        logger.debug("Padding count set successfully, new data length: %d bytes", len(self.data))