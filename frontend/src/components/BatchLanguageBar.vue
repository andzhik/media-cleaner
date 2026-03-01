<script setup lang="ts">
import Checkbox from 'primevue/checkbox';
import { mediaStore } from '../stores/mediaStore';
import { computed } from 'vue';

const languages = computed(() => mediaStore.languages);

const toggleBatch = (lang: string, type: 'audio' | 'subtitle', value: boolean) => {
    mediaStore.toggleLanguage(lang, type, value);
};
</script>

<template>
  <div class="flex flex-wrap gap-4 p-2 bg-gray-900 border-bottom-1 border-gray-700">
    <div class="flex align-items-center">
      <span class="font-bold mr-2">Batch Audio:</span>
      <div
        v-for="lang in languages"
        :key="'aud-'+lang"
        class="mr-3 flex align-items-center"
      >
        <Checkbox
          :binary="true"
          @change="e => toggleBatch(lang, 'audio', (e.target as HTMLInputElement).checked)"
        />
        <span class="ml-1">{{ lang }}</span>
      </div>
    </div>
    <div class="flex align-items-center">
      <span class="font-bold mr-2">Batch Subs:</span>
      <div
        v-for="lang in languages"
        :key="'sub-'+lang"
        class="mr-3 flex align-items-center"
      >
        <Checkbox
          :binary="true"
          @change="e => toggleBatch(lang, 'subtitle', (e.target as HTMLInputElement).checked)"
        />
        <span class="ml-1">{{ lang }}</span>
      </div>
    </div>
  </div>
</template>
