"""
Logging configuration for the TonieToolbox package.
"""

import logging
import os
import sys

# Define log levels and their names
TRACE = 5  # Custom level for ultra-verbose debugging
logging.addLevelName(TRACE, 'TRACE')

# Create a method for the TRACE level
def trace(self, message, *args, **kwargs):
    """Log a message with TRACE level (more detailed than DEBUG)"""
    if self.isEnabledFor(TRACE):
        self.log(TRACE, message, *args, **kwargs)

# Add trace method to the Logger class
logging.Logger.trace = trace

def setup_logging(level=logging.INFO):
    """
    Set up logging configuration for the entire application.
    
    Args:
        level: Logging level (default: logging.INFO)
        
    Returns:
        logging.Logger: Root logger instance
    """
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get the root logger
    root_logger = logging.getLogger('TonieToolbox')
    root_logger.setLevel(level)
    
    return root_logger

def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name, typically the module name
        
    Returns:
        logging.Logger: Logger instance
    """
    # Get logger with proper hierarchical naming
    logger = logging.getLogger(f'TonieToolbox.{name}')
    return logger