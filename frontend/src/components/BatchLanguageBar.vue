<script setup lang="ts">
import Checkbox from 'primevue/checkbox';
import { mediaStore } from '../stores/mediaStore';
import { computed } from 'vue';

const languages = computed(() => mediaStore.languages);

// We need a way to track "batch selected" state.
// Simplest: if ALL files have this lang selected, it's checked.
// If SOME, maybe indeterminate? PrimeVue Checkbox supports distinct binding.
// But we want it to be a toggle.

const isSelected = (lang: string, type: 'audio' | 'subtitle') => {
    // Return true if selected in all included files that have this stream
    // This might be expensive to compute every render.
    // Let's just use it as a "Select All" / "Deselect All" button.
    return false; 
    // Actually, let's keep it simple: It's an action button/checkbox.
};

const toggleBatch = (lang: string, type: 'audio' | 'subtitle', value: boolean) => {
    mediaStore.toggleLanguage(lang, type, value);
};
</script>

<template>
    <div class="flex flex-wrap gap-4 p-2 bg-gray-900 border-bottom-1 border-gray-700">
        <div class="flex align-items-center"><span class="font-bold mr-2">Batch Audio:</span>
            <div v-for="lang in languages" :key="'aud-'+lang" class="mr-3 flex align-items-center">
                <Checkbox :binary="true" @change="e => toggleBatch(lang, 'audio', e.target.checked)" />
                <span class="ml-1">{{ lang }}</span>
            </div>
        </div>
        <div class="flex align-items-center"><span class="font-bold mr-2">Batch Subs:</span>
            <div v-for="lang in languages" :key="'sub-'+lang" class="mr-3 flex align-items-center">
                <Checkbox :binary="true" @change="e => toggleBatch(lang, 'subtitle', e.target.checked)" />
                <span class="ml-1">{{ lang }}</span>
            </div>
        </div>
    </div>
</template>
