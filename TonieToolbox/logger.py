#!/usr/bin/python3
"""
Logging configuration for the TonieToolbox package.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Define log levels and their names
TRACE = 5  # Custom level for ultra-verbose debugging
logging.addLevelName(TRACE, 'TRACE')

# Create a method for the TRACE level
def trace(self: logging.Logger, message: str, *args, **kwargs) -> None:
    """Log a message with TRACE level (more detailed than DEBUG)"""
    if self.isEnabledFor(TRACE):
        self.log(TRACE, message, *args, **kwargs)

# Add trace method to the Logger class
logging.Logger.trace = trace

def get_log_file_path() -> Path:
    """
    Get the path to the log file in the .tonietoolbox folder with timestamp.
    
    Returns:
        Path: Path to the log file
    """
    # Create .tonietoolbox folder in user's home directory if it doesn't exist
    log_dir = Path.home() / '.tonietoolbox' / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamp string for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define log file path with timestamp
    log_file = log_dir / f'tonietoolbox_{timestamp}.log'
    
    return log_file

def setup_logging(level: int = logging.INFO, log_to_file: bool = False) -> logging.Logger:
    """
    Set up logging configuration for the entire application.
    
    Args:
        level (int): Logging level (default: logging.INFO)
        log_to_file (bool): Whether to log to a file (default: False)
    Returns:
        logging.Logger: Root logger instance
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get the root logger
    root_logger = logging.getLogger('TonieToolbox')
    root_logger.setLevel(level)
    
    # Remove any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        try:
            log_file = get_log_file_path()
            file_handler = logging.FileHandler(
                log_file,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)
            root_logger.info(f"Log file created at: {log_file}")
        except Exception as e:
            root_logger.error(f"Failed to set up file logging: {e}")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name (str): Logger name, typically the module name
    Returns:
        logging.Logger: Logger instance
    """
    # Get logger with proper hierarchical naming
    logger = logging.getLogger(f'TonieToolbox.{name}')
    return logger