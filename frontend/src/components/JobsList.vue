<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue';
import { jobsListStore } from '../stores/jobsListStore';
import { cancelJob } from '../api/client';

onMounted(() => jobsListStore.connectEvents());
onUnmounted(() => jobsListStore.disconnect());

const sortedJobs = computed(() => {
  return [...jobsListStore.jobs].sort((a, b) => {
    if (a.status === 'processing' && b.status !== 'processing') return -1;
    if (a.status !== 'processing' && b.status === 'processing') return 1;
    return 0;
  });
});

function basename(path: string): string {
  const parts = path.replace(/\\/g, '/').split('/').filter(Boolean);
  return parts.pop() || path;
}

function jobLabel(job: { dir: string; first_file: string | null; current_file: string | null }): string {
  const source = job.first_file || job.current_file || job.dir;
  return basename(source);
}

async function removeJob(jobId: string) {
  try {
    await cancelJob(jobId);
  } catch { /* ignore cancel errors */ }
}
</script>

<template>
  <div
    v-if="sortedJobs.length > 0"
    class="border-top-1 surface-border"
  >
    <div class="p-2 font-bold surface-section border-bottom-1 surface-border text-900 text-sm">
      Jobs
    </div>
    <div
      class="overflow-auto"
      style="max-height: 12rem;"
    >
      <div
        v-for="job in sortedJobs"
        :key="job.job_id"
        class="flex align-items-start gap-2 px-3 py-2 border-bottom-1 surface-border"
      >
        <i
          :class="job.status === 'processing' ? 'pi pi-spin pi-spinner' : 'pi pi-clock'"
          class="text-500 flex-shrink-0 mt-1"
          style="font-size: 0.85rem;"
        />
        <div class="flex-grow-1 min-w-0">
          <div class="text-sm text-900 white-space-nowrap overflow-hidden text-overflow-ellipsis">
            {{ jobLabel(job) }}
          </div>
          <div
            v-if="job.status === 'processing'"
            class="text-xs text-500 mt-1"
          >
            {{ Math.round(job.overall_percent) }}%
            <span
              v-if="job.current_file"
              class="ml-1"
            >— {{ job.current_file }}</span>
          </div>
        </div>
        <button
          v-if="job.status === 'pending'"
          class="p-link flex-shrink-0 text-400 hover:text-600 border-none bg-transparent cursor-pointer p-0"
          style="line-height: 1;"
          title="Cancel job"
          @click="removeJob(job.job_id)"
        >
          <i
            class="pi pi-times"
            style="font-size: 0.75rem;"
          />
        </button>
      </div>
    </div>
  </div>
</template>
