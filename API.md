# Video Cleaner Backend API Specification

This document describes the REST API for the Video Cleaner backend service.

## Tools
- Install REST Client extension for VS Code/Antigravity/etc to run test requests directly from this file.

## Base URL
All API endpoints are prefixed with `/api`.
The server runs on `http://localhost:8000` by default.

## Endpoints

### 1. File System Navigation

#### Get Directory Tree
Returns a hierarchical tree of directories starting from the configured input root.

- **URL**: `/api/tree`
- **Method**: `GET`
- **Example**:
```http
http://localhost:8000/api/tree
```
- **Response**: `FileNode` (hierarchical)
```json
{
  "name": "ROOT",
  "rel_path": "/",
  "children": [
    {
      "name": "Movies",
      "rel_path": "/Movies",
      "children": [...]
    }
  ]
}
```

#### List Directory Contents
Lists video files in a specific directory. It also probes each video file to extract audio and subtitle stream information.

- **URL**: `/api/list`
- **Method**: `GET`
- **Query Parameters**:
  - `dir`: Relative path to the directory (e.g., `/Movies`)
- **Example**:
```http
http://localhost:8000/api/list?dir=/tv/Fallout
```
- **Response**: `DirectoryContent`
```json
{
  "dir": "/Movies",
  "files": [
    {
      "name": "movie.mkv",
      "rel_path": "/Movies/movie.mkv",
      "audio_streams": [
        {
          "id": 1,
          "language": "eng",
          "title": "Stereo",
          "codec_type": "audio"
        }
      ],
      "subtitle_streams": []
    }
  ],
  "languages": ["eng", "jpa"]
}
```

### 2. Processing

#### Start Processing Job
Queues a new processing job to clean video files based on selected languages.

- **URL**: `/api/process`
- **Method**: `POST`
- **Request Body**: `ProcessRequest`

```json
{
  "dir": "/Movies",
  "output_dir": "/Output",
  "audio_languages": ["eng", "jpa"],
  "subtitle_languages": ["eng"],
  "selections": [
    {
      "rel_path": "/Movies/movie.mkv",
      "audio_stream_ids": [1, 2],
      "subtitle_stream_ids": [5]
    }
  ]
}
```

- **Response**:
```json
{
  "jobId": "uuid-string"
}
```

### 3. Job Management

#### Get Job Status
Retrieves the current status of a specific job.

- **URL**: `/api/jobs/{job_id}`
- **Method**: `GET`
- **Response**: `JobStatus`
- **Example**: `curl "http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000"`

```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "overall_percent": 45.5,
  "current_file": "movie.mkv",
  "logs": ["Started processing movie.mkv..."]
}
```

#### Job Events Stream (SSE)
Subscribe to real-time updates for a specific job using Server-Sent Events.

- **URL**: `/api/jobs/{job_id}/events`
- **Method**: `GET`
- **Response**: **text/event-stream**
  - Event: `status`
  - Data: JSON string of `JobStatus`

## Data Models

### FileNode
- `name`: string
- `rel_path`: string
- `children`: List[FileNode] (optional)

### VideoFile
- `name`: string
- `rel_path`: string
- `audio_streams`: List[StreamInfo]
- `subtitle_streams`: List[StreamInfo]

### StreamInfo
- `id`: integer
- `language`: string
- `title`: string (optional)
- `codec_type`: string ('audio' or 'subtitle')

### ProcessRequest
- `dir`: string (optional, source directory)
- `files`: List[string] (optional, specific files to process, deprecated)
- `output_dir`: string (destination)
- `audio_languages`: List[string] (global languages to keep)
- `subtitle_languages`: List[string] (global languages to keep)
- `selections`: List[FileSelection] (optional, granular per-file stream selection)

### FileSelection
- `rel_path`: string
- `audio_stream_ids`: List[integer]
- `subtitle_stream_ids`: List[integer]

### JobStatus
- `job_id`: string
- `status`: string ('pending', 'processing', 'completed', 'failed')
- `overall_percent`: float
- `current_file`: string (optional)
- `logs`: List[string]
