#!/usr/bin/python3
"""
Integration for KDE with service menus.
This module generates KDE service menu entries (.desktop files) to add a 'TonieToolbox' submenu.
"""
import os
import sys
import json
from .constants import SUPPORTED_EXTENSIONS, CONFIG_TEMPLATE, ICON_BASE64
from .logger import get_logger

logger = get_logger(__name__)

class KDEServiceMenuIntegration:
    """
    Class to generate KDE service menu entries for TonieToolbox integration.
    Creates .desktop files in ~/.local/share/kservices5/ServiceMenus/ for supported audio files, .taf files, and folders.
    """
    def __init__(self):
        # Find tonietoolbox executable
        self.exe_path = self._find_executable()
        self.output_dir = os.path.join(os.path.expanduser('~'), '.tonietoolbox')
        # Try KDE6 first, then KDE5
        kde6_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'kio', 'servicemenus')
        kde5_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'kservices5', 'ServiceMenus')
        
        # Check KDE version and use appropriate directory
        kde_version = os.environ.get('KDE_SESSION_VERSION', '5')
        if kde_version == '6':
            self.service_menu_dir = kde6_dir
        else:
            self.service_menu_dir = kde5_dir
            
        # Application directory for .desktop application files
        self.application_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'applications')
        self.icon_path = os.path.join(self.output_dir, 'icon.png')
        
        # Load or create configuration
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

    def _find_executable(self):
        """Find the tonietoolbox executable."""
        # Check common locations
        possible_paths = [
            os.path.join(sys.prefix, 'bin', 'tonietoolbox'),
            '/usr/local/bin/tonietoolbox',
            '/usr/bin/tonietoolbox',
            os.path.expanduser('~/.local/bin/tonietoolbox')
        ]
        
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        # Try which command
        import subprocess
        try:
            result = subprocess.run(['which', 'tonietoolbox'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Fallback to just 'tonietoolbox' and hope it's in PATH
        return 'tonietoolbox'

    def _build_cmd(self, base_args, use_upload=False, use_artwork=False, use_json=False, use_compare=False, use_info=False, use_play=False, is_recursive=False, is_split=False, is_folder=False, keep_open=False, log_to_file=False):
        """Dynamically build command strings for service menu entries."""
        # Build the tonietoolbox command
        tonietoolbox_cmd = f'{self.exe_path} {base_args}'
        
        if log_to_file:
            tonietoolbox_cmd += ' --log-file'
        if is_recursive:
            tonietoolbox_cmd += ' --recursive'
        tonietoolbox_cmd += ' --output-to-source'
        if use_info:
            tonietoolbox_cmd += ' --info'
        if use_play:
            tonietoolbox_cmd += ' --play'
        if is_split:
            tonietoolbox_cmd += ' --split'
        if use_compare:
            tonietoolbox_cmd += ' --compare'
        if use_upload:
            tonietoolbox_cmd += f' --upload "{self.upload_url}"'
            if self.basic_authentication_cmd:
                tonietoolbox_cmd += f' {self.basic_authentication_cmd}'
            elif self.client_cert_cmd:
                tonietoolbox_cmd += f' {self.client_cert_cmd}'
            if getattr(self, "ignore_ssl_verify", False):
                tonietoolbox_cmd += ' --ignore-ssl-verify'
        if use_artwork:
            tonietoolbox_cmd += ' --include-artwork'
        if use_json:
            tonietoolbox_cmd += ' --create-custom-json'
        
        return tonietoolbox_cmd

    def _get_log_level_arg(self):
        """Return the correct log level argument for TonieToolbox CLI based on self.log_level."""
        level = str(self.log_level).strip().upper()
        if level == 'DEBUG':
            return '--debug'
        elif level == 'INFO':
            return '--info'
        return '--silent'

    def _setup_commands(self):
        """Set up all command strings for service menu entries dynamically."""
        log_level_arg = self._get_log_level_arg()
        
        # Audio file commands
        self.convert_cmd = self._build_cmd(f'{log_level_arg}', log_to_file=self.log_to_file)
        self.upload_cmd = self._build_cmd(f'{log_level_arg}', use_upload=True, log_to_file=self.log_to_file)
        self.upload_artwork_cmd = self._build_cmd(f'{log_level_arg}', use_upload=True, use_artwork=True, log_to_file=self.log_to_file)
        self.upload_artwork_json_cmd = self._build_cmd(f'{log_level_arg}', use_upload=True, use_artwork=True, use_json=True, log_to_file=self.log_to_file)

        # .taf file commands
        info_log_level = '--info' if self.log_level.upper() == 'SILENT' else log_level_arg
        self.show_info_cmd = self._build_cmd(info_log_level, use_info=True, keep_open=True, log_to_file=self.log_to_file)
        self.extract_opus_cmd = self._build_cmd(log_level_arg, is_split=True, log_to_file=self.log_to_file)
        self.play_cmd = self._build_cmd(log_level_arg,use_play=True, keep_open=True, log_to_file=self.log_to_file)
        self.upload_taf_cmd = self._build_cmd(log_level_arg, use_upload=True, log_to_file=self.log_to_file)
        self.upload_taf_artwork_cmd = self._build_cmd(log_level_arg, use_upload=True, use_artwork=True, log_to_file=self.log_to_file)
        self.upload_taf_artwork_json_cmd = self._build_cmd(log_level_arg, use_upload=True, use_artwork=True, use_json=True, log_to_file=self.log_to_file)

        # Folder commands
        self.convert_folder_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, log_to_file=self.log_to_file)
        self.upload_folder_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, use_upload=True, log_to_file=self.log_to_file)
        self.upload_folder_artwork_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, use_upload=True, use_artwork=True, log_to_file=self.log_to_file)
        self.upload_folder_artwork_json_cmd = self._build_cmd(f'{log_level_arg}', is_recursive=True, is_folder=True, use_upload=True, use_artwork=True, use_json=True, log_to_file=self.log_to_file)

    def _apply_config_template(self):
        """Apply the default configuration template if config.json is missing or invalid. Extracts the icon from base64 if not present."""
        config_path = os.path.join(self.output_dir, 'config.json')
        icon_path = os.path.join(self.output_dir, 'icon.png')
        os.makedirs(self.output_dir, exist_ok=True)    
        # Extract icon to PNG for KDE (KDE prefers PNG over ICO)
        if not os.path.exists(icon_path):
            self._base64_to_png(ICON_BASE64, icon_path)
        if not os.path.exists(self.icon_path):
            self.icon_path = 'audio-x-generic'
        
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump(CONFIG_TEMPLATE, f, indent=4)
            logger.debug(f"Default configuration created at {config_path}")
            return CONFIG_TEMPLATE
        else:
            logger.debug(f"Configuration file found at {config_path}")
            return self._load_config()

    def _base64_to_png(self, base64_data, output_path):
        """Convert base64 ICO data to PNG format for KDE."""
        try:
            import base64
            from PIL import Image
            import io
            ico_data = base64.b64decode(base64_data)
            with Image.open(io.BytesIO(ico_data)) as img:
                img.save(output_path, 'PNG')
                
        except ImportError:
            import base64
            ico_data = base64.b64decode(base64_data)
            ico_path = output_path.replace('.png', '.ico')
            self._base64_to_ico(base64_data, ico_path)
            self.icon_path = ico_path
        except Exception as e:
            logger.warning(f"Failed to convert icon: {e}")
            self.icon_path = 'applications-multimedia'

    def _base64_to_ico(self, base64_string, output_path):
        """
        Convert a base64 string back to an ICO file
        """
        import base64
        ico_bytes = base64.b64decode(base64_string)
        
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, "wb") as ico_file:
            ico_file.write(ico_bytes)
            
        return output_path

    def _load_config(self):
        """Load configuration settings from config.json"""
        config_path = os.path.join(self.output_dir, 'config.json')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            content = f.read().strip()
            if not content:
                # Empty file, return default config
                logger.debug("Config file is empty, using default template")
                return CONFIG_TEMPLATE
            config = json.loads(content)
        
        return config

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
                cert_path = os.path.expanduser(self.client_cert_path)
                key_path = os.path.expanduser(self.client_cert_key_path)
                self.client_cert_cmd = f'--client-cert "{cert_path}" --client-key "{key_path}"'
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

    def _generate_audio_extensions_entries(self):
        """Generate KDE service menu entries for supported audio file extensions"""
        mime_types = set()
        for ext in SUPPORTED_EXTENSIONS:
            ext = ext.lower().lstrip('.')
            # Map common extensions to MIME types
            mime_map = {
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav',
                'flac': 'audio/flac', 
                'ogg': 'audio/ogg',
                'opus': 'audio/opus',
                'aac': 'audio/aac',
                'm4a': 'audio/mp4',
                'wma': 'audio/x-ms-wma',
                'aiff': 'audio/x-aiff',
                'mp2': 'audio/mpeg',
                'mp4': 'audio/mp4',
                'webm': 'audio/webm',
                'mka': 'audio/x-matroska',
                'ape': 'audio/x-ape'
            }
            if ext in mime_map:
                mime_types.add(mime_map[ext])
        mime_types_list = sorted(list(mime_types))
        mime_types_str = ';'.join(mime_types_list) + ';'
        
        actions = ["convert"]
        if self.upload_enabled:
            actions.extend(["upload", "upload_artwork", "upload_artwork_json"])
        actions_str = ';'.join(actions)
        
        desktop_content = f"""[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType={mime_types_str}
Actions={actions_str}
X-KDE-Submenu=TonieToolbox
X-KDE-Submenu[de]=TonieToolbox
Icon={self.icon_path}

[Desktop Action convert]
Name=Convert File to .taf
Name[de]=Datei zu .taf konvertieren
Icon={self.icon_path}
Exec=konsole -e {self.convert_cmd} %f
"""
        
        if self.upload_enabled:
            desktop_content += f"""
[Desktop Action upload]
Name=Convert File to .taf and Upload
Name[de]=Datei zu .taf konvertieren und hochladen
Icon={self.icon_path}
Exec=konsole -e {self.upload_cmd} %f

[Desktop Action upload_artwork]
Name=Convert File to .taf and Upload + Artwork
Name[de]=Datei zu .taf konvertieren und hochladen + Artwork
Icon={self.icon_path}
Exec=konsole -e {self.upload_artwork_cmd} %f

[Desktop Action upload_artwork_json]
Name=Convert File to .taf and Upload + Artwork + JSON
Name[de]=Datei zu .taf konvertieren und hochladen + Artwork + JSON
Icon={self.icon_path}
Exec=konsole -e {self.upload_artwork_json_cmd} %f
"""
        
        return 'tonietoolbox-audio.desktop', desktop_content

    def _generate_taf_file_entries(self):
        """Generate KDE service menu entries for .taf files"""
        desktop_content = f"""[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=audio/x-tonie;
Actions=show_info;extract_opus;"""
        
        if self.upload_enabled:
            desktop_content += "upload_taf;upload_taf_artwork;upload_taf_artwork_json;"
        
        desktop_content += f"""
X-KDE-Submenu=TonieToolbox
X-KDE-Submenu[de]=TonieToolbox
Icon={self.icon_path}

[Desktop Action show_info]
Name=Show Info
Name[de]=Info anzeigen
Icon={self.icon_path}
Exec=konsole --noclose -e {self.show_info_cmd} %f

[Desktop Action extract_opus]
Name=Extract Opus Tracks
Name[de]=Opus-Spuren extrahieren
Icon={self.icon_path}
Exec=konsole -e {self.extract_opus_cmd} %f
"""
        
        if self.upload_enabled:
            desktop_content += f"""
[Desktop Action upload_taf]
Name=Upload
Name[de]=Hochladen
Icon={self.icon_path}
Exec=konsole -e {self.upload_taf_cmd} %f

[Desktop Action upload_taf_artwork]
Name=Upload + Artwork
Name[de]=Hochladen + Artwork
Icon={self.icon_path}
Exec=konsole -e {self.upload_taf_artwork_cmd} %f

[Desktop Action upload_taf_artwork_json]
Name=Upload + Artwork + JSON
Name[de]=Hochladen + Artwork + JSON
Icon={self.icon_path}
Exec=konsole -e {self.upload_taf_artwork_json_cmd} %f
"""
        
        return 'tonietoolbox-taf.desktop', desktop_content

    def _generate_folder_entries(self):
        """Generate KDE service menu entries for folders"""
        desktop_content = f"""[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=inode/directory;
Actions=convert_folder;"""
        
        if self.upload_enabled:
            desktop_content += "upload_folder;upload_folder_artwork;upload_folder_artwork_json;"
        
        desktop_content += f"""
X-KDE-Submenu=TonieToolbox
X-KDE-Submenu[de]=TonieToolbox
Icon={self.icon_path}

[Desktop Action convert_folder]
Name=Convert Folder to .taf (recursive)
Name[de]=Ordner zu .taf konvertieren (rekursiv)
Icon={self.icon_path}
Exec=konsole -e {self.convert_folder_cmd} %f
"""
        
        if self.upload_enabled:
            desktop_content += f"""
[Desktop Action upload_folder]
Name=Convert Folder to .taf and Upload (recursive)
Name[de]=Ordner zu .taf konvertieren und hochladen (rekursiv)
Icon={self.icon_path}
Exec=konsole -e {self.upload_folder_cmd} %f

[Desktop Action upload_folder_artwork]
Name=Convert Folder to .taf and Upload + Artwork (recursive)
Name[de]=Ordner zu .taf konvertieren und hochladen + Artwork (rekursiv)
Icon={self.icon_path}
Exec=konsole -e {self.upload_folder_artwork_cmd} %f

[Desktop Action upload_folder_artwork_json]
Name=Convert Folder to .taf and Upload + Artwork + JSON (recursive)
Name[de]=Ordner zu .taf konvertieren und hochladen + Artwork + JSON (rekursiv)
Icon={self.icon_path}
Exec=konsole -e {self.upload_folder_artwork_json_cmd} %f
"""
        
        return 'tonietoolbox-folder.desktop', desktop_content
    
    def generate_service_menu_files(self):
        """
        Generate KDE service menu files for TonieToolbox integration.
        Returns the paths to the generated service menu files.
        """
        os.makedirs(self.service_menu_dir, exist_ok=True)
        generated_files = []
        
        # Generate entries for audio extensions
        filename, content = self._generate_audio_extensions_entries()
        file_path = os.path.join(self.service_menu_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(file_path, 0o755)  # Make executable
        generated_files.append(file_path)
        
        # Generate entries for .taf files
        filename, content = self._generate_taf_file_entries()
        file_path = os.path.join(self.service_menu_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(file_path, 0o755)  # Make executable
        generated_files.append(file_path)
        
        # Generate entries for folders
        filename, content = self._generate_folder_entries()
        file_path = os.path.join(self.service_menu_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(file_path, 0o755)  # Make executable
        generated_files.append(file_path)
        
        return generated_files
    
    def _generate_application_desktop_file(self):
        """Generate desktop application file for opening .taf files with double-click"""
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=TonieToolbox Player
Name[de]=TonieToolbox Player
Comment=Play Tonie audio files with TonieToolbox
Comment[de]=Tonie-Audiodateien mit TonieToolbox abspielen
GenericName=Tonie Audio Player
GenericName[de]=Tonie Audio Player
Exec=konsole -e {self.play_cmd} %f
Icon={self.icon_path}
Terminal=false
NoDisplay=true
MimeType=audio/x-tonie;
Categories=AudioVideo;Audio;Player;
"""
        return 'tonietoolbox-player.desktop', desktop_content
    
    def generate_application_file(self):
        """Generate and install the desktop application file"""
        os.makedirs(self.application_dir, exist_ok=True)
        
        filename, content = self._generate_application_desktop_file()
        file_path = os.path.join(self.application_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(file_path, 0o755)  # Make executable
        
        return file_path
        
    def remove_service_menu_files(self):
        """
        Remove TonieToolbox service menu files.
        """
        files_to_remove = [
            'tonietoolbox-audio.desktop',
            'tonietoolbox-taf.desktop', 
            'tonietoolbox-folder.desktop'
        ]
        
        removed_files = []
        for filename in files_to_remove:
            file_path = os.path.join(self.service_menu_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    removed_files.append(file_path)
                    logger.info(f"Removed service menu file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove service menu file {file_path}: {e}")
        
        return removed_files
    
    def remove_application_file(self):
        """Remove the TonieToolbox player application desktop file"""
        app_filename = 'tonietoolbox-player.desktop'
        app_file_path = os.path.join(self.application_dir, app_filename)
        
        if os.path.exists(app_file_path):
            try:
                os.remove(app_file_path)
                logger.info(f"Removed application file: {app_file_path}")
                return app_file_path
            except Exception as e:
                logger.error(f"Failed to remove application file {app_file_path}: {e}")
        return None

    def create_taf_mime_type(self):
        """Create MIME type definition for .taf files"""
        mime_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'mime')
        packages_dir = os.path.join(mime_dir, 'packages')
        os.makedirs(packages_dir, exist_ok=True)
        
        # Create MIME type definition with higher priority for file extension
        mime_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="audio/x-tonie">
    <comment>Tonie Audio File</comment>
    <comment xml:lang="de">Tonie-Audiodatei</comment>
    <icon name="audio-x-generic"/>
    <glob pattern="*.taf" weight="100"/>
    <glob pattern="*.TAF" weight="100"/>
  </mime-type>
</mime-info>'''
        
        mime_xml_path = os.path.join(packages_dir, 'audio-x-tonie.xml')
        with open(mime_xml_path, 'w', encoding='utf-8') as f:
            f.write(mime_xml_content)
        
        # Update MIME database
        import subprocess
        try:
            subprocess.run(['update-mime-database', mime_dir], check=True, capture_output=True)
            logger.info(f"Created MIME type definition: {mime_xml_path}")
            return mime_xml_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update MIME database: {e}")
            return None
        except FileNotFoundError:
            logger.warning("update-mime-database command not found")
            return None

    def remove_taf_mime_type(self):
        """Remove MIME type definition for .taf files"""
        mime_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'mime')
        mime_xml_path = os.path.join(mime_dir, 'packages', 'audio-x-tonie.xml')
        
        if os.path.exists(mime_xml_path):
            try:
                os.remove(mime_xml_path)
                # Update MIME database
                import subprocess
                subprocess.run(['update-mime-database', mime_dir], check=True, capture_output=True)
                logger.info(f"Removed MIME type definition: {mime_xml_path}")
                return mime_xml_path
            except Exception as e:
                logger.error(f"Failed to remove MIME type definition: {e}")
        return None

    def _update_kde_cache(self):
        """Update KDE's service menu cache."""
        import subprocess
        cache_updated = False
        
        # KDE6 cache update
        try:
            result = subprocess.run(['kbuildsycoca6'], check=False, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Updated KDE6 service menu cache")
                cache_updated = True
            else:
                logger.debug(f"kbuildsycoca6 failed: {result.stderr}")
        except FileNotFoundError:
            pass
        
        # KDE5 cache update (fallback)
        if not cache_updated:
            try:
                result = subprocess.run(['kbuildsycoca5'], check=False, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Updated KDE5 service menu cache")
                    cache_updated = True
                else:
                    logger.debug(f"kbuildsycoca5 failed: {result.stderr}")
            except FileNotFoundError:
                pass
        
        if not cache_updated:
            logger.warning("Could not find kbuildsycoca command. Service menus may require logout/login to appear.")
            logger.info("You can try manually running: kbuildsycoca6 or kbuildsycoca5")

    @classmethod
    def install(cls):
        """
        Generate service menu files and install them.
        """
        try:
            instance = cls()
            # Create MIME type definition for .taf files
            mime_file = instance.create_taf_mime_type()
            generated_files = instance.generate_service_menu_files()
            app_file = instance.generate_application_file()
            generated_files.append(app_file)
            if mime_file:
                generated_files.append(mime_file)
            instance._update_kde_cache()
            logger.info(f"KDE integration installed successfully. Generated files: {generated_files}")
            print(f"KDE integration installed successfully!")
            print(f"Generated service menu files:")
            for file_path in generated_files:
                print(f"  {file_path}")
            print("Service menus should appear in the right-click context menu.")
            print("Double-click .taf files will now play them with TonieToolbox.")
            print("")
            print("Note: If the menus don't appear immediately:")
            print("  1. Try restarting Dolphin file manager")
            print("  2. Or log out and back in to refresh all KDE services")
            print("  3. For immediate effect, you can run: kbuildsycoca6")
            return True
        except Exception as e:
            logger.error(f"KDE integration installation failed: {e}")
            print(f"KDE integration installation failed: {e}")
            return False

    @classmethod
    def uninstall(cls):
        """
        Remove service menu files and uninstall integration.
        """
        try:
            instance = cls()
            removed_files = instance.remove_service_menu_files()
            app_file = instance.remove_application_file()
            if app_file:
                removed_files.append(app_file)
            # Remove MIME type definition
            mime_file = instance.remove_taf_mime_type()
            if mime_file:
                removed_files.append(mime_file)
            instance._update_kde_cache()
            logger.info(f"KDE integration uninstalled successfully. Removed files: {removed_files}")
            print(f"KDE integration uninstalled successfully!")
            if removed_files:
                print(f"Removed service menu files:")
                for file_path in removed_files:
                    print(f"  {file_path}")
            else:
                print("No service menu files were found to remove.")
            return True
        except Exception as e:
            logger.error(f"KDE integration uninstallation failed: {e}")
            print(f"KDE integration uninstallation failed: {e}")
            return False