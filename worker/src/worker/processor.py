import json
import os
import shutil
from pathlib import Path
from .ffmpeg_runner import FfmpegRunner
import time

JOB_DATA_ROOT = Path(os.getenv("JOB_DATA_ROOT", "/job-data"))
INPUT_ROOT = Path(os.getenv("INPUT_ROOT", "/media/input"))
OUTPUT_ROOT = Path(os.getenv("OUTPUT_ROOT", "/media/output"))

class JobProcessor:
    def __init__(self):
        self.pending_dir = JOB_DATA_ROOT / "pending"
        self.processing_dir = JOB_DATA_ROOT / "processing"
        self.completed_dir = JOB_DATA_ROOT / "completed"
        self.failed_dir = JOB_DATA_ROOT / "failed"
        
        for d in [self.pending_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def process_jobs(self):
        # Polling loop
        while True:
            # Check for pending jobs
            files = sorted(list(self.pending_dir.glob("*.json")))
            if not files:
                time.sleep(2)
                continue
                
            job_file = files[0]
            self.process_job(job_file)

    def process_job(self, job_file: Path):
        print(f"Picking up job {job_file.name}")
        
        # Move to processing
        processing_file = self.processing_dir / job_file.name
        shutil.move(job_file, processing_file)
        
        job_data = {}
        try:
            with open(processing_file, "r") as f:
                job_data = json.load(f)
            
            job_id = job_data["job_id"]
            self.update_status(job_id, "processing", 0.0)

            # Resolve paths:
            # Input paths in job_data are relative to INPUT_ROOT
            # Output dir is relative to OUTPUT_ROOT
            
            input_root = INPUT_ROOT
            output_root = OUTPUT_ROOT
            
            files = job_data.get("files", [])
            dir_rel = job_data.get("dir")
            output_dir_rel = job_data.get("output_dir", "")
            
            if dir_rel:
                # If dir provided, scanning it again? Or we trust 'files' list?
                # The prompt says: "Selected directory or explicit file list"
                # If only dir, we might need to scan. But let's assume UI sends explicit files list 
                # or we implement scanning here.
                # Simplest: UI should send file list?
                # Plan says: "Selected directory OR explicit file list"
                pass
            
            # If files list is empty but dir is present, scan dir?
            if not files and dir_rel:
                source_dir = input_root / dir_rel.lstrip("/")
                if source_dir.is_dir():
                    files = [
                        "/" + str(p.relative_to(input_root)).replace("\\", "/") 
                        for p in source_dir.glob("*") 
                        if p.suffix.lower() in {".mkv", ".mp4", ".avi", ".mov"}
                    ]
            
            output_dir = output_root / output_dir_rel.lstrip("/")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use 'selections' if available, otherwise use 'files' (fallback)
            selections = job_data.get("selections")
            
            all_logs: list = []

            if selections:
                total_files = len(selections)
                for idx, sel in enumerate(selections):
                    file_rel = sel["rel_path"]
                    self.update_status(job_id, "processing", (idx / total_files) * 100, current_file=file_rel)
                    
                    input_path = input_root / file_rel.lstrip("/")
                    output_path = output_dir / Path(file_rel).name
                    
                    if not input_path.exists():
                        print(f"Input not found: {input_path}")
                        continue

                    runner = FfmpegRunner()
                    log = runner.run_ffmpeg(
                        input_path, 
                        output_path, 
                        job_data["audio_languages"], 
                        job_data["subtitle_languages"],
                        lambda p: self.update_status(job_id, "processing", ((idx + p/100) / total_files) * 100, current_file=file_rel, logs=all_logs),
                        audio_stream_ids=sel.get("audio_stream_ids"),
                        subtitle_stream_ids=sel.get("subtitle_stream_ids"),
                        log_callback=lambda line: all_logs.append(line)
                    )
            else:
                total_files = len(files)
                for idx, file_rel in enumerate(files):
                    self.update_status(job_id, "processing", (idx / total_files) * 100, current_file=file_rel)
                    
                    input_path = input_root / file_rel.lstrip("/")
                    output_path = output_dir / Path(file_rel).name
                    
                    # Check if input exists
                    if not input_path.exists():
                         print(f"Input not found: {input_path}")
                         continue

                    runner = FfmpegRunner()
                    log = runner.run_ffmpeg(
                        input_path, 
                        output_path, 
                        job_data["audio_languages"], 
                        job_data["subtitle_languages"],
                        lambda p: self.update_status(job_id, "processing", ((idx + p/100) / total_files) * 100, current_file=file_rel, logs=all_logs),
                        log_callback=lambda line: all_logs.append(line)
                    )

            self.update_status(job_id, "completed", 100.0, logs=all_logs)
            shutil.move(processing_file, self.completed_dir / job_file.name)
            
        except Exception as e:
            print(f"Job failed: {e}")
            self.update_status(job_data.get("job_id", "unknown"), "failed", 0.0, logs=[str(e)])
            shutil.move(processing_file, self.failed_dir / job_file.name)

    def update_status(self, job_id, status, percent, current_file=None, logs=None):
        # Update status file which API reads?
        # Actually API needs to know status. 
        # If API serves job status from memory, worker needs to push it back.
        # Impl Plan: "Backend provides overall progress... Worker... writes output."
        # If they use shared volume, maybe Worker writes status.json?
        # But 'store.py' in API was in-memory.
        
        # Okay, I will change API 'store.py' to read from file if in-memory missing/stale?
        # OR better: API polls status file?
        # Since I'm using "Simplest" - let's make the worker write a status file 
        # that the API can read.
        pass
        
        # I'll implement a 'status' directory in JOB_DATA_ROOT
        status_file = JOB_DATA_ROOT / "status" / f"{job_id}.json"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "job_id": job_id,
            "status": status,
            "overall_percent": percent,
            "current_file": current_file,
            "logs": logs or []
        }
        
        # Simple atomic write
        tmp_file = status_file.with_suffix(".tmp")
        with open(tmp_file, "w") as f:
            json.dump(data, f)
        
        # Retry replacing the file to handle Windows file locking issues
        # (e.g. if the API is currently reading the file)
        for _ in range(10):
            try:
                os.replace(tmp_file, status_file)
                break
            except OSError:
                import time
                time.sleep(0.05)

if __name__ == "__main__":
    processor = JobProcessor()
    processor.process_jobs()
