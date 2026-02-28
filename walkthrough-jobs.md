# Jobs Panel Walkthrough

The Jobs Panel feature has been fully implemented! Here's a breakdown of the changes that were made:

## Backend API & Models
1. **Added Metadata to Jobs**: Upgraded the [JobStatus](backend/src/app/core/models.py#43-51) Pydantic model and `job_queue.enqueue` method to capture the initial `dir` (directory) and `files` (file payload) attributes. This ensures the frontend has information about the source folder and files.
2. **Worker Status Payload**: Updated [JobProcessor](worker/src/worker/processor.py#12-191) inside the worker to save `dir` and `files` when moving jobs from `pending` to `processing`, passing those to the shared `/job-data/status` files.
3. **SSE Endpoint**: Added a new endpoint at `GET /api/jobs` within [routes_jobs.py](backend/src/app/api/routes_jobs.py) that streams the status of all `pending` and `processing` jobs. The endpoint polls the job store every second.

## Frontend UI
1. **JobsPanel Component**: Created a new [JobsPanel.vue](frontend/src/components/JobsPanel.vue) component that connects to the `/api/jobs` endpoint using Server-Sent Events (`EventSource`).
2. **Data Binding**: It parses the incoming JSON data and dynamically renders active jobs.
3. **UI Elements**: 
   - A list of jobs is shown with the respective folder name.
   - A `pi-spin pi-spinner` icon is used for processing jobs.
   - A `pi-clock` icon is used for pending jobs.
   - A tooltip built via PrimeVue (`v-tooltip`) appears on hover, providing a multiline summary containing the overall percentage and the list of files to process.
4. **Resiliency**: The SSE component handles reconnects automatically on disconnection, attempting to reconnect every 2 seconds.
5. **Layout Integration**: Added `<JobsPanel />` directly below the `<FolderTree />` inside [MainLayout.vue](frontend/src/components/MainLayout.vue) as requested. 

## Testing / Verification
Since this relies heavily on real-time rendering and interaction:
1. Please start both the backend/worker and the frontend using your standard `run_all.bat`.
2. Open the UI, select some files to process, and click the **Process** button.
3. Verify that the **Jobs Panel** correctly appears below the Input Folders section and displays the current working folder.
4. Verify that hovering over the entries provides the complete list of files and the current overall progress duration!
