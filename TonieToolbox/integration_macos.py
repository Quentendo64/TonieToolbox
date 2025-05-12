# filepath: d:\Repository\TonieToolbox\TonieToolbox\integration_macos.py
import os
import sys
import json
import plistlib
import subprocess
from pathlib import Path
from .constants import SUPPORTED_EXTENSIONS
from .logger import get_logger

logger = get_logger('integration_macos')

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
        
        # Error handling and success messages for shell scripts
        self.error_handling = 'if [ $? -ne 0 ]; then\n  echo "Error: Command failed with error code $?"\n  read -p "Press any key to close this window..." key\n  exit 1\nfi'
        self.success_handling = 'echo "Command completed successfully"\nsleep 2'
        
        # Load configuration
        self.config = self._load_config()
        
        # Ensure these attributes always exist
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
            cmd_line += ' --compare "$1" "$2"'
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
        # Always initialize authentication flags
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
        # Create Quick Action directory
        action_dir = os.path.join(self.services_dir, f"{name}.workflow")
        os.makedirs(action_dir, exist_ok=True)
        
        # Create Contents directory
        contents_dir = os.path.join(action_dir, "Contents")
        os.makedirs(contents_dir, exist_ok=True)
        
        # Create document.wflow file with plist content
        document_path = os.path.join(contents_dir, "document.wflow")
        
        # Create Info.plist
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
                    "NSSendTypes": ["NSFilenamesPboardType"] if directory_based else []
                }
            ]
        }
        
        info_path = os.path.join(contents_dir, "Info.plist")
        with open(info_path, "wb") as f:
            plistlib.dump(info_plist, f)
        
        # Create script file
        script_dir = os.path.join(contents_dir, "MacOS")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, "script")
        
        with open(script_path, "w") as f:
            f.write(command)
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Create document.wflow file with a basic workflow definition
        workflow = {
            "AMApplication": "Automator",
            "AMCanShowSelectedItemsWhenRun": False,
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
                            "input": "as arguments"
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

    def _generate_audio_extension_actions(self):
        """Generate Quick Actions for supported audio file extensions."""
        extensions = [ext.lower().lstrip('.') for ext in SUPPORTED_EXTENSIONS]
        
        # Create audio file actions
        self._create_quick_action(
            "TonieToolbox - Convert to TAF",
            self.convert_cmd,
            file_types=extensions
        )
        
        if self.upload_enabled:
            self._create_quick_action(
                "TonieToolbox - Convert and Upload",
                self.upload_cmd,
                file_types=extensions
            )
            
            self._create_quick_action(
                "TonieToolbox - Convert, Upload with Artwork",
                self.upload_artwork_cmd,
                file_types=extensions
            )
            
            self._create_quick_action(
                "TonieToolbox - Convert, Upload with Artwork and JSON",
                self.upload_artwork_json_cmd,
                file_types=extensions
            )

    def _generate_taf_file_actions(self):
        """Generate Quick Actions for .taf files."""
        self._create_quick_action(
            "TonieToolbox - Show Info",
            self.show_info_cmd,
            file_types=["taf"]
        )
        
        self._create_quick_action(
            "TonieToolbox - Extract Opus Tracks",
            self.extract_opus_cmd,
            file_types=["taf"]
        )
        
        if self.upload_enabled:
            self._create_quick_action(
                "TonieToolbox - Upload",
                self.upload_taf_cmd,
                file_types=["taf"]
            )
            
            self._create_quick_action(
                "TonieToolbox - Upload with Artwork",
                self.upload_taf_artwork_cmd,
                file_types=["taf"]
            )
            
            self._create_quick_action(
                "TonieToolbox - Upload with Artwork and JSON",
                self.upload_taf_artwork_json_cmd,
                file_types=["taf"]
            )
        
        self._create_quick_action(
            "TonieToolbox - Compare with another TAF file",
            self.compare_taf_cmd,
            file_types=["taf"]
        )

    def _generate_folder_actions(self):
        """Generate Quick Actions for folders."""
        self._create_quick_action(
            "TonieToolbox - Convert Folder to TAF (recursive)",
            self.convert_folder_cmd,
            directory_based=True
        )
        
        if self.upload_enabled:
            self._create_quick_action(
                "TonieToolbox - Convert Folder and Upload (recursive)",
                self.upload_folder_cmd,
                directory_based=True
            )
            
            self._create_quick_action(
                "TonieToolbox - Convert Folder, Upload with Artwork (recursive)",
                self.upload_folder_artwork_cmd,
                directory_based=True
            )
            
            self._create_quick_action(
                "TonieToolbox - Convert Folder, Upload with Artwork and JSON (recursive)",
                self.upload_folder_artwork_json_cmd,
                directory_based=True
            )

    def install_quick_actions(self):
        """Install all Quick Actions."""
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
        subprocess.run(["killall", "-HUP", "Finder"], check=False)
        
        print("TonieToolbox Quick Actions installed successfully.")
        print("You'll find them in the Services menu when right-clicking on audio files, TAF files, or folders.")

    def uninstall_quick_actions(self):
        """Uninstall all TonieToolbox Quick Actions."""
        # Find and remove all TonieToolbox Quick Actions
        for item in os.listdir(self.services_dir):
            if item.startswith("TonieToolbox - ") and item.endswith(".workflow"):
                action_path = os.path.join(self.services_dir, item)
                try:
                    subprocess.run(["rm", "-rf", action_path], check=True)
                    print(f"Removed: {item}")
                except subprocess.CalledProcessError:
                    print(f"Failed to remove: {item}")
        
        # Refresh the Services menu
        subprocess.run(["killall", "-HUP", "Finder"], check=False)
        
        print("TonieToolbox Quick Actions uninstalled successfully.")

    @classmethod
    def install(cls):
        """
        Generate Quick Actions and install them.
        """
        instance = cls()
        instance.install_quick_actions()

    @classmethod
    def uninstall(cls):
        """
        Uninstall all TonieToolbox Quick Actions.
        """
        instance = cls()
        instance.uninstall_quick_actions()