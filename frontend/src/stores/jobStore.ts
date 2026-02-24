import { reactive } from 'vue';
import { startProcess, getJobEventsUrl } from '../api/client';

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
            this.logs = [];
            this.status = 'starting';
            this.progress = 0;
            this.currentFile = null;
            const res = await startProcess(payload);
            this.activeJobId = res.jobId;
            this.connectEvents(res.jobId);
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
            if (data.logs && data.logs.length) {
                this.logs = data.logs;
            }

            if (data.status === 'completed' || data.status === 'failed') {
                this.eventSource?.close();
                this.eventSource = null;
            }
        });

        this.eventSource.onerror = (e) => {
            console.error("SSE Error", e);
            this.eventSource?.close();
        };
    }
});
