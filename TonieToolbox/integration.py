import platform
from .logger import get_logger

logger = get_logger(__name__)

def handle_integration(args):
    import platform
    if platform.system() == 'Windows':
        from .integration_windows import WindowsClassicContextMenuIntegration as ContextMenuIntegration
        if args.install_integration:
            success = ContextMenuIntegration.install()
            if success:
                logger.info("Integration installed successfully.")
                return True
            else:
                logger.error("Integration installation failed.")
                return False
        elif args.uninstall_integration:
            success = ContextMenuIntegration.uninstall()
            if success:
                logger.info("Integration uninstalled successfully.")
                return True
            else:
                logger.error("Integration uninstallation failed.")
                return False
    elif platform.system() == 'Darwin':
        from .integration_macos import MacOSContextMenuIntegration as ContextMenuIntegration
        if args.install_integration:
            success = ContextMenuIntegration.install()
            if success:
                logger.info("Integration installed successfully.")
                return True
            else:
                logger.error("Integration installation failed.")
                return False
        elif args.uninstall_integration:
            success = ContextMenuIntegration.uninstall()
            if success:
                logger.info("Integration uninstalled successfully.")
                return True
            else:
                logger.error("Integration uninstallation failed.")
                return False
    elif platform.system() == 'Linux':
        raise NotImplementedError("Context menu integration is not supported on Linux YET. But Soon™")
    else:
        raise NotImplementedError(f"Context menu integration is not supported on this OS: {platform.system()}")
    
def handle_config():
    """Opens the configuration file in the default text editor."""
    import os
    import platform
    import subprocess

    config_path = os.path.join(os.path.expanduser("~"), ".tonietoolbox", "config.json")

    if not os.path.exists(config_path):
        logger.info(f"Configuration file not found at {config_path}.")
        logger.info("Creating a new configuration file. Using --install-integration will create a new config file.")
        return
    if platform.system() == "Windows":
        os.startfile(config_path)
    elif platform.system() == "Darwin":
        subprocess.call(["open", config_path])
    elif platform.system() == "Linux":
        subprocess.call(["xdg-open", config_path])
    else:
        logger.error(f"Unsupported OS: {platform.system()}")