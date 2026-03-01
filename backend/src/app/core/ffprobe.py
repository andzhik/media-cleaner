import json
import subprocess
import asyncio
from pathlib import Path
from typing import List, Dict
from .models import StreamInfo

async def probe_file(file_path: Path) -> Dict[str, List[StreamInfo]]:
    """
    Runs ffprobe on the file and returns a dict with 'audio' and 'subtitle' lists of StreamInfo.
    """
    log_file = Path("ffprobe_debug.log")
    
    cmd = [
        "ffprobe",
        "-print_format", "json",
        "-show_streams",
        str(file_path)
    ]

    try:
        # Run ffprobe in a thread to avoid event loop issues on Windows
        def run_ffprobe():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

        result = await asyncio.to_thread(run_ffprobe)

        if result.returncode != 0:
            error_msg = f"ffprobe failed for {file_path} with code {result.returncode}\nStderr: {result.stderr}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(error_msg)
            return {"audio": [], "subtitle": []}

        data = json.loads(result.stdout)

        streams = data.get("streams", [])

        audio_streams = []
        subtitle_streams = []

        for stream in streams:
            codec_type = stream.get("codec_type")
            if codec_type not in ["audio", "subtitle"]:
                continue

            tags = stream.get("tags", {})
            
            # Extract info
            # ffprobe index is 'index'
            index = stream.get("index")
            language = tags.get("language", "unknown")
            title = tags.get("title")

            if index is None:
                continue

            info = StreamInfo(
                id=index,
                language=language,
                title=title,
                codec_type=codec_type
            )

            if codec_type == "audio":
                audio_streams.append(info)
            else:
                subtitle_streams.append(info)

        return {"audio": audio_streams, "subtitle": subtitle_streams}

    except Exception as e:
        error_msg = f"Error probing {file_path}: {type(e).__name__}: {str(e)}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(error_msg)
        return {"audio": [], "subtitle": []}

