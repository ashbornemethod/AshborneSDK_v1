"""
File signature generation for the canonical SDK repository.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from .similarity import compute_sha256
from .utils import safe_write_json


def is_binary_file(file_path: str, sample_size: int = 8192) -> bool:
    """
    Check if a file is binary by sampling its content.
    
    Args:
        file_path: Path to file
        sample_size: Number of bytes to sample
        
    Returns:
        True if file appears to be binary
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)
            
        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            return True
        
        # Check if content is mostly text
        text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
        non_text = sum(1 for byte in chunk if byte not in text_chars)
        
        return non_text / len(chunk) > 0.3 if chunk else False
        
    except Exception:
        return True


def generate_signatures(
    root_dir: str = "sdk",
    output_file: str = "data/signatures.json",
    skip_binary: bool = True
) -> Dict[str, Dict]:
    """
    Walk directory tree and generate file signatures.
    
    Args:
        root_dir: Root directory to scan
        output_file: Output JSON file path
        skip_binary: Whether to skip binary files
        
    Returns:
        Dictionary mapping file paths to signature metadata
        
    Raises:
        FileNotFoundError: If root_dir doesn't exist
    """
    logger = logging.getLogger("clone_tracker.signatures")
    
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"Directory not found: {root_dir}")
    
    logger.info(f"Generating signatures for directory: {root_dir}")
    
    signatures = {}
    file_count = 0
    skipped_count = 0
    
    # Walk directory tree
    for root, dirs, files in os.walk(root_dir):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for filename in files:
            # Skip hidden files
            if filename.startswith('.'):
                continue
            
            file_path = os.path.join(root, filename)
            
            # Check if binary
            if skip_binary and is_binary_file(file_path):
                logger.debug(f"Skipping binary file: {file_path}")
                skipped_count += 1
                continue
            
            try:
                # Read file content
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Compute hash
                sha256 = compute_sha256(content)
                
                # Get file stats
                stat = os.stat(file_path)
                
                # Normalize path (relative to root_dir)
                rel_path = os.path.relpath(file_path, root_dir)
                
                signatures[rel_path] = {
                    'sha256': sha256,
                    'size': stat.st_size,
                    'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                file_count += 1
                logger.debug(f"Generated signature for: {rel_path}")
                
            except Exception as e:
                logger.warning(f"Failed to generate signature for {file_path}: {e}")
                continue
    
    logger.info(
        f"Generated {file_count} signatures, skipped {skipped_count} files"
    )
    
    # Add metadata
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'root_directory': root_dir,
        'file_count': file_count,
        'signatures': signatures
    }
    
    # Write to file
    safe_write_json(output_data, output_file, create_backup_flag=True)
    logger.info(f"Signatures written to: {output_file}")
    
    return signatures


def load_signatures(file_path: str = "data/signatures.json") -> Dict[str, Dict]:
    """
    Load signatures from JSON file.
    
    Args:
        file_path: Path to signatures file
        
    Returns:
        Dictionary of signatures
        
    Raises:
        FileNotFoundError: If signatures file doesn't exist
    """
    logger = logging.getLogger("clone_tracker.signatures")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Signatures file not found: {file_path}")
    
    import json
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    signatures = data.get('signatures', {})
    logger.info(f"Loaded {len(signatures)} signatures from {file_path}")
    
    return signatures
