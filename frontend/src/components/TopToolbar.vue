<script setup lang="ts">
import { ref, computed } from 'vue';
import Checkbox from 'primevue/checkbox';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import { mediaStore } from '../stores/mediaStore';
import { jobStore } from '../stores/jobStore';

const outputDir = ref('processed');

const languages = computed(() => mediaStore.languages);

const toggleBatch = (lang: string, value: boolean) => {
    mediaStore.toggleLanguage(lang, 'both', value);
    if (value) {
        if (!mediaStore.selectedLanguages.includes(lang)) mediaStore.selectedLanguages.push(lang);
    } else {
        mediaStore.selectedLanguages = mediaStore.selectedLanguages.filter(l => l !== lang);
    }
};

const onProcess = async () => {
    if (!mediaStore.currentDir) return;
    
    const selections = mediaStore.files
        .filter(f => f.includeFile)
        .map(f => ({
            rel_path: f.rel_path,
            audio_stream_ids: f.selectedAudio,
            subtitle_stream_ids: f.selectedSubs
        }));

    const payload = {
        dir: mediaStore.currentDir,
        output_dir: outputDir.value,
        audio_languages: mediaStore.selectedLanguages,
        subtitle_languages: mediaStore.selectedLanguages,
        selections: selections
    };
    
    await jobStore.startJob(payload);
};
</script>

<template>
    <div class="p-3 surface-section border-bottom-1 surface-border flex flex-wrap gap-4 align-items-center justify-content-between">
        <!-- Left: Unified Batch Checkboxes -->
        <div class="flex gap-4">
            <div class="flex align-items-center">
                <span class="font-bold mr-2 text-700 text-sm">Languages:</span>
                <div v-for="lang in languages" :key="'batch-'+lang" class="mr-3 flex align-items-center">
                    <Checkbox :modelValue="mediaStore.selectedLanguages.includes(lang)" :binary="true" @update:modelValue="v => toggleBatch(lang, v)" />
                    <span class="ml-1 text-700 uppercase">{{ lang === 'unknown' ? 'UNK' : lang }}</span>
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
