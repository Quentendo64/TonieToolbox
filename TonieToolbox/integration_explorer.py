import os
import sys
import json
from .constants import SUPPORTED_EXTENSIONS, ICON
from .logger import get_logger

logger = get_logger('integration_explorer')

class WindowsClassicContextMenuIntegration:
    """
    Class to generate Windows registry entries for TonieToolbox "classic" context menu integration.
    Adds a 'TonieToolbox' cascade menu for supported audio files, .taf files, and folders.
    """
    def __init__(self):
        self.exe_path = os.path.join(sys.prefix, 'Scripts', 'tonietoolbox.exe')
        self.exe_path_reg = self.exe_path.replace('\\', r'\\\\')
        self.output_dir = os.path.join(os.path.expanduser('~'), '.tonietoolbox')
        self.icon_path = os.path.join(self.output_dir, 'icon.ico').replace('\\', r'\\')
        self.cascade_name = 'TonieToolbox'
        self.entry_is_separator = '"CommandFlags"=dword:00000008'
        self.show_uac = '"CommandFlags"=dword:00000010'
        self.separator_below = '"CommandFlags"=dword:00000040'
        self.separator_above = '"CommandFlags"=dword:00000020'
        self.error_handling = r' && if %ERRORLEVEL% neq 0 (echo Error: Command failed with error code %ERRORLEVEL% && pause && exit /b %ERRORLEVEL%) else (echo Command completed successfully && ping -n 2 127.0.0.1 > nul)'
        self.show_info_error_handling = r' && if %ERRORLEVEL% neq 0 (echo Error: Command failed with error code %ERRORLEVEL% && pause && exit /b %ERRORLEVEL%) else (echo. && echo Press any key to close this window... && pause > nul)'
        self._setup_upload()
        self._setup_commands()

    
    def _setup_commands(self):
        """Set up all command strings for registry entries"""
        # Command strings for audio files
        self.convert_cmd = f'cmd.exe /c \\"echo Running TonieToolbox convert command... && \\"{self.exe_path_reg}\\" --output-to-source \\"%1\\"{self.error_handling}\\"'
        self.upload_cmd = f'cmd.exe /c \\"echo Running TonieToolbox convert and upload command... && \\"{self.exe_path_reg}\\" --output-to-source --upload \\"%1\\"{self.error_handling}\\"'
        self.upload_artwork_cmd = f'cmd.exe /c \\"echo Running TonieToolbox convert, upload and artwork command... && \\"{self.exe_path_reg}\\" --output-to-source --upload --include-artwork \\"%1\\"{self.error_handling}\\"'
        self.upload_artwork_json_cmd = f'cmd.exe /c \\"echo Running TonieToolbox convert, upload, artwork and JSON command... && \\"{self.exe_path_reg}\\" --output-to-source --upload --include-artwork --create-custom-json \\"%1\\"{self.error_handling}\\"'
        
        # Command strings for .taf files
        self.show_info_cmd = f'cmd.exe /k \\"echo Running TonieToolbox info command... && \\"{self.exe_path_reg}\\" --info --silent \\"%1\\" && echo. && pause && exit > nul\\"'
        self.extract_opus_cmd = f'cmd.exe /c \\"echo Running TonieToolbox split command... && \\"{self.exe_path_reg}\\" --split --silent \\"%1\\"{self.error_handling}\\"'
        self.upload_taf_cmd = f'cmd.exe /c \\"echo Running TonieToolbox upload command... && \\"{self.exe_path_reg}\\" --upload \\"%1\\"{self.error_handling}\\"'
        self.upload_taf_artwork_cmd = f'cmd.exe /c \\"echo Running TonieToolbox upload and artwork command... && \\"{self.exe_path_reg}\\" --upload --include-artwork \\"%1\\"{self.error_handling}\\"'
        self.upload_taf_artwork_json_cmd = f'cmd.exe /c \\"echo Running TonieToolbox upload, artwork and JSON command... && \\"{self.exe_path_reg}\\" --upload --include-artwork --create-custom-json \\"%1\\"{self.error_handling}\\"'
        self.compare_taf_cmd = f'cmd.exe /k \\"echo Running TonieToolbox compare command... && echo %1 && echo %2 && \\"{self.exe_path_reg}\\" --silent --compare \\"%1\\" \\"%2\\" && echo. && pause && exit > nul\\"'

        # Command string for folders
        self.convert_folder_cmd = f'cmd.exe /c \\"echo Running TonieToolbox recursive folder convert command... && \\"{self.exe_path_reg}\\" --recursive --output-to-source \\"%1\\"{self.error_handling}\\"'
        self.upload_folder_cmd = f'cmd.exe /c \\"echo Running TonieToolbox recursive folder convert and upload command... && \\"{self.exe_path_reg}\\" --recursive --output-to-source --upload \\"%1\\"{self.error_handling}\\"'
        self.upload_folder_artwork_cmd = f'cmd.exe /c \\"echo Running TonieToolbox recursive folder convert, upload and artwork command... && \\"{self.exe_path_reg}\\" --recursive --output-to-source --upload --include-artwork \\"%1\\"{self.error_handling}\\"'
        self.upload_folder_artwork_json_cmd = f'cmd.exe /c \\"echo Running TonieToolbox recursive folder convert, upload, artwork and JSON command... && \\"{self.exe_path_reg}\\" --recursive --output-to-source --upload --include-artwork --create-custom-json \\"%1\\"{self.error_handling}\\"'

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
        try:
            config = self._load_config()        
            upload_config = config.get('upload', {})        
            self.upload_urls = upload_config.get('url', [])
            self.username = upload_config.get('username', '')
            self.password = upload_config.get('password', '')
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
            if not self.client_cert_authentication and not self.basic_authentication:
                self.none_authentication = True
            self.upload_url = self.upload_urls[0] if self.upload_urls else ''
            return True if self.client_cert_authentication or self.basic_authentication or self.none_authentication and self.upload_url else False
        except FileNotFoundError:
            logger.debug("Configuration file not found. Skipping upload setup.")
            return False
        except json.JSONDecodeError:
            logger.debug("Error decoding JSON in configuration file. Skipping upload setup.")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error while loading configuration: {e}")
            return False

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
            reg_lines.append(f'@="{self.convert_cmd}"')
            reg_lines.append(f'"{self.entry_is_separator}"')
            reg_lines.append('')
                    
            # Upload
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\b_Upload]')
            reg_lines.append('@="Convert File to .taf and Upload"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\b_Upload\\command]')
            reg_lines.append(f'@="{self.upload_cmd}"')
            reg_lines.append('')
            
            # Upload + Artwork
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\c_UploadArtwork]')
            reg_lines.append('@="Convert File to .taf and Upload + Artwork"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\c_UploadArtwork\\command]')
            reg_lines.append(f'@="{self.upload_artwork_cmd}"')
            reg_lines.append('')
            
            # Upload + Artwork + JSON
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\d_UploadArtworkJson]')
            reg_lines.append('@="Convert File to .taf and Upload + Artwork + JSON"')
            reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.{ext}\\shell\\{self.cascade_name}\\shell\\d_UploadArtworkJson\\command]')
            reg_lines.append(f'@="{self.upload_artwork_json_cmd}"')
            reg_lines.append('')
        
        return reg_lines
    
    def _generate_taf_file_entries(self):
        """Generate registry entries for .taf files"""
        reg_lines = []
        
        # .taf files cascade
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
        reg_lines.append(f'@="{self.show_info_cmd}"')
        reg_lines.append('')
        
        # Extract Opus Tracks
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\b_ExtractOpus]')
        reg_lines.append('@="Extract Opus Tracks"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\b_ExtractOpus\\command]')
        reg_lines.append(f'@="{self.extract_opus_cmd}"')
        reg_lines.append('')
        
        # Upload
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\c_Upload]')
        reg_lines.append('@="Upload"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\c_Upload\\command]')
        reg_lines.append(f'@="{self.upload_taf_cmd}"')
        reg_lines.append('')
        
        # Upload + Artwork
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\d_UploadArtwork]')
        reg_lines.append('@="Upload + Artwork"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\d_UploadArtwork\\command]')
        reg_lines.append(f'@="{self.upload_taf_artwork_cmd}"')
        reg_lines.append('')
        
        # Upload + Artwork + JSON
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\e_UploadArtworkJson]')
        reg_lines.append('@="Upload + Artwork + JSON"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\e_UploadArtworkJson\\command]')
        reg_lines.append(f'@="{self.upload_taf_artwork_json_cmd}"')
        reg_lines.append('')
        
        # Compare TAF Files
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\f_CompareTaf]')
        reg_lines.append('@="Compare with another .taf file"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.taf\\shell\\{self.cascade_name}\\shell\\f_CompareTaf\\command]')
        reg_lines.append(f'@="{self.compare_taf_cmd}"')
        reg_lines.append('')
        
        return reg_lines
    
    def _generate_folder_entries(self):
        """Generate registry entries for folders"""
        reg_lines = []
        
        # Folder context menu
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
        reg_lines.append(f'@="{self.convert_folder_cmd}"')
        reg_lines.append(f'"CommandFlags"=dword:00000040')
        reg_lines.append('')
        
        # Upload    
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\b_UploadFolder]')
        reg_lines.append('@="Convert Folder to .taf and Upload (recursive)"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\b_UploadFolder\\command]')
        reg_lines.append(f'@="{self.upload_folder_cmd}"')
        reg_lines.append('')
        
        # Upload + Artwork
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\c_UploadFolderArtwork]')
        reg_lines.append('@="Convert Folder to .taf and Upload + Artwork (recursive)"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\c_UploadFolderArtwork\\command]')
        reg_lines.append(f'@="{self.upload_folder_artwork_cmd}"')
        reg_lines.append('')
        
        # Upload + Artwork + JSON
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\d_UploadFolderArtworkJson]')
        reg_lines.append('@="Convert Folder to .taf and Upload + Artwork + JSON (recursive)"')
        reg_lines.append(f'[HKEY_CLASSES_ROOT\\Directory\\shell\\{self.cascade_name}\\shell\\d_UploadFolderArtworkJson\\command]')
        reg_lines.append(f'@="{self.upload_folder_artwork_json_cmd}"')
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



