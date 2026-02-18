from fastapi import APIRouter
from pathlib import Path
from ..core.config import settings
from ..core.models import FileNode

router = APIRouter()

def build_tree(path: Path, root: Path) -> FileNode:
    """
    Recursively builds a tree of FileNode objects containing only directories.
    """
    name = "ROOT" if path == root else path.name
    
    # Standardize path to use forward slashes and ensure it starts with /
    rel_path = "/" + str(path.relative_to(root)).replace("\\", "/")
    if rel_path == "/.":
        rel_path = "/"
        
    node = FileNode(name=name, rel_path=rel_path, is_dir=True)
    
    children = []
    try:
        # Sort directories alphabetically by name
        items = sorted(
            [item for item in path.iterdir() if item.is_dir() and not item.name.startswith(".")], 
            key=lambda x: x.name.lower()
        )
        for item in items:
            children.append(build_tree(item, root))
    except PermissionError:
        pass
    node.children = children
        
    return node

@router.get("/tree", response_model=FileNode)
async def get_tree():
    """
    Returns the directory tree (folders only) for the input root.
    """
    return build_tree(settings.INPUT_ROOT, settings.INPUT_ROOT)

