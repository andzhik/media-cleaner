<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import Checkbox from 'primevue/checkbox';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import RadioButton from 'primevue/radiobutton';
import { mediaStore } from '../stores/mediaStore';
import { jobStore } from '../stores/jobStore';

const envMediaTypes = (import.meta.env.VITE_MEDIA_TYPES as string) || 'tv show,movies';
const availableMediaTypes = envMediaTypes.split(',').map(s => s.trim());

const outputDir = ref('');
const mediaType = ref(availableMediaTypes[0] || 'tv');

watch(() => mediaStore.currentDir, (currentDir) => {
    if (currentDir) {
        outputDir.value = '/' + mediaType.value + currentDir;
    }
}, { immediate: true });

const onMediaTypeChange = () => {
    if (!outputDir.value) {
        outputDir.value = '/' + mediaType.value;
        return;
    }
    const sep = outputDir.value.includes('\\') ? '\\' : '/';
    let segments = outputDir.value.split(sep);
    const index = segments[0] === '' ? 1 : 0;
    segments[index] = mediaType.value;
    outputDir.value = segments.join(sep);
};


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
        <div
          v-for="lang in languages"
          :key="'batch-'+lang"
          class="mr-3 flex align-items-center"
        >
          <Checkbox
            :model-value="mediaStore.selectedLanguages.includes(lang)"
            :binary="true"
            @update:model-value="v => toggleBatch(lang, v)"
          />
          <span class="ml-1 text-700 uppercase">{{ lang === 'unknown' ? 'UNK' : lang }}</span>
        </div>
      </div>
    </div>

    <!-- Center/Right: Output Controls -->
    <div class="flex gap-2 align-items-center">
      <div class="flex gap-3 align-items-center mr-3">
        <div
          v-for="type in availableMediaTypes"
          :key="type"
          class="flex align-items-center"
        >
          <RadioButton
            v-model="mediaType"
            :input-id="'type-' + type"
            name="mediaType"
            :value="type"
            @change="onMediaTypeChange"
          />
          <label
            :for="'type-' + type"
            class="ml-2 capitalize"
          >{{ type === 'tv' ? 'TV' : type }}</label>
        </div>
      </div>
      <span class="p-input-icon-left">
        <i class="pi pi-folder" />
        <InputText
          v-model="outputDir"
          placeholder="Output Folder"
          class="w-30rem"
        />
      </span>
      <Button
        label="Process"
        icon="pi pi-cog"
        :loading="!!jobStore.activeJobId && !['completed', 'failed'].includes(jobStore.status || '')"
        :disabled="!mediaStore.currentDir"
        @click="onProcess"
      />
    </div>
  </div>
</template>
