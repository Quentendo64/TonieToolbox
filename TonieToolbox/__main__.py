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
from .tonie_analysis import check_tonie_file, check_tonie_file_cli, split_to_opus_files
from .dependency_manager import get_ffmpeg_binary, get_opus_binary
from .logger import setup_logging, get_logger
from .filename_generator import guess_output_filename
from .version_handler import check_for_updates, clear_version_cache
from .recursive_processor import process_recursive_folders
from .media_tags import is_available as is_media_tags_available, ensure_mutagen, extract_album_info, format_metadata_filename
from .teddycloud import TeddyCloudClient
from .tags import get_tags
from .tonies_json import fetch_and_update_tonies_json
from .artwork import upload_artwork


def main():
    """Entry point for the TonieToolbox application."""
    parser = argparse.ArgumentParser(description='Create Tonie compatible file from Ogg opus file(s).')
    parser.add_argument('-v', '--version', action='version', version=f'TonieToolbox {__version__}',
                        help='show program version and exit')    
    # ------------- Parser - Teddycloud -------------
    teddycloud_group = parser.add_argument_group('TeddyCloud Options')
    teddycloud_group.add_argument('--upload', metavar='URL', action='store',
                       help='Upload to TeddyCloud instance (e.g., https://teddycloud.example.com). Supports .taf, .jpg, .jpeg, .png files.')
    teddycloud_group.add_argument('--include-artwork', action='store_true',
                       help='Upload cover artwork image alongside the Tonie file when using --upload')
    teddycloud_group.add_argument('--get-tags', action='store', metavar='URL',
                       help='Get available tags from TeddyCloud instance')
    teddycloud_group.add_argument('--ignore-ssl-verify', action='store_true',
                       help='Ignore SSL certificate verification (for self-signed certificates)')
    teddycloud_group.add_argument('--special-folder', action='store', metavar='FOLDER',
                       help='Special folder to upload to (currently only "library" is supported)', default='library')
    teddycloud_group.add_argument('--path', action='store', metavar='PATH',
                       help='Path where to write the file on TeddyCloud server')
    teddycloud_group.add_argument('--connection-timeout', type=int, metavar='SECONDS', default=10,
                       help='Connection timeout in seconds (default: 10)')
    teddycloud_group.add_argument('--read-timeout', type=int, metavar='SECONDS', default=300,
                       help='Read timeout in seconds (default: 300)')
    teddycloud_group.add_argument('--max-retries', type=int, metavar='RETRIES', default=3,
                       help='Maximum number of retry attempts (default: 3)')
    teddycloud_group.add_argument('--retry-delay', type=int, metavar='SECONDS', default=5,
                       help='Delay between retry attempts in seconds (default: 5)')
    teddycloud_group.add_argument('--create-custom-json', action='store_true',
                       help='Fetch and update custom Tonies JSON data')
    # ------------- Parser - Authentication options for TeddyCloud -------------
    teddycloud_group.add_argument('--username', action='store', metavar='USERNAME',
                       help='Username for basic authentication')
    teddycloud_group.add_argument('--password', action='store', metavar='PASSWORD',
                       help='Password for basic authentication')
    teddycloud_group.add_argument('--client-cert', action='store', metavar='CERT_FILE',
                       help='Path to client certificate file for certificate-based authentication')
    teddycloud_group.add_argument('--client-key', action='store', metavar='KEY_FILE',
                       help='Path to client private key file for certificate-based authentication')

    # ------------- Parser - Source Input -------------
    parser.add_argument('input_filename', metavar='SOURCE', type=str, nargs='?',
                        help='input file or directory or a file list (.lst)')
    parser.add_argument('output_filename', metavar='TARGET', nargs='?', type=str,
                        help='the output file name (default: ---ID---)')
    parser.add_argument('-t', '--timestamp', dest='user_timestamp', metavar='TIMESTAMP', action='store',
                        help='set custom timestamp / bitstream serial')
    # ------------- Parser - Librarys -------------
    parser.add_argument('-f', '--ffmpeg', help='specify location of ffmpeg', default=None)
    parser.add_argument('-o', '--opusenc', help='specify location of opusenc', default=None)
    parser.add_argument('-b', '--bitrate', type=int, help='set encoding bitrate in kbps (default: 96)', default=96)
    parser.add_argument('-c', '--cbr', action='store_true', help='encode in cbr mode')
    parser.add_argument('--auto-download', action='store_true',
                        help='automatically download ffmpeg and opusenc if not found')
    # ------------- Parser - TAF -------------
    parser.add_argument('-a', '--append-tonie-tag', metavar='TAG', action='store',
                        help='append [TAG] to filename (must be an 8-character hex value)')
    parser.add_argument('-n', '--no-tonie-header', action='store_true', help='do not write Tonie header')
    parser.add_argument('-i', '--info', action='store_true', help='Check and display info about Tonie file')
    parser.add_argument('-s', '--split', action='store_true', help='Split Tonie file into opus tracks')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process folders recursively')
    parser.add_argument('-O', '--output-to-source', action='store_true', 
                        help='Save output files in the source directory instead of output directory')
    parser.add_argument('-fc', '--force-creation', action='store_true', default=False,
                        help='Force creation of Tonie file even if it already exists')
    # ------------- Parser - Debug TAFs -------------
    parser.add_argument('-k', '--keep-temp', action='store_true', 
                       help='Keep temporary opus files in a temp folder for testing')
    parser.add_argument('-u', '--use-legacy-tags', action='store_true',
                       help='Use legacy hardcoded tags instead of dynamic TonieToolbox tags')
    parser.add_argument('-C', '--compare', action='store', metavar='FILE2', 
                       help='Compare input file with another .taf file for debugging')
    parser.add_argument('-D', '--detailed-compare', action='store_true',
                       help='Show detailed OGG page differences when comparing files')    
    # ------------- Parser - Media Tag Options -------------
    media_tag_group = parser.add_argument_group('Media Tag Options')
    media_tag_group.add_argument('-m', '--use-media-tags', action='store_true',
                       help='Use media tags from audio files for naming')
    media_tag_group.add_argument('--name-template', metavar='TEMPLATE', action='store',
                       help='Template for naming files using media tags. Example: "{album} - {artist}"')
    media_tag_group.add_argument('--show-tags', action='store_true',
                       help='Show available media tags from input files')
    # ------------- Parser - Version handling -------------
    version_group = parser.add_argument_group('Version Check Options')
    version_group.add_argument('-S', '--skip-update-check', action='store_true',
                       help='Skip checking for updates')
    version_group.add_argument('-F', '--force-refresh-cache', action='store_true',
                       help='Force refresh of update information from PyPI')
    version_group.add_argument('-X', '--clear-version-cache', action='store_true',
                       help='Clear cached version information')
    # ------------- Parser - Logging -------------
    log_group = parser.add_argument_group('Logging Options')
    log_level_group = log_group.add_mutually_exclusive_group()
    log_level_group.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    log_level_group.add_argument('-T', '--trace', action='store_true', help='Enable trace logging (very verbose)')
    log_level_group.add_argument('-q', '--quiet', action='store_true', help='Show only warnings and errors')
    log_level_group.add_argument('-Q', '--silent', action='store_true', help='Show only errors')
    log_group.add_argument('--log-file', action='store_true', default=False,
                       help='Save logs to a timestamped file in .tonietoolbox folder')
    args = parser.parse_args()
    
    # ------------- Parser - Source Input -------------
    if args.input_filename is None and not (args.get_tags or args.upload):
        parser.error("the following arguments are required: SOURCE")

    # ------------- Logging -------------
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
    setup_logging(log_level, log_to_file=args.log_file)
    logger = get_logger('main')
    logger.debug("Starting TonieToolbox v%s with log level: %s", __version__, logging.getLevelName(log_level))
    logger.debug("Command-line arguments: %s", vars(args))

    # ------------- Version handling -------------
    if args.clear_version_cache:
        logger.debug("Clearing version cache")
        if clear_version_cache():
            logger.info("Version cache cleared successfully")
        else:
            logger.info("No version cache to clear or error clearing cache")
    
    if not args.skip_update_check:
        logger.debug("Checking for updates (force_refresh=%s)", args.force_refresh_cache)
        is_latest, latest_version, message, update_confirmed = check_for_updates(
            quiet=args.silent or args.quiet,
            force_refresh=args.force_refresh_cache
        )
        
        logger.debug( "Update check results: is_latest=%s, latest_version=%s, update_confirmed=%s", 
                   is_latest, latest_version, update_confirmed)
        
        if not is_latest and not update_confirmed and not (args.silent or args.quiet):
            logger.info("Update available but user chose to continue without updating.")

        # ------------- Normalize Path Input -------------
    if args.input_filename:
        logger.debug("Original input path: %s", args.input_filename)
        # Strip quotes from the beginning and end
        args.input_filename = args.input_filename.strip('"\'')
        # Handle paths that end with a backslash
        if args.input_filename.endswith('\\'):
            args.input_filename = args.input_filename.rstrip('\\')
        logger.debug("Normalized input path: %s", args.input_filename)

        # ------------- Setup TeddyCloudClient-------------
    if args.upload or args.get_tags:
        if args.upload:
            teddycloud_url = args.upload
        elif args.get_tags:
            teddycloud_url = args.get_tags        
        if not teddycloud_url:
            logger.error("TeddyCloud URL is required for --upload or --get-tags")
            sys.exit(1)
        try:
            client = TeddyCloudClient(
                base_url=teddycloud_url,
                ignore_ssl_verify=args.ignore_ssl_verify,
                username=args.username,
                password=args.password,
                cert_file=args.client_cert,                
                key_file=args.client_key
            )
            logger.debug("TeddyCloud client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize TeddyCloud client: %s", str(e))
            sys.exit(1)

        if args.get_tags:
            logger.debug("Getting tags from TeddyCloud: %s", teddycloud_url)
            success = get_tags(client)
            logger.debug( "Exiting with code %d", 0 if success else 1)
            sys.exit(0 if success else 1)
            
    # ------------- Direct Upload -------------
        if args.upload and not args.recursive:
            logger.debug("Upload to TeddyCloud requested: %s", teddycloud_url)
            logger.trace("TeddyCloud upload parameters: path=%s, special_folder=%s, ignore_ssl=%s", 
                      args.path, args.special_folder, args.ignore_ssl_verify)

            if not args.input_filename:
                logger.error("Missing input file for --upload. Provide a file path as SOURCE argument.")
                logger.trace("Exiting with code 1 due to missing input file")
                sys.exit(1)

            if os.path.exists(args.input_filename) and os.path.isfile(args.input_filename):
                file_path = args.input_filename
                file_size = os.path.getsize(file_path)
                file_ext = os.path.splitext(file_path)[1].lower()
                
                logger.debug("File to upload: %s (size: %d bytes, type: %s)", 
                          file_path, file_size, file_ext)
                logger.info("Uploading %s to TeddyCloud %s", file_path, teddycloud_url)
                
                logger.trace("Starting upload process for %s", file_path)
                response = client.upload_file(
                    destination_path=args.path, 
                    file_path=file_path,                   
                    special=args.special_folder,
                )
                logger.trace("Upload response received: %s", response)
                
                upload_success = response.get('success', False)
                if not upload_success:
                    error_msg = response.get('message', 'Unknown error')
                    logger.error("Failed to upload %s to TeddyCloud: %s", file_path, error_msg)
                    logger.trace("Exiting with code 1 due to upload failure")
                    sys.exit(1)
                else:
                    logger.info("Successfully uploaded %s to TeddyCloud", file_path)
                    logger.debug("Upload response details: %s", 
                              {k: v for k, v in response.items() if k != 'success'})
                
                artwork_url = None
                if args.include_artwork and file_path.lower().endswith('.taf'):
                    source_dir = os.path.dirname(file_path)
                    logger.info("Looking for artwork to upload for %s", file_path)
                    logger.debug("Searching for artwork in directory: %s", source_dir)
                    
                    logger.trace("Calling upload_artwork function")
                    success, artwork_url = upload_artwork(client, file_path, source_dir, [])
                    logger.trace("upload_artwork returned: success=%s, artwork_url=%s", 
                              success, artwork_url)
                    
                    if success:
                        logger.info("Successfully uploaded artwork for %s", file_path)
                        logger.debug("Artwork URL: %s", artwork_url)
                    else:
                        logger.warning("Failed to upload artwork for %s", file_path)
                        logger.debug("No suitable artwork found or upload failed")
                
                if args.create_custom_json and file_path.lower().endswith('.taf'):
                    output_dir = './output'
                    logger.debug("Creating/ensuring output directory for JSON: %s", output_dir)
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir, exist_ok=True)
                        logger.trace("Created output directory: %s", output_dir)

                    logger.debug("Updating tonies.custom.json with: taf=%s, artwork_url=%s", 
                              file_path, artwork_url)
                    success = fetch_and_update_tonies_json(client, file_path, [], artwork_url, output_dir)
                    if success:
                        logger.info("Successfully updated Tonies JSON for %s", file_path)
                    else:
                        logger.warning("Failed to update Tonies JSON for %s", file_path)
                        logger.debug("fetch_and_update_tonies_json returned failure")
                
                logger.trace("Exiting after direct upload with code 0")
                sys.exit(0)
            elif not args.recursive:
                logger.error("File not found or not a regular file: %s", args.input_filename)
                logger.debug("File exists: %s, Is file: %s", 
                          os.path.exists(args.input_filename), 
                          os.path.isfile(args.input_filename) if os.path.exists(args.input_filename) else False)
                logger.trace("Exiting with code 1 due to invalid input file")
                sys.exit(1)
        
        if args.recursive and args.upload:
            logger.info("Recursive mode with upload enabled: %s -> %s", args.input_filename, teddycloud_url)
            logger.debug("Will process all files in directory recursively and upload to TeddyCloud")
    
    # ------------- Librarys / Prereqs -------------
    logger.debug("Checking for external dependencies")
    ffmpeg_binary = args.ffmpeg
    if ffmpeg_binary is None:
        logger.debug("No FFmpeg specified, attempting to locate binary (auto_download=%s)", args.auto_download)
        ffmpeg_binary = get_ffmpeg_binary(args.auto_download)
        if ffmpeg_binary is None:
            logger.error("Could not find FFmpeg. Please install FFmpeg or specify its location using --ffmpeg or use --auto-download")
            sys.exit(1)
        logger.debug("Using FFmpeg binary: %s", ffmpeg_binary)

    opus_binary = args.opusenc
    if opus_binary is None:
        logger.debug("No opusenc specified, attempting to locate binary (auto_download=%s)", args.auto_download)
        opus_binary = get_opus_binary(args.auto_download) 
        if opus_binary is None:
            logger.error("Could not find opusenc. Please install opus-tools or specify its location using --opusenc or use --auto-download")
            sys.exit(1)
        logger.debug("Using opusenc binary: %s", opus_binary)

    if (args.use_media_tags or args.show_tags or args.name_template) and not is_media_tags_available():
        if not ensure_mutagen(auto_install=args.auto_download):
            logger.warning("Media tags functionality requires the mutagen library but it could not be installed.")
            if args.use_media_tags or args.show_tags:
                logger.error("Cannot proceed with --use-media-tags or --show-tags without mutagen library")
                sys.exit(1)
        else:
            logger.info("Successfully enabled media tag support")
        
    # ------------- Recursive Processing -------------
    if args.recursive:
        logger.info("Processing folders recursively: %s", args.input_filename)
        process_tasks = process_recursive_folders(
            args.input_filename,
            use_media_tags=args.use_media_tags,
            name_template=args.name_template
        )
        
        if not process_tasks:
            logger.error("No folders with audio files found for recursive processing")
            sys.exit(1)
            
        output_dir = None if args.output_to_source else './output'
        
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.debug("Created output directory: %s", output_dir)
        
        created_files = []
        for task_index, (output_name, folder_path, audio_files) in enumerate(process_tasks):
            if args.output_to_source:
                task_out_filename = os.path.join(folder_path, f"{output_name}.taf")
            else:
                task_out_filename = os.path.join(output_dir, f"{output_name}.taf")
            
            skip_creation = False
            if os.path.exists(task_out_filename):
                logger.warning("Output file already exists: %s", task_out_filename)
                valid_taf = check_tonie_file_cli(task_out_filename)

                if valid_taf and not args.force_creation:
                    logger.warning("Valid Tonie file: %s", task_out_filename)
                    logger.warning("Skipping creation step for existing Tonie file: %s", task_out_filename)
                    skip_creation = True
                else:
                    logger.info("Output file exists but is not a valid Tonie file, proceeding to create a new one.")
            
            logger.info("[%d/%d] Processing folder: %s -> %s", 
                      task_index + 1, len(process_tasks), folder_path, task_out_filename)
            
            if not skip_creation:
                create_tonie_file(task_out_filename, audio_files, args.no_tonie_header, args.user_timestamp,
                               args.bitrate, not args.cbr, ffmpeg_binary, opus_binary, args.keep_temp, 
                               args.auto_download, not args.use_legacy_tags)
                logger.info("Successfully created Tonie file: %s", task_out_filename)
            
            created_files.append(task_out_filename)
    # ------------- Recursive File Upload -------------       
            if args.upload:                
                response = client.upload_file(
                    file_path=task_out_filename,
                    destination_path=args.path,                    
                    special=args.special_folder,
                )
                upload_success = response.get('success', False)
                
                if not upload_success:
                    logger.error("Failed to upload %s to TeddyCloud", task_out_filename)
                else:
                    logger.info("Successfully uploaded %s to TeddyCloud", task_out_filename)
                    
                    # Handle artwork upload
                if args.include_artwork:
                    success, artwork_url = upload_artwork(client, task_out_filename, folder_path, audio_files)                        
                    if success:
                        logger.info("Successfully uploaded artwork for %s", task_out_filename)
                    else:
                        logger.warning("Failed to upload artwork for %s", task_out_filename)
                            
                    # tonies.custom.json generation
                if args.create_custom_json:
                    success = fetch_and_update_tonies_json(client, task_out_filename, audio_files, artwork_url, output_dir)
                    if success:
                        logger.info("Successfully updated Tonies JSON for %s", task_out_filename)
                    else:
                        logger.warning("Failed to update Tonies JSON for %s", task_out_filename)
        
        logger.info("Recursive processing completed. Created %d Tonie files.", len(process_tasks))
        sys.exit(0)
    # ------------- Single File Processing -------------
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
    if args.show_tags:
        from .media_tags import get_file_tags
        logger.info("Showing media tags for input files:")
        
        for file_index, file_path in enumerate(files):
            tags = get_file_tags(file_path)
            if tags:
                print(f"\nFile {file_index + 1}: {os.path.basename(file_path)}")
                print("-" * 40)
                for tag_name, tag_value in sorted(tags.items()):
                    print(f"{tag_name}: {tag_value}")
            else:
                print(f"\nFile {file_index + 1}: {os.path.basename(file_path)} - No tags found")
        sys.exit(0)
    guessed_name = None
    if args.use_media_tags:
        if len(files) > 1 and os.path.dirname(files[0]) == os.path.dirname(files[-1]):
            folder_path = os.path.dirname(files[0])            
            logger.debug("Extracting album info from folder: %s", folder_path)
            
            album_info = extract_album_info(folder_path)
            if album_info:
                template = args.name_template or "{album} - {artist}"
                new_name = format_metadata_filename(album_info, template)
                
                if new_name:
                    logger.info("Using album metadata for output filename: %s", new_name)
                    guessed_name = new_name
                else:
                    logger.debug("Could not format filename from album metadata")
        elif len(files) == 1:
            from .media_tags import get_file_tags, format_metadata_filename
            
            tags = get_file_tags(files[0])
            if tags:
                template = args.name_template or "{title} - {artist}"
                new_name = format_metadata_filename(tags, template)
                
                if new_name:
                    logger.info("Using file metadata for output filename: %s", new_name)
                    guessed_name = new_name
                else:
                    logger.debug("Could not format filename from file metadata")
        
        # For multiple files from different folders, try to use common tags if they exist
        elif len(files) > 1:
            from .media_tags import get_file_tags, format_metadata_filename
            
            # Try to find common tags among files
            common_tags = {}
            for file_path in files:
                tags = get_file_tags(file_path)
                if tags:
                    for key, value in tags.items():
                        if key in ['album', 'albumartist', 'artist']:
                            if key not in common_tags:
                                common_tags[key] = value
                            # Only keep values that are the same across files
                            elif common_tags[key] != value:
                                common_tags[key] = None
            
            # Remove None values
            common_tags = {k: v for k, v in common_tags.items() if v is not None}
            
            if common_tags:
                template = args.name_template or "Collection - {album}" if 'album' in common_tags else "Collection"
                new_name = format_metadata_filename(common_tags, template)
                
                if new_name:
                    logger.info("Using common metadata for output filename: %s", new_name)
                    guessed_name = new_name
                else:
                    logger.debug("Could not format filename from common metadata")

    if args.output_filename:
        out_filename = args.output_filename
    elif guessed_name:
        if args.output_to_source:
            source_dir = os.path.dirname(files[0]) if files else '.'
            out_filename = os.path.join(source_dir, guessed_name)
            logger.debug("Using source location for output with media tags: %s", out_filename)
        else:
            output_dir = './output'
            if not os.path.exists(output_dir):
                logger.debug("Creating default output directory: %s", output_dir)
                os.makedirs(output_dir, exist_ok=True)
            out_filename = os.path.join(output_dir, guessed_name)
            logger.debug("Using default output location with media tags: %s", out_filename)
    else:
        guessed_name = guess_output_filename(args.input_filename, files)    
        if args.output_to_source:
            source_dir = os.path.dirname(files[0]) if files else '.'
            out_filename = os.path.join(source_dir, guessed_name)
            logger.debug("Using source location for output: %s", out_filename)
        else:
            output_dir = './output'
            if not os.path.exists(output_dir):
                logger.debug("Creating default output directory: %s", output_dir)
                os.makedirs(output_dir, exist_ok=True)
            out_filename = os.path.join(output_dir, guessed_name)
            logger.debug("Using default output location: %s", out_filename)
    
    # Make sure source_dir is defined for later use with artwork upload
    source_dir = os.path.dirname(files[0]) if files else '.'

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
                     args.bitrate, not args.cbr, ffmpeg_binary, opus_binary, args.keep_temp, 
                     args.auto_download, not args.use_legacy_tags)
    logger.info("Successfully created Tonie file: %s", out_filename)
    
    # ------------- Single File Upload -------------  
    artwork_url = None
    if args.upload:                
        response = client.upload_file(
            file_path=out_filename,
            destination_path=args.path,                    
            special=args.special_folder,
        )
        upload_success = response.get('success', False)
        if not upload_success:
            logger.error("Failed to upload %s to TeddyCloud", out_filename)
        else:
            logger.info("Successfully uploaded %s to TeddyCloud", out_filename)

            # Handle artwork upload
        if args.include_artwork:
            success, artwork_url = upload_artwork(client, out_filename, source_dir, files)                        
            if success:
                logger.info("Successfully uploaded artwork for %s", out_filename)
            else:
                logger.warning("Failed to upload artwork for %s", out_filename)        
            # tonies.custom.json generation
        if args.create_custom_json:
            success = fetch_and_update_tonies_json(client, out_filename, files, artwork_url)
            if success:
                logger.info("Successfully updated Tonies JSON for %s", out_filename)
            else:
                logger.warning("Failed to update Tonies JSON for %s", out_filename)

if __name__ == "__main__":
    main()