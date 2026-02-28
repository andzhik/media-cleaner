from pydantic import BaseModel
from typing import List, Optional, Set

class FileNode(BaseModel):
    name: str
    rel_path: str
    children: Optional[List['FileNode']] = None

FileNode.model_rebuild()

class StreamInfo(BaseModel):
    id: int
    language: str
    title: Optional[str] = None
    codec_type: str # 'audio' or 'subtitle'

class VideoFile(BaseModel):
    name: str
    rel_path: str
    audio_streams: List[StreamInfo] = []
    subtitle_streams: List[StreamInfo] = []

class DirectoryContent(BaseModel):
    dir: str
    files: List[VideoFile]
    languages: List[str]

class FileSelection(BaseModel):
    rel_path: str
    audio_stream_ids: List[int]
    subtitle_stream_ids: List[int]

class ProcessRequest(BaseModel):
    dir: Optional[str] = None
    files: Optional[List[str]] = None  # Deprecated in favor of selections
    output_dir: str
    # Global selected languages to KEEP (e.g. "eng", "jpa", "unknown")
    audio_languages: List[str]
    subtitle_languages: List[str]
    # Specific per-file selections
    selections: Optional[List[FileSelection]] = None

class JobStatus(BaseModel):
    job_id: str
    status: str # 'pending', 'processing', 'completed', 'failed'
    overall_percent: float
    current_file: Optional[str] = None
    dir: Optional[str] = None
    files: Optional[List[str]] = None
    logs: List[str] = []
