#!/usr/bin/python3
"""
Integration for MacOS Quick Actions (Services) for TonieToolbox.
This module provides functionality to create and manage Quick Actions.
"""
import os
import sys
import json
import plistlib
import subprocess
from pathlib import Path
from .constants import SUPPORTED_EXTENSIONS, CONFIG_TEMPLATE,UTI_MAPPINGS,ICON_BASE64
from .artwork import base64_to_ico
from .logger import get_logger

logger = get_logger(__name__)

class MacOSContextMenuIntegration:
    """
    Class to generate macOS Quick Actions for TonieToolbox integration.
    Creates Quick Actions (Services) for supported audio files, .taf files, and folders.
    """
    def __init__(self):
        # Find the installed command-line tool path
        self.exe_path = os.path.join(sys.prefix, 'bin', 'tonietoolbox')
        self.output_dir = os.path.join(os.path.expanduser('~'), '.tonietoolbox')
        self.services_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Services')
        self.icon_path = os.path.join(self.output_dir, 'icon.png')
        os.makedirs(self.output_dir, exist_ok=True)
        self.error_handling = 'if [ $? -ne 0 ]; then\n  echo "Error: Command failed with error code $?"\n  read -p "Press any key to close this window..." key\n  exit 1\nfi'
        self.success_handling = 'echo "Command completed successfully"\nsleep 2'
        self.config = self._apply_config_template()
        self.upload_url = ''
        self.log_level = self.config.get('log_level', 'SILENT')
        self.log_to_file = self.config.get('log_to_file', False)
        self.basic_authentication_cmd = ''
        self.client_cert_cmd = ''
        self.upload_enabled = self._setup_upload()
        
        logger.debug(f"Upload enabled: {self.upload_enabled}")
        logger.debug(f"Upload URL: {self.upload_url}")
        logger.debug(f"Authentication: {'Basic Authentication' if self.basic_authentication else ('None' if self.none_authentication else ('Client Cert' if self.client_cert_authentication else 'Unknown'))}")        
        self._setup_commands()    
    
    def _build_cmd(self, base_args, file_placeholder='$1', output_to_source=True, use_upload=False, use_artwork=False, use_json=False, use_compare=False, use_info=False, is_recursive=False, is_split=False, is_folder=False, keep_open=False, log_to_file=False):
        """Dynamically build command strings for quick actions."""
        exe = self.exe_path
        cmd = '#!/bin/bash\n\n'
          # Debug output to see what's being passed to the script
        cmd += 'echo "Arguments received: $@"\n'
        cmd += 'echo "Number of arguments: $#"\n'
        cmd += 'if [ $# -gt 0 ]; then\n'
        cmd += '  echo "First argument: $1"\n'
        cmd += 'fi\n\n'
        
        # Add a description of what's being executed
        cmd += 'echo "Running TonieToolbox'
        if use_info:
            cmd += ' info'
        elif is_split:
            cmd += ' split'
        elif use_compare:
            cmd += ' compare'
        elif is_recursive:
            cmd += ' recursive folder convert'
        elif is_folder:
            cmd += ' folder convert'
        elif use_upload and use_artwork and use_json:
            cmd += ' convert, upload, artwork and JSON'
        elif use_upload and use_artwork:
            cmd += ' convert, upload and artwork'
        elif use_upload:
            cmd += ' convert and upload'
        else:
            cmd += ' convert'
        cmd += ' command..."\n\n'
          # Properly handle paths from macOS Services
        if is_folder or is_recursive:
            # Handle multiple arguments and ensure we get a valid folder
            cmd += '# Handle paths from macOS Services\n'
            cmd += '# First, try to get paths from stdin (macOS passes paths this way)\n'
            cmd += 'if [ -p /dev/stdin ]; then\n'
            cmd += '  PATHS=$(cat /dev/stdin)\n'
            cmd += '  echo "Found paths from stdin: $PATHS"\n'
            cmd += 'fi\n\n'
            cmd += '# If no paths from stdin, check command line arguments\n'
            cmd += 'FOLDER_PATH=""\n'
            cmd += 'if [ -z "$PATHS" ]; then\n'
            cmd += '  for arg in "$@"; do\n'
            cmd += '    if [ -d "$arg" ]; then\n'
            cmd += '      FOLDER_PATH="$arg"\n'
            cmd += '      echo "Processing folder from args: $FOLDER_PATH"\n'
            cmd += '      break\n'
            cmd += '    fi\n'
            cmd += '  done\n'
            cmd += 'else\n'
            cmd += '  for path in $PATHS; do\n'
            cmd += '    if [ -d "$path" ]; then\n'
            cmd += '      FOLDER_PATH="$path"\n'
            cmd += '      echo "Processing folder from stdin: $FOLDER_PATH"\n'
            cmd += '      break\n'
            cmd += '    fi\n'
            cmd += '  done\n'
            cmd += 'fi\n\n'
            cmd += 'if [ -z "$FOLDER_PATH" ]; then\n'
            cmd += '  echo "Error: No valid folder path found in arguments or stdin"\n'
            cmd += '  read -p "Press any key to close this window..." key\n'
            cmd += '  exit 1\n'
            cmd += 'fi\n\n'
            
            # Use the variable for the command
            file_placeholder='$FOLDER_PATH'
        elif use_compare:
            # For compare operation, we need two file paths
            cmd += '# Compare requires two files\n'
            cmd += 'if [ $# -lt 2 ]; then\n'
            cmd += '  echo "Error: Compare operation requires two files."\n'
            cmd += '  read -p "Press any key to close this window..." key\n'
            cmd += '  exit 1\n'
            cmd += 'fi\n\n'        
        else:
            # For regular file operations, handle paths correctly
            cmd += '# Handle file paths correctly - try multiple methods for macOS\n'
            cmd += 'FILE_PATH=""\n'
            
            # First, try to get paths from stdin (macOS passes paths this way sometimes)
            cmd += '# Method 1: Try to read from stdin if available\n'
            cmd += 'if [ -p /dev/stdin ]; then\n'
            cmd += '  STDIN_PATHS=$(cat)\n'
            cmd += '  if [ -n "$STDIN_PATHS" ]; then\n'
            cmd += '    for path in $STDIN_PATHS; do\n'
            cmd += '      if [ -f "$path" ]; then\n'
            cmd += '        FILE_PATH="$path"\n'
            cmd += '        echo "Found file path from stdin: $FILE_PATH"\n'
            cmd += '        break\n'
            cmd += '      fi\n'
            cmd += '    done\n'
            cmd += '  fi\n'
            cmd += 'fi\n\n'
            
            # Method 2: Try command line arguments
            cmd += '# Method 2: Check command line arguments\n'
            cmd += 'if [ -z "$FILE_PATH" ]; then\n'
            cmd += '  for arg in "$@"; do\n'
            cmd += '    if [ -f "$arg" ]; then\n'
            cmd += '      FILE_PATH="$arg"\n'
            cmd += '      echo "Found file path from arguments: $FILE_PATH"\n'
            cmd += '      break\n'
            cmd += '    fi\n'
            cmd += '  done\n'
            cmd += 'fi\n\n'
            
            # Method 3: Try to handle case where path might be in $1
            cmd += '# Method 3: Try first argument directly\n'
            cmd += 'if [ -z "$FILE_PATH" ] && [ -n "$1" ] && [ -f "$1" ]; then\n'
            cmd += '  FILE_PATH="$1"\n'
            cmd += '  echo "Using first argument directly as file path: $FILE_PATH"\n'
            cmd += 'fi\n\n'
            
            # Method 4: Parse automator's encoded path format
            cmd += '# Method 4: Try to decode special format macOS might use\n'
            cmd += 'if [ -z "$FILE_PATH" ] && [ -n "$1" ]; then\n'
            cmd += '  # Sometimes macOS passes paths with "file://" prefix\n'
            cmd += '  DECODED_PATH=$(echo "$1" | sed -e "s|^file://||" -e "s|%20| |g")\n'
            cmd += '  if [ -f "$DECODED_PATH" ]; then\n'
            cmd += '    FILE_PATH="$DECODED_PATH"\n'
            cmd += '    echo "Using decoded path: $FILE_PATH"\n'
            cmd += '  fi\n'
            cmd += 'fi\n\n'
            
            # Final check
            cmd += 'if [ -z "$FILE_PATH" ]; then\n'
            cmd += '  echo "Error: Could not find a valid file path. Tried:"\n'
            cmd += '  echo "- Reading from stdin"\n'
            cmd += '  echo "- Command arguments: $@"\n'
            cmd += '  echo "- Decoding URL format"\n'
            cmd += '  read -p "Press any key to close this window..." key\n'
            cmd += '  exit 1\n'
            cmd += 'fi\n\n'
            
            # Use the variable for the command
            file_placeholder='$FILE_PATH'
        
        # Build the actual command
        cmd_line = f'"{exe}" {base_args}'
        if log_to_file:
            cmd_line += ' --log-file'        
        if is_recursive:
            cmd_line += ' --recursive'
        if output_to_source:
            cmd_line += ' --output-to-source'
        if use_info:
            cmd_line += ' --info'
        if is_split:
            cmd_line += ' --split'
        if use_compare:
            # For compare, we need to handle two files
            cmd += '# Find two TAF files for comparison\n'
            cmd += 'FILE1=""\n'
            cmd += 'FILE2=""\n'
            cmd += 'for arg in "$@"; do\n'
            cmd += '  if [ -f "$arg" ]; then\n'
            cmd += '    if [ -z "$FILE1" ]; then\n'
            cmd += '      FILE1="$arg"\n'
            cmd += '      echo "First TAF file: $FILE1"\n'
            cmd += '    elif [ -z "$FILE2" ]; then\n'
            cmd += '      FILE2="$arg"\n'
            cmd += '      echo "Second TAF file: $FILE2"\n'
            cmd += '      break\n'
            cmd += '    fi\n'
            cmd += '  fi\n'
            cmd += 'done\n\n'
            cmd += 'if [ -z "$FILE1" ] || [ -z "$FILE2" ]; then\n'
            cmd += '  echo "Error: Need two TAF files for comparison."\n'
            cmd += '  read -p "Press any key to close this window..." key\n'
            cmd += '  exit 1\n'
            cmd += 'fi\n\n'            
            cmd_line += ' --compare "$FILE1" "$FILE2"'
        else:
            cmd_line += f' "{file_placeholder}"'
        if use_upload:
            cmd_line += f' --upload "{self.upload_url}"'
            if self.basic_authentication_cmd:
                cmd_line += f' {self.basic_authentication_cmd}'
            elif self.client_cert_cmd:
                cmd_line += f' {self.client_cert_cmd}'
            if getattr(self, "ignore_ssl_verify", False):
                cmd_line += ' --ignore-ssl-verify'
        if use_artwork:
            cmd_line += ' --include-artwork'
        if use_json:
            cmd_line += ' --create-custom-json'
            
        # Add the command to the script
        cmd += f'echo "Executing: {cmd_line}"\n'
        cmd += f'{cmd_line}\n\n'
        
        # Add error and success handling
        cmd += f'{self.error_handling}\n\n'
        if use_info or use_compare or keep_open:
            cmd += 'echo ""\nread -p "Press any key to close this window..." key\n'
        else:
            cmd += f'{self.success_handling}\n'
            
        return cmd

    def _get_log_level_arg(self):
        """Return the correct log level argument for TonieToolbox CLI based on self.log_level."""
        level = str(self.log_level).strip().upper()
        if level == 'DEBUG':
            return '--debug'
        elif level == 'INFO':
            return '--info'
        return '--silent'

    def _setup_commands(self):
        """Set up all command strings for quick actions dynamically."""
        log_level_arg = self._get_log_level_arg()
        
        # Audio file commands
        self.convert_cmd = self._build_cmd(f'{log_level_arg}', log_to_file=self.log_to_file)
        self.upload_cmd = self._build_cmd(f'{log_level_arg}', use_upload=True, log_to_file=self.log_to_file)
        self.upload_artwork_cmd = self._build_cmd(f'{log_level_arg}', use_upload=True, use_artwork=True, log_to_file=self.log_to_file)
        self.upload_artwork_json_cmd = self._build_cmd(f'{log_level_arg}', use_upload=True, use_artwork=True, use_json=True, log_to_file=self.log_to_file)

        # .taf file commands
        self.show_info_cmd = self._build_cmd(log_level_arg, use_info=True, keep_open=True, log_to_file=self.log_to_file)
        self.extract_opus_cmd = self._build_cmd(log_level_arg, is_split=True, log_to_file=self.log_to_file)
        self.upload_taf_cmd = self._build_cmd(log_level_arg, use_upload=True, log_to_file=self.log_to_file)
        self.upload_taf_artwork_cmd = self._build_cmd(log_level_arg, use_upload=True, use_artwork=True, log_to_file=self.log_to_file)
        self.upload_taf_artwork_json_cmd = self._build_cmd(log_level_arg, use_upload=True, use_artwork=True, use_json=True, log_to_file=self.log_to_file)
        self.compare_taf_cmd = self._build_cmd(log_level_arg, use_compare=True, keep_open=True, log_to_file=self.log_to_file)

        # Folder commands
        self.convert_folder_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, log_to_file=self.log_to_file)
        self.upload_folder_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, use_upload=True, log_to_file=self.log_to_file)
        self.upload_folder_artwork_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, use_upload=True, use_artwork=True, log_to_file=self.log_to_file)
        self.upload_folder_artwork_json_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, use_upload=True, use_artwork=True, use_json=True, log_to_file=self.log_to_file)

    def _apply_config_template(self):
        """Apply the default configuration template if config.json is missing or invalid. Extracts the icon from base64 if not present."""
        config_path = os.path.join(self.output_dir, 'config.json')
        icon_path = os.path.join(self.output_dir, 'icon.ico')
        if not os.path.exists(icon_path):
            base64_to_ico(ICON_BASE64, icon_path)
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump(CONFIG_TEMPLATE, f, indent=4)
            logger.debug(f"Default configuration created at {config_path}")
            return CONFIG_TEMPLATE
        else:
            logger.debug(f"Configuration file found at {config_path}")
            return self._load_config()
            
    def _load_config(self):
        """Load configuration settings from config.json"""
        config_path = os.path.join(self.output_dir, 'config.json')
        if not os.path.exists(config_path):
            logger.debug(f"Configuration file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = json.loads(f.read())
            return config
        except (json.JSONDecodeError, IOError) as e:
            logger.debug(f"Error loading config: {e}")
            return {}

    def _setup_upload(self):
        """Set up upload functionality based on config.json settings"""
        self.basic_authentication = False
        self.client_cert_authentication = False
        self.none_authentication = False
        
        config = self.config
        try:            
            upload_config = config.get('upload', {})            
            self.upload_urls = upload_config.get('url', [])
            self.ignore_ssl_verify = upload_config.get('ignore_ssl_verify', False)
            self.username = upload_config.get('username', '')
            self.password = upload_config.get('password', '')
            self.basic_authentication_cmd = ''
            self.client_cert_cmd = ''
            
            if self.username and self.password:
                self.basic_authentication_cmd = f'--username {self.username} --password {self.password}'
                self.basic_authentication = True
                
            self.client_cert_path = upload_config.get('client_cert_path', '')
            self.client_cert_key_path = upload_config.get('client_cert_key_path', '')
            if self.client_cert_path and self.client_cert_key_path:
                self.client_cert_cmd = f'--client-cert {self.client_cert_path} --client-cert-key {self.client_cert_key_path}'
                self.client_cert_authentication = True
                
            if self.client_cert_authentication and self.basic_authentication:
                logger.warning("Both client certificate and basic authentication are set. Only one can be used.")
                return False
                
            self.upload_url = self.upload_urls[0] if self.upload_urls else ''
            if not self.client_cert_authentication and not self.basic_authentication and self.upload_url:
                self.none_authentication = True
                
            return bool(self.upload_url)
        except Exception as e:
            logger.debug(f"Unexpected error while loading configuration: {e}")
            return False    
    def _create_quick_action(self, name, command, file_types=None, directory_based=False):
        """Create a macOS Quick Action (Service) with the given name and command."""
        action_dir = os.path.join(self.services_dir, f"{name}.workflow")
        os.makedirs(action_dir, exist_ok=True)
        contents_dir = os.path.join(action_dir, "Contents")
        os.makedirs(contents_dir, exist_ok=True)
        document_path = os.path.join(contents_dir, "document.wflow")
        
        # Set up the plist to ensure the service appears in context menus
        info_plist = {
            "NSServices": [
                {
                    "NSMenuItem": {
                        "default": name
                    },
                    "NSMessage": "runWorkflowAsService",
                    "NSRequiredContext": {
                        "NSApplicationIdentifier": "com.apple.finder"
                    },
                    "NSSendFileTypes": file_types if file_types else [],
                    "NSSendTypes": ["NSFilenamesPboardType"], # Always include this to ensure paths are passed correctly
                    "NSUserData": name,
                    "NSExecutable": "script", # Ensure macOS knows which script to run
                    "NSReturnTypes": []
                }
            ]
        }
        
        info_path = os.path.join(contents_dir, "Info.plist")
        with open(info_path, "wb") as f:
            plistlib.dump(info_plist, f)    
        script_dir = os.path.join(contents_dir, "MacOS")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, "script")
        
        with open(script_path, "w") as f:
            f.write(command)    
        os.chmod(script_path, 0o755)
        workflow = {
            "AMApplication": "Automator",
            "AMCanShowSelectedItemsWhenRun": True,
            "AMCanShowWhenRun": True,
            "AMDockBadgeLabel": "",
            "AMDockBadgeStyle": "badge",
            "AMName": name,
            "AMRootElement": {
                "actions": [
                    {
                        "action": "run-shell-script",
                        "parameters": {
                            "shell": "/bin/bash",
                            "script": command,
                            "input": "as arguments",
                            "showStdout": True,
                            "showStderr": True,
                            "showOutput": True,
                            "runAsAdmin": False
                        }
                    }
                ],
                "class": "workflow",
                "connections": {},
                "id": "workflow-element",
                "title": name
            },
            "AMWorkflowSchemeVersion": 2.0,
        }
        with open(document_path, "wb") as f:
            plistlib.dump(workflow, f)
            
        return action_dir
        
    def _extension_to_uti(self, extension):
        """Convert a file extension to macOS UTI (Uniform Type Identifier)."""
        uti_map = UTI_MAPPINGS
        ext = extension.lower().lstrip('.')
        return uti_map.get(ext, f'public.{ext}')
        
    def _generate_audio_extension_actions(self):
        """Generate Quick Actions for supported audio file extensions."""
        extensions = [ext.lower().lstrip('.') for ext in SUPPORTED_EXTENSIONS]
        # Convert extensions to UTIs (Uniform Type Identifiers)
        utis = [self._extension_to_uti(ext) for ext in extensions]
        self._create_quick_action(
            "TonieToolbox - Convert to TAF",
            self.convert_cmd,
            file_types=utis
        )
        
        if self.upload_enabled:
            self._create_quick_action(
                "TonieToolbox - Convert and Upload",
                self.upload_cmd,
                file_types=utis
            )
            
            self._create_quick_action(
                "TonieToolbox - Convert, Upload with Artwork",
                self.upload_artwork_cmd,
                file_types=utis
            )
            
            self._create_quick_action(
                "TonieToolbox - Convert, Upload with Artwork and JSON",
                self.upload_artwork_json_cmd,
                file_types=utis
            )
            
    def _generate_taf_file_actions(self):
        """Generate Quick Actions for .taf files."""
        taf_uti = self._extension_to_uti("taf")  # Use UTI for TAF files
        
        self._create_quick_action(
            "TonieToolbox - Show Info",
            self.show_info_cmd,
            file_types=[taf_uti]
        )
        
        self._create_quick_action(
            "TonieToolbox - Extract Opus Tracks",
            self.extract_opus_cmd,
            file_types=[taf_uti]
        )
        
        if self.upload_enabled:
            self._create_quick_action(
                "TonieToolbox - Upload",
                self.upload_taf_cmd,
                file_types=[taf_uti]
            )
            self._create_quick_action(
                "TonieToolbox - Upload with Artwork",
                self.upload_taf_artwork_cmd,
                file_types=[taf_uti]
            )
            
            self._create_quick_action(
                "TonieToolbox - Upload with Artwork and JSON",
                self.upload_taf_artwork_json_cmd,
                file_types=[taf_uti]
            )
            
            self._create_quick_action(
                "TonieToolbox - Compare with another TAF file",
                self.compare_taf_cmd,
                file_types=[taf_uti]
            )
        
    def _generate_folder_actions(self):
        """Generate Quick Actions for folders."""
        self._create_quick_action(
            "TonieToolbox - 1. Convert Folder to TAF (recursive)",
            self.convert_folder_cmd,
            directory_based=True
        )
        
        if self.upload_enabled:
            self._create_quick_action(
                "TonieToolbox - 2. Convert Folder and Upload (recursive)",
                self.upload_folder_cmd,
                directory_based=True
            )
            
            self._create_quick_action(
                "TonieToolbox - 3. Convert Folder, Upload with Artwork (recursive)",
                self.upload_folder_artwork_cmd,
                directory_based=True
            )
            
            self._create_quick_action(
                "TonieToolbox - 4. Convert Folder, Upload with Artwork and JSON (recursive)",
                self.upload_folder_artwork_json_cmd,
                directory_based=True
            )
    
    def install_quick_actions(self):
        """
        Install all Quick Actions.
        
        Returns:
            bool: True if all actions were installed successfully, False otherwise.
        """
        try:
            # Ensure Services directory exists
            os.makedirs(self.services_dir, exist_ok=True)
            
            # Check if the icon exists, copy default if needed
            if not os.path.exists(self.icon_path):
                # Include code to extract icon from resources
                logger.debug(f"Icon not found at {self.icon_path}, using default")
            
            # Generate Quick Actions for different file types
            self._generate_audio_extension_actions()
            self._generate_taf_file_actions()
            self._generate_folder_actions()
            
            # Refresh the Services menu by restarting the Finder
            result = subprocess.run(["killall", "-HUP", "Finder"], check=False, 
                                   capture_output=True, text=True)
            logger.info("TonieToolbox Quick Actions installed successfully.")
            logger.info("You'll find them in the Services menu when right-clicking on audio files, TAF files, or folders.")
            
            return True
        except Exception as e:
            logger.error(f"Failed to install Quick Actions: {e}")
            return False
            
    def uninstall_quick_actions(self):
        """
        Uninstall all TonieToolbox Quick Actions.
        
        Returns:
            bool: True if all actions were uninstalled successfully, False otherwise.
        """
        try:
            any_failures = False
            for item in os.listdir(self.services_dir):
                if item.startswith("TonieToolbox - ") and item.endswith(".workflow"):
                    action_path = os.path.join(self.services_dir, item)
                    try:
                        subprocess.run(["rm", "-rf", action_path], check=True)
                        print(f"Removed: {item}")
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to remove: {item}")
                        logger.error(f"Error removing {item}: {e}")
                        any_failures = True            
            subprocess.run(["killall", "-HUP", "Finder"], check=False)
            
            print("TonieToolbox Quick Actions uninstalled successfully.")
            
            return not any_failures
        except Exception as e:
            logger.error(f"Failed to uninstall Quick Actions: {e}")
            return False
            
    @classmethod
    def install(cls):
        """
        Generate Quick Actions and install them.
        
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        instance = cls()
        if instance.install_quick_actions():
            logger.info("macOS integration installed successfully.")
            return True
        else:
            logger.error("macOS integration installation failed.")
            return False

    @classmethod
    def uninstall(cls):
        """
        Uninstall all TonieToolbox Quick Actions.
        
        Returns:
            bool: True if uninstallation was successful, False otherwise.
        """
        instance = cls()
        if instance.uninstall_quick_actions():
            logger.info("macOS integration uninstalled successfully.")
            return True
        else:
            logger.error("macOS integration uninstallation failed.")
            return False