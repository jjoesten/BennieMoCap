import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Union

def remove_empty_directories(root_dir: Union[str, Path]):
    """Recursively removes empty directories from the specified root directory"""
    for path in Path(root_dir).rglob("*"):
        if path.is_dir() and not any(path.iterdir()):
            logger.info(f"Removing: {path}")
            path.rmdir()
        elif path.is_dir() and any(path.iterdir()):
            remove_empty_directories(path)  # recursion
        else:
            continue