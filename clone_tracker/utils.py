"""
Utility functions for file I/O, logging, and backup management.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict


def setup_logger(name: str = "clone_tracker", log_dir: str = "logs") -> logging.Logger:
    """
    Set up a rotating file logger.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    ensure_directory_exists(log_dir)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    log_file = os.path.join(log_dir, f"{name}.log")
    
    # Rotating file handler: 5MB max, 3 backups
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        directory: Directory path to create
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def create_backup(file_path: str) -> str:
    """
    Create a timestamped backup of a file.
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file
        
    Raises:
        FileNotFoundError: If source file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak.{timestamp}"
    
    shutil.copy2(file_path, backup_path)
    logger = logging.getLogger("clone_tracker")
    logger.info(f"Created backup: {backup_path}")
    
    return backup_path


def safe_write_json(data: Dict[str, Any], file_path: str, create_backup_flag: bool = True) -> None:
    """
    Safely write JSON data to file with optional backup.
    
    Args:
        data: Data to write
        file_path: Destination file path
        create_backup_flag: Whether to create backup of existing file
        
    Raises:
        IOError: If write operation fails
    """
    logger = logging.getLogger("clone_tracker")
    
    # Create backup if file exists
    if create_backup_flag and os.path.exists(file_path):
        try:
            create_backup(file_path)
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
    
    # Ensure parent directory exists
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        ensure_directory_exists(parent_dir)
    
    # Write to temporary file first for atomicity
    temp_path = f"{file_path}.tmp"
    try:
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Move temp file to final location
        shutil.move(temp_path, file_path)
        logger.debug(f"Successfully wrote JSON to {file_path}")
        
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Failed to write JSON to {file_path}: {e}")
        raise IOError(f"Failed to write JSON to {file_path}: {e}")


def load_json(file_path: str, default: Any = None) -> Any:
    """
    Load JSON data from file.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist
        
    Returns:
        Loaded data or default value
    """
    logger = logging.getLogger("clone_tracker")
    
    if not os.path.exists(file_path):
        logger.debug(f"File {file_path} does not exist, returning default")
        return default
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return default


def get_timestamp() -> str:
    """
    Get current timestamp string.
    
    Returns:
        ISO format timestamp
    """
    return datetime.now().isoformat()
