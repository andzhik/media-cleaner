from pathlib import Path

def validate_path(rel_path: str, root_path: Path) -> Path:
    clean_rel = rel_path.lstrip("/")
    if not clean_rel:
        return root_path
    full_path = (root_path / clean_rel).resolve()
    if not str(full_path).startswith(str(root_path)):
        raise Exception("Path traversal attempt detected")
    return full_path

root = Path("C:/data/input").resolve()
print(f"Root: {root}")

path1 = "/tv/fallout"
resolved1 = validate_path(path1, root)
print(f"Path: {path1} -> Resolved: {resolved1}")

path2 = "tv/fallout"
resolved2 = validate_path(path2, root)
print(f"Path: {path2} -> Resolved: {resolved2}")

path3 = "movies/action/diehard.mkv"
resolved3 = validate_path(path3, root)
print(f"Path: {path3} -> Resolved: {resolved3}")
