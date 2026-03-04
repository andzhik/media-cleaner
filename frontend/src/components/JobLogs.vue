<script setup lang="ts">
import { jobStore } from '../stores/jobStore';
import { ref, watch, nextTick, computed } from 'vue';

const logContainer = ref<HTMLElement | null>(null);

function basename(path: string): string {
    return path.split('/').pop() ?? path;
}

function fmtBytes(n: number): string {
    return (n / 1048576).toFixed(1) + 'MiB';
}

function buildMetricsParts(info: any): string[] {
    const parts: string[] = [];
    if (info.frame != null) {
        const frameStr = info.total_frames != null
            ? `${info.frame}/${info.total_frames}`
            : String(info.frame);
        parts.push(`frame=${frameStr}`);
    }
    if (info.fps != null) parts.push(`fps=${info.fps}`);
    if (info.q != null) parts.push(`q=${info.q}`);
    if (info.size_bytes != null) {
        const sizeStr = info.total_size_bytes != null
            ? `${fmtBytes(info.size_bytes)}/${fmtBytes(info.total_size_bytes)}`
            : fmtBytes(info.size_bytes);
        parts.push(`size=${sizeStr}`);
    }
    if (info.time != null) {
        const timeStr = info.total_time != null
            ? `${info.time}/${info.total_time}`
            : info.time;
        parts.push(`time=${timeStr}`);
    }
    if (info.bitrate != null) parts.push(`bitrate=${info.bitrate}`);
    if (info.speed != null) parts.push(`speed=${info.speed}x`);
    return parts;
}

// Cache the last non-empty metrics string per file path
const lastMetrics = ref<Record<string, string>>({});

watch(() => jobStore.fileProgress, (fp) => {
    for (const [rel, info] of Object.entries(fp) as [string, any][]) {
        const parts = buildMetricsParts(info);
        if (parts.length) {
            lastMetrics.value[rel] = parts.join(' ');
        }
    }
}, { deep: true });

// Build ordered list of file rows from fileProgress
const fileRows = computed(() => {
    return Object.entries(jobStore.fileProgress).map(([rel, info]: [string, any]) => {
        const name = basename(rel);
        const status = info.status ?? 'queued';

        if (status === 'queued') {
            return { name, line: `${name}: [queued]`, status };
        }

        if (status === 'failed') {
            return { name, line: `${name}: [failed]`, status };
        }

        // processing or done — build metrics line
        const parts = buildMetricsParts(info);
        const metrics = parts.length
            ? parts.join(' ')
            : (status === 'done' ? (lastMetrics.value[rel] ?? '') : '…');
        return {
            name,
            line: `${name}: ${metrics}`,
            status,
            cmd: (info.cmd as string) ?? null,
            doneLine: (info.done_line as string) ?? null,
        };
    });
});

watch(fileRows, () => {
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
    <template v-for="row in fileRows" :key="row.name">
      <div v-if="row.cmd" class="white-space-pre-wrap">$ {{ row.cmd }}</div>
      <div
        class="white-space-pre-wrap font-bold"
      >
        {{ row.line }}
      </div>
      <div v-if="row.doneLine" class="white-space-pre-wrap">{{ row.doneLine }}</div>
    </template>
  </div>
</template>
