"""
File operations tools for the AutoGen agent.
These tools allow reading and writing files.
"""
import os
from pathlib import Path
from typing import Annotated


def read_file(
    filepath: Annotated[str, "The path to the file to read"]
) -> Annotated[str, "The contents of the file"]:
    """
    Read the contents of a file.
    
    Args:
        filepath: Path to the file to read
        
    Returns:
        The contents of the file as a string
    """
    try:
        path = Path(filepath).expanduser().resolve()
        
        if not path.exists():
            return f"Error: File '{filepath}' does not exist"
        
        if not path.is_file():
            return f"Error: '{filepath}' is not a file"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"Successfully read {len(content)} characters from '{filepath}':\n\n{content}"
    
    except PermissionError:
        return f"Error: Permission denied when reading '{filepath}'"
    except Exception as e:
        return f"Error reading file '{filepath}': {str(e)}"


def write_file(
    filepath: Annotated[str, "The path to the file to write"],
    content: Annotated[str, "The content to write to the file"]
) -> Annotated[str, "Confirmation message"]:
    """
    Write content to a file. Creates the file if it doesn't exist, overwrites if it does.
    
    Args:
        filepath: Path to the file to write
        content: Content to write to the file
        
    Returns:
        A confirmation message
    """
    try:
        path = Path(filepath).expanduser().resolve()
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} characters to '{filepath}'"
    
    except PermissionError:
        return f"Error: Permission denied when writing to '{filepath}'"
    except Exception as e:
        return f"Error writing file '{filepath}': {str(e)}"


def append_to_file(
    filepath: Annotated[str, "The path to the file to append to"],
    content: Annotated[str, "The content to append to the file"]
) -> Annotated[str, "Confirmation message"]:
    """
    Append content to an existing file. Creates the file if it doesn't exist.
    
    Args:
        filepath: Path to the file to append to
        content: Content to append to the file
        
    Returns:
        A confirmation message
    """
    try:
        path = Path(filepath).expanduser().resolve()
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully appended {len(content)} characters to '{filepath}'"
    
    except PermissionError:
        return f"Error: Permission denied when appending to '{filepath}'"
    except Exception as e:
        return f"Error appending to file '{filepath}': {str(e)}"


def list_directory(
    dirpath: Annotated[str, "The path to the directory to list"] = "."
) -> Annotated[str, "List of files and directories"]:
    """
    List the contents of a directory.
    
    Args:
        dirpath: Path to the directory to list (default: current directory)
        
    Returns:
        A formatted list of files and directories
    """
    try:
        path = Path(dirpath).expanduser().resolve()
        
        if not path.exists():
            return f"Error: Directory '{dirpath}' does not exist"
        
        if not path.is_dir():
            return f"Error: '{dirpath}' is not a directory"
        
        items = []
        for item in sorted(path.iterdir()):
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{item_type}] {item.name}")
        
        if not items:
            return f"Directory '{dirpath}' is empty"
        
        return f"Contents of '{dirpath}':\n" + "\n".join(items)
    
    except PermissionError:
        return f"Error: Permission denied when listing '{dirpath}'"
    except Exception as e:
        return f"Error listing directory '{dirpath}': {str(e)}"