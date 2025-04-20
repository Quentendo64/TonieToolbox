#!/usr/bin/python3
"""
Main entry point for the TonieToolbox package.
"""

import argparse
import os
import sys
import logging

from . import __version__
from .audio_conversion import get_input_files, append_to_filename
from .tonie_file import create_tonie_file
from .tonie_analysis import check_tonie_file, split_to_opus_files
from .dependency_manager import get_ffmpeg_binary, get_opus_binary
from .logger import setup_logging, get_logger
from .filename_generator import guess_output_filename
from .version_handler import check_for_updates, clear_version_cache

def main():
    """Entry point for the TonieToolbox application."""
    parser = argparse.ArgumentParser(description='Create Tonie compatible file from Ogg opus file(s).')
    parser.add_argument('--version', action='version', version=f'TonieToolbox {__version__}',
                        help='show program version and exit')
    parser.add_argument('input_filename', metavar='SOURCE', type=str, 
                        help='input file or directory or a file list (.lst)')
    parser.add_argument('output_filename', metavar='TARGET', nargs='?', type=str,
                        help='the output file name (default: ---ID---)')
    parser.add_argument('--ts', dest='user_timestamp', metavar='TIMESTAMP', action='store',
                        help='set custom timestamp / bitstream serial')

    parser.add_argument('--ffmpeg', help='specify location of ffmpeg', default=None)
    parser.add_argument('--opusenc', help='specify location of opusenc', default=None)
    parser.add_argument('--bitrate', type=int, help='set encoding bitrate in kbps (default: 96)', default=96)
    parser.add_argument('--cbr', action='store_true', help='encode in cbr mode')
    parser.add_argument('--append-tonie-tag', metavar='TAG', action='store',
                        help='append [TAG] to filename (must be an 8-character hex value)')
    parser.add_argument('--no-tonie-header', action='store_true', help='do not write Tonie header')
    parser.add_argument('--info', action='store_true', help='Check and display info about Tonie file')
    parser.add_argument('--split', action='store_true', help='Split Tonie file into opus tracks')
    parser.add_argument('--auto-download', action='store_true', help='Automatically download FFmpeg and opusenc if needed')
    parser.add_argument('--keep-temp', action='store_true', 
                       help='Keep temporary opus files in a temp folder for testing')
    parser.add_argument('--compare', action='store', metavar='FILE2', 
                       help='Compare input file with another .taf file for debugging')
    parser.add_argument('--detailed-compare', action='store_true',
                       help='Show detailed OGG page differences when comparing files')
    
    # Version check options
    version_group = parser.add_argument_group('Version Check Options')
    version_group.add_argument('--skip-update-check', action='store_true',
                       help='Skip checking for updates')
    version_group.add_argument('--force-refresh-cache', action='store_true',
                       help='Force refresh of update information from PyPI')
    version_group.add_argument('--clear-version-cache', action='store_true',
                       help='Clear cached version information')
    
    log_group = parser.add_argument_group('Logging Options')
    log_level_group = log_group.add_mutually_exclusive_group()
    log_level_group.add_argument('--debug', action='store_true', help='Enable debug logging')
    log_level_group.add_argument('--trace', action='store_true', help='Enable trace logging (very verbose)')
    log_level_group.add_argument('--quiet', action='store_true', help='Show only warnings and errors')
    log_level_group.add_argument('--silent', action='store_true', help='Show only errors')

    args = parser.parse_args()
    if args.trace:
        from .logger import TRACE
        log_level = TRACE
    elif args.debug:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    elif args.silent:
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    setup_logging(log_level)
    logger = get_logger('main')
    logger.debug("Starting TonieToolbox v%s with log level: %s", __version__, logging.getLevelName(log_level))
    
    # Handle version cache operations
    if args.clear_version_cache:
        if clear_version_cache():
            logger.info("Version cache cleared successfully")
        else:
            logger.info("No version cache to clear or error clearing cache")
    
    # Check for updates
    if not args.skip_update_check:
        logger.debug("Checking for updates (force_refresh=%s)", args.force_refresh_cache)
        check_for_updates(
            quiet=args.silent or args.quiet,
            force_refresh=args.force_refresh_cache
        )

    ffmpeg_binary = args.ffmpeg
    if ffmpeg_binary is None:
        ffmpeg_binary = get_ffmpeg_binary(args.auto_download)
        if ffmpeg_binary is None:
            logger.error("Could not find FFmpeg. Please install FFmpeg or specify its location using --ffmpeg or use --auto-download")
            sys.exit(1)
        logger.debug("Using FFmpeg binary: %s", ffmpeg_binary)

    opus_binary = args.opusenc
    if opus_binary is None:
        opus_binary = get_opus_binary(args.auto_download) 
        if opus_binary is None:
            logger.error("Could not find opusenc. Please install opus-tools or specify its location using --opusenc or use --auto-download")
            sys.exit(1)
        logger.debug("Using opusenc binary: %s", opus_binary)

    if os.path.isdir(args.input_filename):
        logger.debug("Input is a directory: %s", args.input_filename)
        args.input_filename += "/*"
    else:
        logger.debug("Input is a file: %s", args.input_filename)
        if args.info:
            logger.info("Checking Tonie file: %s", args.input_filename)
            ok = check_tonie_file(args.input_filename)
            sys.exit(0 if ok else 1)
        elif args.split:
            logger.info("Splitting Tonie file: %s", args.input_filename)
            split_to_opus_files(args.input_filename, args.output_filename)
            sys.exit(0)
        elif args.compare:
            from .tonie_analysis import compare_taf_files
            logger.info("Comparing Tonie files: %s and %s", args.input_filename, args.compare)
            result = compare_taf_files(args.input_filename, args.compare, args.detailed_compare)
            sys.exit(0 if result else 1)

    files = get_input_files(args.input_filename)
    logger.debug("Found %d files to process", len(files))

    if len(files) == 0:
        logger.error("No files found for pattern %s", args.input_filename)
        sys.exit(1)

    if args.output_filename:
        out_filename = args.output_filename
    else:
        guessed_name = guess_output_filename(args.input_filename, files)    
        output_dir = './output'
        if not os.path.exists(output_dir):
            logger.debug("Creating default output directory: %s", output_dir)
            os.makedirs(output_dir, exist_ok=True)
        out_filename = os.path.join(output_dir, guessed_name)
        logger.debug("Using default output location: %s", out_filename)

    if args.append_tonie_tag:
        logger.debug("Appending Tonie tag to output filename")
        hex_tag = args.append_tonie_tag
        logger.debug("Validating tag: %s", hex_tag)
        if not all(c in '0123456789abcdefABCDEF' for c in hex_tag) or len(hex_tag) != 8:
            logger.error("TAG must be an 8-character hexadecimal value")
            sys.exit(1)
        logger.debug("Appending [%s] to output filename", hex_tag)
        out_filename = append_to_filename(out_filename, hex_tag)
    
    if not out_filename.lower().endswith('.taf'):
        out_filename += '.taf'

    logger.info("Creating Tonie file: %s with %d input file(s)", out_filename, len(files))
    create_tonie_file(out_filename, files, args.no_tonie_header, args.user_timestamp,
                     args.bitrate, not args.cbr, ffmpeg_binary, opus_binary, args.keep_temp, args.auto_download)
    logger.info("Successfully created Tonie file: %s", out_filename)


if __name__ == "__main__":
    main()