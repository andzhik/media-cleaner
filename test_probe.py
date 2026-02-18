
import asyncio
import os
from pathlib import Path
import sys

# Add backend/src to path
sys.path.append(os.path.abspath("backend/src"))

from app.core.ffprobe import probe_file
from app.core.config import settings

async def main():
    # Try to find where the files actually are
    possible_paths = [
        Path("mnt/input/tv/Fallout/Fallout.S02E01.1080p.WEB-DLRip.H265.mkv"),
        Path(r"c:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\input\tv\Fallout\Fallout.S02E01.1080p.WEB-DLRip.H265.mkv"),
        Path(r"C:\media\input\tv\Fallout\Fallout.S02E01.1080p.WEB-DLRip.H265.mkv")
    ]
    
    for p in possible_paths:
        abs_p = p.resolve()
        print(f"Trying path: {abs_p}")
        if abs_p.exists():
            print(f"Path exists! Probing...")
            res = await probe_file(abs_p)
            print(f"Result: {res}")
        else:
            print(f"Path does not exist.")

if __name__ == "__main__":
    asyncio.run(main())
