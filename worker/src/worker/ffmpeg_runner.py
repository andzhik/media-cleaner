import subprocess
import re
import json
from pathlib import Path
from typing import List, Callable

PROGRESS_RE = re.compile(
    r"frame=\s*(\d+)\s+fps=\s*([\d.]+)\s+q=\s*([-\d.]+)\s+"
    r"size=\s*([\d.]+)(KiB|kB|MiB|MB|GiB|GB)\s+"
    r"time=(\d{2}:\d{2}:\d{2})\.\d+\s+"
    r"bitrate=\s*([\S]+)\s+speed=\s*([\d.]+)x"
)

_SIZE_MULTIPLIERS = {
    "KiB": 1024,
    "kB": 1024,
    "MiB": 1048576,
    "MB": 1048576,
    "GiB": 1073741824,
    "GB": 1073741824,
}

class FfmpegRunner:
    def run_ffmpeg(self,
                   input_path: Path,
                   output_path: Path,
                   audio_languages: List[str],
                   subtitle_languages: List[str],
                   progress_callback: Callable[[dict], None],
                   audio_stream_ids: List[int] = None,
                   subtitle_stream_ids: List[int] = None,
                   log_callback: Callable[[str], None] = None,
                   cmd_callback: Callable[[str], None] = None):

        # Probe for video totals
        probe = self._probe_streams(input_path)
        total_frames = probe["video"].get("total_frames")
        total_duration = probe["video"].get("total_duration")
        total_size_bytes = input_path.stat().st_size if input_path.exists() else None

        # Build command
        # Map all video streams
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-map", "0:v",
            "-c", "copy"
        ]

        self._map_streams(
            input_path=input_path,
            cmd=cmd,
            audio_languages=audio_languages,
            subtitle_languages=subtitle_languages,
            audio_stream_ids=audio_stream_ids,
            subtitle_stream_ids=subtitle_stream_ids
        )

        # If no audio selected/found, what to do?
        # Usually we might want to keep *something* or just proceed without audio.
        # Add output path
        cmd.append(str(output_path))

        # Run
        cmd_str = ' '.join(cmd)
        print(f"\nExecuting: {cmd_str}")

        if cmd_callback:
            cmd_callback(cmd_str)

        log: List[str] = []

        def emit(line: str):
            """Append to local log and fire the optional live callback."""
            log.append(line)
            if log_callback:
                log_callback(line)

        emit(f"$ {cmd_str}")

        # Merge stdout+stderr into a single pipe so everything is captured in order
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8'
        )

        duration = None

        while True:
            line = process.stdout.readline()
            if not line:
                break

            stripped = line.rstrip("\n")

            # Emit progress lines live
            if "frame=" in line:
                print(stripped)
                emit(stripped)

            # Parse duration: "Duration: 00:00:00.00"
            if "Duration:" in line and not duration:
                duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                if duration_match:
                    h, m, s, cs = map(int, duration_match.groups())
                    duration = h * 3600 + m * 60 + s + cs / 100.0
                    # Fall back total_duration from ffmpeg output if probe missed it
                    if not total_duration and duration > 0:
                        td_h = int(duration // 3600)
                        td_m = int((duration % 3600) // 60)
                        td_s = int(duration % 60)
                        total_duration = f"{td_h:02d}:{td_m:02d}:{td_s:02d}"

            # Parse time: "time=00:00:00.00"
            if "time=" in line and duration:
                time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                if time_match:
                    h, m, s, cs = map(int, time_match.groups())
                    current_time = h * 3600 + m * 60 + s + cs / 100.0
                    if duration > 0:
                        percent = (current_time / duration) * 100

                        # Try to extract full progress dict via PROGRESS_RE
                        m_prog = PROGRESS_RE.search(line)
                        if m_prog:
                            frame, fps, q, size_val, size_unit, time_str, bitrate, speed = m_prog.groups()
                            size_bytes = int(float(size_val) * _SIZE_MULTIPLIERS.get(size_unit, 1024))
                            progress_callback({
                                "percent": percent,
                                "frame": int(frame),
                                "fps": float(fps),
                                "q": float(q),
                                "size_bytes": size_bytes,
                                "total_size_bytes": total_size_bytes,
                                "time": time_str,
                                "total_frames": total_frames,
                                "total_time": total_duration,
                                "bitrate": bitrate,
                                "speed": float(speed),
                            })
                        else:
                            progress_callback({"percent": percent})

        process.wait()
        if process.returncode != 0:
            raise Exception("ffmpeg failed\n" + "\n".join(log))

        emit(f"Done: {input_path} -> {output_path}")
        emit("---")

        return log

    def _probe_streams(self, file_path: Path):
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(res.stdout) if res.stdout.strip() else {}

        audio = []
        subs = []
        video_info = {}
        for s in data.get("streams", []):
            if s.get("codec_type") == "audio":
                audio.append(s)
            elif s.get("codec_type") == "subtitle":
                subs.append(s)
            elif s.get("codec_type") == "video" and not video_info:
                nb = s.get("nb_frames", "")
                fps_str = s.get("r_frame_rate") or s.get("avg_frame_rate", "")
                dur = float(s.get("duration", 0) or 0)

                total_frames = None
                if nb and nb != "N/A":
                    try:
                        total_frames = int(nb)
                    except ValueError:
                        pass
                elif dur > 0 and fps_str and "/" in fps_str:
                    num, den = fps_str.split("/")
                    fps = int(num) / int(den) if int(den) else 0
                    total_frames = int(dur * fps) if fps else None

                total_dur_str = None
                if dur > 0:
                    total_h = int(dur // 3600)
                    total_m = int((dur % 3600) // 60)
                    total_s = int(dur % 60)
                    total_dur_str = f"{total_h:02d}:{total_m:02d}:{total_s:02d}"

                video_info = {"total_frames": total_frames, "total_duration": total_dur_str}

        return {"audio": audio, "subtitle": subs, "video": video_info}

    def _map_streams(self,
                     input_path: Path,
                     cmd: List[str],
                     audio_languages: List[str],
                     subtitle_languages: List[str],
                     audio_stream_ids: List[int] = None,
                     subtitle_stream_ids: List[int] = None):
        # Use specific indices if provided
        if audio_stream_ids is not None or subtitle_stream_ids is not None:
            if audio_stream_ids:
                for idx in audio_stream_ids:
                    cmd.extend(["-map", f"0:{idx}"])
                cmd.extend(['-disposition:a:0', 'default'])
            if subtitle_stream_ids:
                for idx in subtitle_stream_ids:
                    cmd.extend(["-map", f"0:{idx}"])
                cmd.extend(['-disposition:s:0', 'default'])
        else:
            # Fallback to language-based mapping
            stream_indices = self._probe_streams(input_path)

            kv_audio = set(audio_languages)
            kv_subs = set(subtitle_languages)

            for s in stream_indices['audio']:
                lang = s.get('tags', {}).get('language', 'unknown')
                if lang in kv_audio:
                    cmd.extend(["-map", f"0:{s['index']}"])

            for s in stream_indices['subtitle']:
                lang = s.get('tags', {}).get('language', 'unknown')
                if lang in kv_subs:
                    cmd.extend(["-map", f"0:{s['index']}"])
