import platform

def handle_integration(args):
    import platform
    if platform.system() == 'Windows':
        from .integration_windows import WindowsClassicContextMenuIntegration as ContextMenuIntegration
        if args.install_integration:
            ContextMenuIntegration.install()
        elif args.uninstall_integration:
            ContextMenuIntegration.uninstall()
    elif platform.system() == 'Darwin':
        from .integration_macos import MacOSContextMenuIntegration as ContextMenuIntegration
        if args.install_integration:
            ContextMenuIntegration.install()
        elif args.uninstall_integration:
            ContextMenuIntegration.uninstall()
    elif platform.system() == 'Linux':
        raise NotImplementedError("Context menu integration is not supported on Linux YET. But Soon™")
    else:
        raise NotImplementedError(f"Context menu integration is not supported on this OS: {platform.system()}")