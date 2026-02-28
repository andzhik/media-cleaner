<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { getJobsUrl } from '../api/client';

interface Job {
  job_id: string;
  status: string;
  overall_percent: number;
  dir: string | null;
  files: string[] | null;
}

const jobs = ref<Job[]>([]);
let eventSource: EventSource | null = null;
let reconnectTimer: number | null = null;

const connect = () => {
    if (eventSource) {
        eventSource.close();
    }
    eventSource = new EventSource(getJobsUrl());
    
    eventSource.onmessage = (event) => {
        // We only expect 'jobs' event from backend, but EventSource defaults to 'message' if no event name provided
        // Let's listen to the specific named event we used in backend 
    };

    eventSource.addEventListener('jobs', (event) => {
        try {
            const data = JSON.parse(event.data);
            jobs.value = data;
        } catch (e) {
            console.error("Failed to parse jobs list", e);
        }
    });

    eventSource.onerror = (err) => {
        console.error("Jobs SSE connection error", err);
        eventSource?.close();
        
        // Auto-reconnect after a delay
        if (reconnectTimer) clearTimeout(reconnectTimer);
        reconnectTimer = window.setTimeout(() => connect(), 2000);
    };
};

onMounted(() => {
    connect();
});

onUnmounted(() => {
    if (eventSource) {
        eventSource.close();
    }
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
    }
});

const getTooltipContent = (job: Job) => {
    let content = `Progress: ${job.overall_percent.toFixed(1)}%\n`;
    if (job.files && job.files.length > 0) {
        content += "Files:\n" + job.files.join('\n');
    }
    return content;
};
</script>

<template>
  <div class="h-15rem border-top-1 surface-border flex flex-column surface-card">
    <div class="p-2 font-bold surface-section border-bottom-1 surface-border text-900 flex justify-content-between align-items-center">
        <span>Active Jobs</span>
        <span class="text-sm font-normal text-500">{{ jobs.length }}</span>
    </div>
    <div class="flex-grow-1 overflow-y-auto p-2">
      <div v-if="jobs.length === 0" class="text-500 text-sm italic text-center p-3">
          No active jobs
      </div>
      <div v-else class="flex flex-column gap-2">
          <div 
            v-for="job in jobs" 
            :key="job.job_id"
            class="flex align-items-center gap-2 p-2 border-round surface-hover cursor-pointer state-box"
            v-tooltip.top="{ value: getTooltipContent(job), style: { whiteSpace: 'pre-line' } }"
          >
              <i v-if="job.status === 'processing'" class="pi pi-spin pi-spinner text-primary"></i>
              <i v-else-if="job.status === 'pending'" class="pi pi-clock text-500"></i>
              <span class="text-overflow-ellipsis white-space-nowrap overflow-hidden text-sm w-full" :title="job.dir || 'Selected Files'">
                  {{ job.dir || 'Selected Files' }}
              </span>
          </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.state-box {
    border: 1px solid var(--surface-border);
}
</style>
