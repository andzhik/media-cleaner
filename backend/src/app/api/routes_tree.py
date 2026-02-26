from fastapi import APIRouter
from pathlib import Path
from typing import Optional
from ..core.config import settings
from ..core.models import FileNode

router = APIRouter()

def build_tree(path: Path, root: Path) -> Optional[FileNode]:
    """
    Recursively builds a tree of FileNode objects containing only directories.
    Only includes directories that contain video files or subdirectories with video files.
    """
    children = []
    try:
        # Get sub-directories and recursively build their trees
        subdirs = sorted(
            [item for item in path.iterdir() if item.is_dir() and not item.name.startswith(".")],
            key=lambda x: x.name.lower()
        )
        for subdir in subdirs:
            child_node = build_tree(subdir, root)
            if child_node:
                children.append(child_node)
    except (PermissionError, FileNotFoundError):
        pass

    # Check if this directory itself contains any video files
    has_videos = False
    try:
        has_videos = any(
            item.is_file() and item.suffix.lower() in settings.VIDEO_EXTENSIONS 
            for item in path.iterdir()
        )
    except (PermissionError, FileNotFoundError):
        pass

    # If this directory has no video files and no non-empty subdirectories, skip it
    if not has_videos and not children:
        return None

    name = "/" if path == root else path.name
    
    # Standardize path to use forward slashes and ensure it starts with /
    rel_path = "/" + str(path.relative_to(root)).replace("\\", "/")
    if rel_path == "/.":
        rel_path = "/"
        
    return FileNode(name=name, rel_path=rel_path, children=children)

@router.get("/tree", response_model=FileNode)
async def get_tree():
    """
    Returns the directory tree (folders only) for the input root.
    """
    tree = build_tree(settings.INPUT_ROOT, settings.INPUT_ROOT)
    if tree is None:
        return FileNode(name="/", rel_path="/", children=[])
    return tree

