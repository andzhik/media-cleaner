from pathlib import Path
from fastapi import HTTPException
from .config import settings

def validate_path(rel_path: str, root_path: Path) -> Path:
    """
    Validates that joining root_path with rel_path stays within root_path.
    Returns the absolute resolved path.
    """
    # Remove leading slash to ensure join works as relative
    clean_rel = rel_path.lstrip("/")
    if not clean_rel:
        return root_path

    # Resolve the full path
    full_path = (root_path / clean_rel).resolve()

    # Check that the resolved path starts with the root path
    if not str(full_path).startswith(str(root_path)):
        # Provide more specific error for debugging if needed, but safe to just say 403/400
        raise HTTPException(status_code=403, detail="Path traversal attempt detected")
    
    return full_path

def get_input_path(rel_path: str) -> Path:
    return validate_path(rel_path, settings.INPUT_ROOT)

def get_output_path(rel_path: str) -> Path:
    return validate_path(rel_path, settings.OUTPUT_ROOT)
