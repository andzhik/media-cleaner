<script setup lang="ts">
import { jobStore } from '../stores/jobStore';
import { ref, watch, nextTick } from 'vue';

const logContainer = ref<HTMLElement | null>(null);

watch(() => jobStore.logs.length, () => {
    nextTick(() => {
        if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight;
        }
    });
});
</script>

<template>
  <div
    ref="logContainer"
    class="surface-ground text-color font-mono text-sm p-2 h-full w-full overflow-y-auto border-none"
  >
    <div
      v-for="(log, i) in jobStore.logs"
      :key="i"
      class="white-space-pre-wrap"
    >
      {{ log }}
    </div>
  </div>
</template>
