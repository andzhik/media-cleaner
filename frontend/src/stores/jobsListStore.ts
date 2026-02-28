import { reactive } from 'vue';
import { getJobsListEventsUrl } from '../api/client';

export interface ActiveJob {
  job_id: string;
  dir: string;
  status: 'pending' | 'processing';
  overall_percent: number;
  current_file: string | null;
  first_file: string | null;
}

export const jobsListStore = reactive({
  jobs: [] as ActiveJob[],
  eventSource: null as EventSource | null,

  connectEvents() {
    if (this.eventSource) return;
    const url = getJobsListEventsUrl();
    this.eventSource = new EventSource(url);

    this.eventSource.addEventListener('jobs_list', (event: MessageEvent) => {
      this.jobs = JSON.parse(event.data) as ActiveJob[];
    });

    this.eventSource.onerror = () => {
      this.eventSource?.close();
      this.eventSource = null;
    };
  },

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
  },
});
