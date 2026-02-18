import subprocess
import re
from pathlib import Path
from typing import List, Callable, Set

class FfmpegRunner:
    def run_ffmpeg(self, 
                   input_path: Path, 
                   output_path: Path, 
                   audio_languages: List[str], 
                   subtitle_languages: List[str], 
                   progress_callback: Callable[[float], None]):
        
        # Build command
        # Map all video streams
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-map", "0:v",
            "-c", "copy"
        ]

        # Map audio streams by language
        # We need to probe first to know which indices match? 
        # Or acts as a filter?
        # ffmpeg -map 0:m:language:eng is supported in newer ffmpeg but maybe complex to combine with 'unknown'.
        # Safest way: 
        # 1. We kept things simple in plan: "Backend translates language selections into ffmpeg mapping"
        # 2. But here I moved logic to worker.
        # 3. Worker has instructions "audio_languages".
        # 4. ffmpeg can select by metadata.
        
        # -map 0:a:m:language:eng ? 
        # If we want to keep 'unknown' (und), we need to handle that.
        
        # Let's try to use negative mapping? No.
        # Let's use inclusive mapping.
        
        # Construct maps. 
        # Problem: 'unknown' might not be tagged.
        # So we might need to probe here again or pass stream indices from backend.
        # The backend plan said: "Backend translates language selections into ffmpeg mapping". 
        # But `ProcessRequest` has `audio_languages: Set[str]`. 
        # So the backend *didn't* provide indices in the request model I implemented. 
        # It provided languages.
        
        # So, the worker needs to decide which streams to keep.
        # It's better to probe here to get exact stream indices.
        
        # Let's do a quick probe.
        stream_indices = self._probe_streams(input_path)
        
        # Filter
        kv_audio = set(audio_languages)
        kv_subs = set(subtitle_languages)
        
        at_least_one_audio = False
        
        for s in stream_indices['audio']:
            lang = s.get('tags', {}).get('language', 'unknown')
            if lang in kv_audio:
                cmd.extend(["-map", f"0:{s['index']}"])
                at_least_one_audio = True
                
        for s in stream_indices['subtitle']:
            lang = s.get('tags', {}).get('language', 'unknown')
            if lang in kv_subs:
                cmd.extend(["-map", f"0:{s['index']}"])

        # If no audio selected/found, what to do? 
        # Usually we might want to keep *something* or just proceed without audio.
        # Lets proceed.
        
        # Run
        print(f"Executing: {' '.join(cmd)}")
        
        # Popen to capture progress
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8' # Ensure decoding
        )
        
        # Parse progress
        # ffmpeg outputs to stderr usually
        duration = None
        
        # We need to read line by line. 
        # Since ffmpeg writes to stderr for progress, we read stderr.
        while True:
            line = process.stderr.readline()
            if not line:
                break
            
            # Print to logs (could be piped to status)
            # print(line.strip()) 
            
            # Parse duration: "Duration: 00:00:00.00"
            if "Duration:" in line and not duration:
                duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                if duration_match:
                    h, m, s, cs = map(int, duration_match.groups())
                    duration = h * 3600 + m * 60 + s + cs / 100.0
            
            # Parse time: "time=00:00:00.00"
            if "time=" in line and duration:
                time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                if time_match:
                    h, m, s, cs = map(int, time_match.groups())
                    current_time = h * 3600 + m * 60 + s + cs / 100.0
                    if duration > 0:
                        percent = (current_time / duration) * 100
                        progress_callback(percent)

        process.wait()
        if process.returncode != 0:
            raise Exception("ffmpeg failed")

    def _probe_streams(self, file_path: Path):
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(res.stdout)
        
        audio = []
        subs = []
        for s in data.get("streams", []):
            if s.get("codec_type") == "audio":
                audio.append(s)
            elif s.get("codec_type") == "subtitle":
                subs.append(s)
        return {"audio": audio, "subtitle": subs}
