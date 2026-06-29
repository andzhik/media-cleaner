# Backend and Worker CLI Test Guide

Use this guide to test the backend and worker together from PowerShell, either with local Python processes or with Docker Compose. The frontend is not required for this test.

## Scenario

Fixture file:

```powershell
C:\Users\Andrei\Documents\Projects\video-cleaner-web\test-files\<video>.mkv
```

The test removes the Russian audio stream and keeps the English audio and English subtitle streams.

Expected output files:

```powershell
# Local-process test output
C:\Users\Andrei\Documents\Projects\video-cleaner-web\test-files\output\<video>.mkv

# Docker Compose test output
C:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\output\<video>.mkv
```

## Confirm Stream IDs

```powershell
$repo = 'C:\Users\Andrei\Documents\Projects\video-cleaner-web'
$video = '<video>.mkv'
$fixture = Join-Path $repo "test-files\$video"

ffprobe -v quiet -print_format json -show_streams $fixture
```

For the current fixture, the relevant streams are:

```text
0 video h264
1 audio rus AC-3 title=TVShows
2 audio eng E-AC-3 title=Original
3 subtitle eng SubRip title=English
```

## Option A: Local Backend and Worker

### 1. Prepare Roots

From the repo root:

```powershell
$repo = 'C:\Users\Andrei\Documents\Projects\video-cleaner-web'
$inputRoot = Join-Path $repo 'test-files'
$outputRoot = Join-Path $repo 'test-files\output'
$jobRoot = Join-Path $repo 'test-files\job-data-cli-test'

New-Item -ItemType Directory -Force -Path $outputRoot, $jobRoot | Out-Null
```

### 2. Start Backend

Open a PowerShell window:

```powershell
Set-Location "$repo\backend"
$env:INPUT_ROOT = $inputRoot
$env:OUTPUT_ROOT = $outputRoot
$env:JOB_DATA_ROOT = $jobRoot
python -m uvicorn --app-dir src app.main:app --host 127.0.0.1 --port 8000
```

### 3. Start Worker

Open another PowerShell window:

```powershell
Set-Location "$repo\worker"
$env:INPUT_ROOT = $inputRoot
$env:OUTPUT_ROOT = $outputRoot
$env:JOB_DATA_ROOT = $jobRoot
python -m worker.main
```

### 4. Run the API Test

Use the shared API test commands below with base URL `http://127.0.0.1:8000`.

## Option B: Docker Compose Backend and Worker

Docker Compose uses the repo's `mnt` roots:

```text
mnt/input    -> /media/input
mnt/output   -> /media/output
mnt/job-data -> /job-data
```

### 1. Prepare Docker Roots

From the repo root:

```powershell
$repo = 'C:\Users\Andrei\Documents\Projects\video-cleaner-web'
Set-Location $repo

New-Item -ItemType Directory -Force -Path '.\mnt\input', '.\mnt\output', '.\mnt\job-data' | Out-Null
$video = '<video>.mkv'
Copy-Item -LiteralPath ".\test-files\$video" -Destination ".\mnt\input\$video" -Force
```

If you want a fresh output for this test:

```powershell
Remove-Item -LiteralPath ".\mnt\output\$video" -Force -ErrorAction SilentlyContinue
```

### 2. Start Docker Services

```powershell
docker compose up --build -d api worker
```

Check the services:

```powershell
docker compose ps
```

The API should be published on `http://127.0.0.1:8000`. The frontend service is not needed for this CLI test.

### 3. Run the API Test

Use the shared API test commands below with base URL `http://127.0.0.1:8000`.

To inspect worker execution:

```powershell
docker compose logs worker --tail 80
```

To stop the Docker services after testing:

```powershell
docker compose down
```

## Shared API Test Commands

### 1. Verify Backend Probing

```powershell
$baseUrl = 'http://127.0.0.1:8000'

$file = Invoke-RestMethod -Uri "$baseUrl/api/list?dir=/" -Method Get |
  Select-Object -ExpandProperty files |
  Where-Object { $_.name -eq $video }

$file | ConvertTo-Json -Depth 6
```

Confirm the backend reports audio stream `1` as `rus`, audio stream `2` as `eng`, and subtitle stream `3` as `eng`.

### 2. Submit Processing Job

```powershell
$body = @{
  dir = '/'
  output_dir = '/'
  audio_languages = @('eng')
  subtitle_languages = @('eng')
  selections = @(
    @{
      rel_path = "/$video"
      audio_stream_ids = @(2)
      subtitle_stream_ids = @(3)
    }
  )
} | ConvertTo-Json -Depth 6

$response = Invoke-RestMethod `
  -Uri "$baseUrl/api/process" `
  -Method Post `
  -ContentType 'application/json' `
  -Body $body

$jobId = $response.jobId
$jobId
```

### 3. Poll Job Status

```powershell
for ($i = 0; $i -lt 180; $i++) {
  $status = Invoke-RestMethod -Uri "$baseUrl/api/jobs/$jobId" -Method Get
  "{0:u} status={1} percent={2:N1} current={3}" -f (Get-Date), $status.status, [double]$status.overall_percent, $status.current_file
  if ($status.status -in @('completed', 'failed')) { break }
  Start-Sleep -Seconds 2
}

$status | ConvertTo-Json -Depth 8
```

The status should become `completed` with `overall_percent` at `100`.

### 4. Verify Output Streams

For the local-process test:

```powershell
ffprobe -v quiet -print_format json -show_streams "$outputRoot\$video"
```

For the Docker Compose test:

```powershell
ffprobe -v quiet -print_format json -show_streams "$repo\mnt\output\$video"
```

Expected output streams:

```text
0 video h264
1 audio eng E-AC-3 title=Original
2 subtitle eng SubRip title=English
```

There should be no `rus` audio stream in the output file.

## Last Known Results

### Local Backend and Worker

This guide was run successfully on 2026-06-28 local time, with worker log timestamps on 2026-06-29 UTC. The job ID was `9515b964-29e8-4def-be85-2d47d2f211aa`.

The worker ran:

```text
ffmpeg -y -i test-files\<video>.mkv -map 0:v -c copy -map 0:2 -disposition:a:0 default -map 0:3 -disposition:s:0 default test-files\output\<video>.mkv
```

The generated output was `1,528,905,208` bytes and contained only the English audio and English subtitle streams.

### Docker Compose Backend and Worker

This guide was run successfully on 2026-06-28 local time using `docker compose up --build -d api worker`. The job ID was `004283eb-9053-4be6-9442-9d0a09149ff3`.

The worker ran:

```text
ffmpeg -y -i /media/input/<video>.mkv -map 0:v -c copy -map 0:2 -disposition:a:0 default -map 0:3 -disposition:s:0 default /media/output/<video>.mkv
```

The generated output was `1,528,905,208` bytes and contained only the English audio and English subtitle streams. The job files were written under `mnt/job-data` through the Docker bind mount.
