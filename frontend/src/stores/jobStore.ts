import { reactive } from 'vue';
import { startProcess, getJobEventsUrl } from '../api/client';
import { jobsListStore } from './jobsListStore';

export const jobStore = reactive({
    activeJobId: null as string | null,
    status: null as string | null,
    progress: 0,
    currentFile: null as string | null,
    logs: [] as string[],
    error: null as string | null,
    eventSource: null as EventSource | null,

    async startJob(payload: any) {
        try {
            this.error = null;
            const res = await startProcess(payload);
            // Only switch view if not currently watching a running job
            if (!this.activeJobId || this.status === 'completed' || this.status === 'failed' || !this.status) {
                this.logs = [];
                this.status = 'starting';
                this.progress = 0;
                this.currentFile = null;
                this.activeJobId = res.jobId;
                this.connectEvents(res.jobId);
            }
        } catch (e: any) {
            this.error = e.message;
        }
    },

    connectEvents(jobId: string) {
        if (this.eventSource) this.eventSource.close();

        const url = getJobEventsUrl(jobId);
        this.eventSource = new EventSource(url);

        this.eventSource.addEventListener('status', (event: MessageEvent) => {
            const data = JSON.parse(event.data);
            this.status = data.status;
            this.progress = data.overall_percent;
            this.currentFile = data.current_file;

            if (data.status === 'completed' || data.status === 'failed') {
                this.eventSource?.close();
                this.eventSource = null;
                // Auto-switch to next running job if one exists
                const next = jobsListStore.jobs.find(j => j.job_id !== jobId);
                if (next) {
                    this.logs = [];
                    this.status = next.status;
                    this.progress = next.overall_percent;
                    this.currentFile = next.current_file;
                    this.activeJobId = next.job_id;
                    this.connectEvents(next.job_id);
                }
            }
        });

        this.eventSource.addEventListener('log', (event: MessageEvent) => {
            const lines: string[] = JSON.parse(event.data);
            this.logs.push(...lines);
        });

        this.eventSource.onerror = (e) => {
            console.error("SSE Error", e);
            this.eventSource?.close();
        };
    }
});
