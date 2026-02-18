<script setup lang="ts">
import { ref, computed } from 'vue';
import Checkbox from 'primevue/checkbox';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import { mediaStore } from '../stores/mediaStore';
import { jobStore } from '../stores/jobStore';

const outputDir = ref('processed');

const languages = computed(() => mediaStore.languages);

const toggleBatch = (lang: string, type: 'audio' | 'subtitle', value: boolean) => {
    mediaStore.toggleLanguage(lang, type, value);
};

const onProcess = async () => {
    if (!mediaStore.currentDir) return;
    
    const allSelectedAudio = new Set<string>();
    const allSelectedSubs = new Set<string>();
    const filesToProcess = [];

    for (const f of mediaStore.files) {
        if (f.includeFile) {
            filesToProcess.push(f.rel_path);
            f.selectedAudio.forEach((l: string) => allSelectedAudio.add(l));
            f.selectedSubs.forEach((l: string) => allSelectedSubs.add(l));
        }
    }

    const payload = {
        dir: mediaStore.currentDir,
        files: filesToProcess,
        output_dir: outputDir.value,
        audio_languages: Array.from(allSelectedAudio),
        subtitle_languages: Array.from(allSelectedSubs)
    };
    
    await jobStore.startJob(payload);
};
</script>

<template>
    <div class="p-3 surface-section border-bottom-1 surface-border flex flex-wrap gap-4 align-items-center justify-content-between">
        <!-- Left: Batch Checkboxes -->
        <div class="flex gap-4">
            <div class="flex align-items-center">
                <span class="font-bold mr-2 text-700">Batch Audio:</span>
                <div v-for="lang in languages" :key="'aud-'+lang" class="mr-3 flex align-items-center">
                    <Checkbox :binary="true" @change="e => toggleBatch(lang, 'audio', e.target.checked)" />
                    <span class="ml-1 text-700">{{ lang }}</span>
                </div>
            </div>
            <div class="flex align-items-center">
                <span class="font-bold mr-2 text-700">Batch Subs:</span>
                <div v-for="lang in languages" :key="'sub-'+lang" class="mr-3 flex align-items-center">
                    <Checkbox :binary="true" @change="e => toggleBatch(lang, 'subtitle', e.target.checked)" />
                    <span class="ml-1 text-700">{{ lang }}</span>
                </div>
            </div>
        </div>

        <!-- Center/Right: Output Controls -->
        <div class="flex gap-2 align-items-center">
            <span class="p-input-icon-left">
                <i class="pi pi-folder" />
                <InputText v-model="outputDir" placeholder="Output Folder" class="w-15rem" />
            </span>
            <Button label="Process" icon="pi pi-cog" @click="onProcess" :loading="!!jobStore.activeJobId" :disabled="!mediaStore.currentDir" />
        </div>
    </div>
</template>
