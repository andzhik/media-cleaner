<script setup lang="ts">
import ProgressBar from 'primevue/progressbar';
import { jobStore } from '../stores/jobStore';
</script>

<template>
  <div
    v-if="jobStore.activeJobId"
    class="p-2 border-top-1 surface-border"
  >
    <div class="flex justify-content-between mb-1 text-sm">
      <span>Overall Progress: {{ jobStore.progress.toFixed(1) }}%</span>
      <span class="text-color-secondary text-xs">
        {{ jobStore.status === 'completed' ? 'Done' : (jobStore.status === 'failed' ? 'Failed' : (jobStore.currentFile || 'Initializing...')) }}
      </span>
    </div>
    <ProgressBar
      :value="jobStore.progress"
      style="height: 6px"
      :show-value="false"
    />
  </div>
</template>
