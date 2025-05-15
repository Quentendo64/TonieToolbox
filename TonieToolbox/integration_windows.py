#!/usr/bin/python3
"""
Integration for Windows "classic" context menu.
This module generates Windows registry entries to add a 'TonieToolbox' cascade menu.
"""
import os
import sys
import json
from .constants import SUPPORTED_EXTENSIONS, CONFIG_TEMPLATE, ICON_BASE64
from .artwork import base64_to_ico
from .logger import get_logger

logger = get_logger(__name__)

class WindowsClassicContextMenuIntegration:
    """
    Class to generate Windows registry entries for TonieToolbox "classic" context menu integration.
    Adds a 'TonieToolbox' cascade menu for supported audio files, .taf files, and folders.
    """
    def __init__(self):
        self.exe_path = os.path.join(sys.prefix, 'Scripts', 'tonietoolbox.exe')
        self.exe_path_reg = self.exe_path.replace('\\', r'\\')
        self.output_dir = os.path.join(os.path.expanduser('~'), '.tonietoolbox')
        self.icon_path = os.path.join(self.output_dir, 'icon.ico').replace('\\', r'\\')
        self.cascade_name = 'TonieToolbox'
        self.entry_is_separator = '"CommandFlags"=dword:00000008'
        self.show_uac = '"CommandFlags"=dword:00000010'
        self.separator_below = '"CommandFlags"=dword:00000040'
        self.separator_above = '"CommandFlags"=dword:00000020'
        self.error_handling = r' && if %ERRORLEVEL% neq 0 (echo Error: Command failed with error code %ERRORLEVEL% && pause && exit /b %ERRORLEVEL%) else (echo Command completed successfully && ping -n 2 127.0.0.1 > nul)'
        self.show_info_error_handling = r' && if %ERRORLEVEL% neq 0 (echo Error: Command failed with error code %ERRORLEVEL% && pause && exit /b %ERRORLEVEL%) else (echo. && echo Press any key to close this window... && pause > nul)'
        self.config = self._apply_config_template()
        self.upload_url = ''
        self.log_level = self.config.get('log_level', 'SILENT')
        self.log_to_file = self.config.get('log_to_file', False)
        self.basic_authentication_cmd = ''
        self.client_cert_cmd = ''
        self.upload_enabled = self._setup_upload()
        
        print(f"Upload enabled: {self.upload_enabled}")
        print(f"Upload URL: {self.upload_url}")
        print(f"Authentication: {'Basic Authentication' if self.basic_authentication else ('None' if self.none_authentication else ('Client Cert' if self.client_cert_authentication else 'Unknown'))}")
        
        self._setup_commands()

    def _build_cmd(self, base_args, file_placeholder='%1', output_to_source=True ,use_upload=False, use_artwork=False, use_json=False, use_compare=False, use_info=False, is_recursive=False, is_split=False, is_folder=False, shell='cmd.exe', keep_open=False, log_to_file=False):
        """Dynamically build command strings for registry entries."""
        exe = self.exe_path_reg        
        cmd = f'{shell} /{"k" if keep_open else "c"} "echo Running TonieToolbox'
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
        cmd += ' command... && "'
        cmd += f'{exe}" {base_args}'
        if log_to_file:
            cmd += ' --log-file'
        if is_recursive:
            cmd += ' --recursive'
        if output_to_source:
            cmd += ' --output-to-source'
        if use_info:
            cmd += ' --info'
        if is_split:
            cmd += ' --split'
        if use_compare:
            cmd += ' --compare "%1" "%2"'
        else:
            cmd += f' "{file_placeholder}"'
        if use_upload:
            cmd += f' --upload "{self.upload_url}"'
            if self.basic_authentication_cmd:
                cmd += f' {self.basic_authentication_cmd}'
            elif self.client_cert_cmd:
                cmd += f' {self.client_cert_cmd}'
            if getattr(self, "ignore_ssl_verify", False):
                cmd += ' --ignore-ssl-verify'
        if use_artwork:
            cmd += ' --include-artwork'
        if use_json:
            cmd += ' --create-custom-json'
        if use_info or use_compare:
            cmd += ' && echo. && pause && exit > nul"'
        else:
            cmd += f'{self.error_handling}"'
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
        """Set up all command strings for registry entries dynamically."""
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
        #self.compare_taf_cmd = self._build_cmd(log_level_arg, use_compare=True, keep_open=True, log_to_file=self.log_to_file)

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
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.loads(f.read())
        
        return config

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
        except FileNotFoundError:
            logger.debug("Configuration file not found. Skipping upload setup.")
            return False
        except json.JSONDecodeError:
            logger.debug("Error decoding JSON in configuration file. Skipping upload setup.")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error while loading configuration: {e}")
            return False

    def _reg_escape(self, s):
        """Escape a string for use in a .reg file (escape double quotes)."""
        return s.replace('"', '\\"')

    def _generate_audio_extensions_entries(self):
        """Generate registry entries for supported audio file extensions"""
        reg_lines = []
        for ext in SUPPORTED_EXTENSIONS:
            ext = ext.lower().lstrip('.')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell]')
            reg_lines.append('')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}]')
            reg_lines.append('"MUIVerb"="TonieToolbox"')
            reg_lines.append(f'"Icon"="{self.icon_path}"')
            reg_lines.append('"subcommands"=""')
            reg_lines.append('')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell]')
            # Convert
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\a_Convert]')
            reg_lines.append('@="Convert File to .taf"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\a_Convert\\command]')
            reg_lines.append(f'@="{self._reg_escape(self.convert_cmd)}"')
            reg_lines.append('')
            if self.upload_enabled:
                # Upload
                reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\b_Upload]')
                reg_lines.append('@="Convert File to .taf and Upload"')
                reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\b_Upload\\command]')
                reg_lines.append(f'@="{self._reg_escape(self.upload_cmd)}"')
                reg_lines.append('')
                # Upload + Artwork
                reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\c_UploadArtwork]')
                reg_lines.append('@="Convert File to .taf and Upload + Artwork"')
                reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\c_UploadArtwork\\command]')
                reg_lines.append(f'@="{self._reg_escape(self.upload_artwork_cmd)}"')
                reg_lines.append('')
                # Upload + Artwork + JSON
                reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\d_UploadArtworkJson]')
                reg_lines.append('@="Convert File to .taf and Upload + Artwork + JSON"')
                reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\d_UploadArtworkJson\\command]')
                reg_lines.append(f'@="{self._reg_escape(self.upload_artwork_json_cmd)}"')
                reg_lines.append('')
        return reg_lines

    def _generate_taf_file_entries(self):
        """Generate registry entries for .taf files"""
        reg_lines = []
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell]')
        reg_lines.append('')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}]')
        reg_lines.append('"MUIVerb"="TonieToolbox"')
        reg_lines.append(f'"Icon"="{self.icon_path}"')
        reg_lines.append('"subcommands"=""')
        reg_lines.append('')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell]')
        # Show Info
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\a_ShowInfo]')
        reg_lines.append('@="Show Info"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\a_ShowInfo\\command]')
        reg_lines.append(f'@="{self._reg_escape(self.show_info_cmd)}"')
        reg_lines.append('')
        # Extract Opus Tracks
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\b_ExtractOpus]')
        reg_lines.append('@="Extract Opus Tracks"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\b_ExtractOpus\\command]')
        reg_lines.append(f'@="{self._reg_escape(self.extract_opus_cmd)}"')
        reg_lines.append('')
        if self.upload_enabled:
            # Upload
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\c_Upload]')
            reg_lines.append('@="Upload"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\c_Upload\\command]')
            reg_lines.append(f'@="{self._reg_escape(self.upload_taf_cmd)}"')
            reg_lines.append('')
            # Upload + Artwork
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\d_UploadArtwork]')
            reg_lines.append('@="Upload + Artwork"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\d_UploadArtwork\\command]')
            reg_lines.append(f'@="{self._reg_escape(self.upload_taf_artwork_cmd)}"')
            reg_lines.append('')
            # Upload + Artwork + JSON
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\e_UploadArtworkJson]')
            reg_lines.append('@="Upload + Artwork + JSON"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\e_UploadArtworkJson\\command]')
            reg_lines.append(f'@="{self._reg_escape(self.upload_taf_artwork_json_cmd)}"')
            reg_lines.append('')
        # Compare TAF Files
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\f_CompareTaf]')
        reg_lines.append('@="Compare with another .taf file"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\f_CompareTaf\\command]')
        reg_lines.append(f'@="{self._reg_escape(self.compare_taf_cmd)}"')
        reg_lines.append('')
        return reg_lines

    def _generate_folder_entries(self):
        """Generate registry entries for folders"""
        reg_lines = []
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell]')
        reg_lines.append('')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}]')
        reg_lines.append('"MUIVerb"="TonieToolbox"')
        reg_lines.append(f'"Icon"="{self.icon_path}"')
        reg_lines.append('"subcommands"=""')
        reg_lines.append('')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell]')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\a_ConvertFolder]')
        reg_lines.append('@="Convert Folder to .taf (recursive)"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\a_ConvertFolder\\command]')
        reg_lines.append(f'@="{self._reg_escape(self.convert_folder_cmd)}"')
        reg_lines.append('')
        if self.upload_enabled:
            # Upload    
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\b_UploadFolder]')
            reg_lines.append('@="Convert Folder to .taf and Upload (recursive)"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\b_UploadFolder\\command]')
            reg_lines.append(f'@="{self._reg_escape(self.upload_folder_cmd)}"')
            reg_lines.append('')
            # Upload + Artwork
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\c_UploadFolderArtwork]')
            reg_lines.append('@="Convert Folder to .taf and Upload + Artwork (recursive)"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\c_UploadFolderArtwork\\command]')
            reg_lines.append(f'@="{self._reg_escape(self.upload_folder_artwork_cmd)}"')
            reg_lines.append('')
            # Upload + Artwork + JSON
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\d_UploadFolderArtworkJson]')
            reg_lines.append('@="Convert Folder to .taf and Upload + Artwork + JSON (recursive)"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\d_UploadFolderArtworkJson\\command]')
            reg_lines.append(f'@="{self._reg_escape(self.upload_folder_artwork_json_cmd)}"')
            reg_lines.append('')
        return reg_lines

    def _generate_uninstaller_entries(self):
        """Generate registry entries for uninstaller"""
        unreg_lines = [
            'Windows Registry Editor Version 5.00',
            '',
        ]
        
        for ext in SUPPORTED_EXTENSIONS:
            ext = ext.lower().lstrip('.')
            unreg_lines.append(f'[-HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}]')
            unreg_lines.append('')
            
        unreg_lines.append(f'[-HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}]')
        unreg_lines.append('')
        unreg_lines.append(f'[-HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}]')
        
        return unreg_lines
    
    def generate_registry_files(self):
        """
        Generate Windows registry files for TonieToolbox context menu integration.
        Returns the path to the installer registry file.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        reg_lines = [
            'Windows Registry Editor Version 5.00',
            '',
        ]
        
        # Add entries for audio extensions
        reg_lines.extend(self._generate_audio_extensions_entries())
        
        # Add entries for .taf files
        reg_lines.extend(self._generate_taf_file_entries())
        
        # Add entries for folders
        reg_lines.extend(self._generate_folder_entries())
        
        # Write the installer .reg file
        reg_path = os.path.join(self.output_dir, 'tonietoolbox_context.reg')
        with open(reg_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(reg_lines))
        
        # Generate and write the uninstaller .reg file
        unreg_lines = self._generate_uninstaller_entries()
        unreg_path = os.path.join(self.output_dir, 'remove_tonietoolbox_context.reg')
        with open(unreg_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unreg_lines))
        
        return reg_path
        
    def install_registry_files(self, uninstall=False):
        """
        Import the generated .reg file into the Windows registry with UAC elevation.
        If uninstall is True, imports the uninstaller .reg file.
        
        Returns:
            bool: True if registry import was successful, False otherwise.
        """
        import subprocess
        reg_file = os.path.join(
            self.output_dir,
            'remove_tonietoolbox_context.reg' if uninstall else 'tonietoolbox_context.reg'
        )
        if not os.path.exists(reg_file):
            logger.error(f"Registry file not found: {reg_file}")
            return False
    
        ps_command = (
            f"Start-Process reg.exe -ArgumentList @('import', '{reg_file}') -Verb RunAs -Wait -PassThru"
        )
        try:
            result = subprocess.run(["powershell.exe", "-Command", ps_command], check=False, 
                                   capture_output=True, text=True)
                        
            if result.returncode == 0:
                logger.info(f"{'Uninstallation' if uninstall else 'Installation'} registry import completed.")
                return True
            else:
                logger.error(f"Registry import command failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to import registry file: {e}")
            return False

    @classmethod
    def install(cls):
        """
        Generate registry files and install them with UAC elevation.
        """
        instance = cls()
        instance.generate_registry_files()
        if instance.install_registry_files(uninstall=False):
            logger.info("Integration installed successfully.")
            return True
        else:
            logger.error("Integration installation failed.")
            return False

    @classmethod
    def uninstall(cls):
        """
        Generate registry files and uninstall them with UAC elevation.
        """
        instance = cls()
        instance.generate_registry_files()
        if instance.install_registry_files(uninstall=True):
            logger.info("Integration uninstalled successfully.")
            return True
        else:
            logger.error("Integration uninstallation failed.")
            return False