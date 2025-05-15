## Technical Details

### TAF (Tonie Audio Format) File Structure

The Tonie Audio Format (TAF) consists of several parts:

#### 1. Tonie Header (0x1000 bytes)

Located at the beginning of the file, structured as:

- A 4-byte big-endian integer specifying the header length
- A Protocol Buffer encoded header (defined in `tonie_header.proto`)
- Padding to fill the entire 4096 bytes (0x1000)

The Protocol Buffer structure contains:

```protobuf
message TonieHeader {
  bytes dataHash = 1;      // SHA1 hash of the audio data
  uint32 dataLength = 2;   // Length of the audio data in bytes
  uint32 timestamp = 3;    // Unix timestamp (also used as bitstream serial number)
  repeated uint32 chapterPages = 4 [packed=true];  // Page numbers for chapter starts
  bytes padding = 5;       // Padding to fill up the header
}
```

#### 2. Audio Data

The audio data consists of:

- Opus encoded audio in Ogg container format
- Every page after the header has a fixed size of 4096 bytes (0x1000)
- First page contains the Opus identification header
- Second page contains the Opus comments/tags
- Remaining pages contain the actual audio data
- All pages use the same bitstream serial number (timestamp from header)

#### 3. Special Requirements

For optimal compatibility with Tonie boxes:

- Audio should be stereo (2 channels)
- Sample rate must be 48 kHz
- Pages must be aligned to 4096 byte boundaries
- Bitrate of 96 kbps VBR is recommended

**Mono audio handling:**

- By default, TonieToolbox will automatically convert mono audio files to stereo for compatibility.
- To disable this behavior (and require your input to already be stereo), use the `--no-mono-conversion` flag.

### File Analysis

When using the `--info` flag, TonieToolbox checks and displays detailed information about a .TAF (Tonie Audio File):

- SHA1 hash validation
- Timestamp/bitstream serial consistency
- Opus data length verification
- Opus header validation (version, channels, sample rate)
- Page alignment and size validation
- Total runtime
- Track listing with durations

### File Comparison

When using the `--compare` flag, TonieToolbox provides a detailed comparison of two .TAF files:

- File size comparison
- Header size verification
- Timestamp comparison
- Data length validation
- SHA1 hash verification
- Chapter page structure analysis
- OGG page-by-page comparison (with `--detailed-compare` flag)

This is particularly useful for debugging when creating TAF files with different tools or parameters.
