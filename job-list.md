# Task: Implement Jobs Panel (Pending + In-Progress)

Add a UI panel below the **Directory Tree** that displays all **pending** and **currently processing** jobs.

Constraints:
- Only one job can be in progress at a time.
- Completed and failed jobs are not shown (they disappear from the list).
- Jobs already persist server-side.

## Frontend Requirements

### Panel Placement

- Render the panel directly below the Directory Tree component.
- The panel is always visible (not collapsible).

### Job List Behavior

- Display a vertical list of jobs received from the backend.
- No manual sorting required.
- The currently processing job appears in the list as provided by the backend.

### Job Item Display

Each job entry must show:

- **Status icon**
  - Processing → progress indicator icon
  - Pending → waiting/pending icon
- **Directory name**

### Tooltip (on Hover)

On mouse hover over a job:

Show a tooltip containing:

- Overall progress percentage (numeric value only)
- List of files included in the job

Notes:
- Progress is calculated from:  
  `ffmpeg_processed_time / total_duration`
- Progress number is displayed only inside the tooltip (not inline).

## Real-Time Updates

### Communication Method

- Use **Server-Sent Events (SSE)**.
- Subscribe immediately on component mount.
- Do NOT fetch initial state via REST.

### SSE Behavior

- Backend sends the **full list of jobs** on every update.
- Frontend replaces the entire local job list with the received data.
- If SSE disconnects:
  - Automatically attempt reconnection.

Constraints:
- No authentication required.
- No Last-Event-ID handling required.

## Backend Requirements

### SSE Endpoint

Provide an SSE endpoint that:

- Streams the full list of jobs
- Includes only:
  - `pending`
  - `processing`
- Excludes:
  - completed
  - failed
