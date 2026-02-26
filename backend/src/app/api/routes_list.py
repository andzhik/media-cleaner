from fastapi import APIRouter, Query, HTTPException
from ..core.security_paths import get_input_path, settings
from ..core.models import DirectoryContent, VideoFile
from ..core.ffprobe import probe_file
import asyncio

router = APIRouter()

@router.get("/list", response_model=DirectoryContent)
async def list_directory(dir: str = Query(..., description="Relative path to directory")):
    try:
        dir_path = get_input_path(dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    files = []
    languages = set()
    
    # List files
    items = sorted(dir_path.iterdir(), key=lambda x: x.name)
    
    # Gather tasks for probing
    probe_tasks = []
    video_files_map = {} # path -> VideoFile
    
    for item in items:
        if item.is_file() and item.suffix.lower() in settings.VIDEO_EXTENSIONS:
            rel_path = "/" + str(item.relative_to(settings.INPUT_ROOT)).replace("\\", "/")
            vf = VideoFile(name=item.name, rel_path=rel_path)
            files.append(vf)
            video_files_map[str(item)] = vf
            probe_tasks.append(probe_file(item))
            
    # Probe in parallel
    if probe_tasks:
        results = await asyncio.gather(*probe_tasks)
        
        # Assign results back
        for vf, res in zip(files, results):
            vf.audio_streams = res["audio"]
            vf.subtitle_streams = res["subtitle"]
            
            for s in vf.audio_streams:
                languages.add(s.language)
            for s in vf.subtitle_streams:
                languages.add(s.language)

    return DirectoryContent(
        dir=dir,
        files=files,
        languages=languages
    )
