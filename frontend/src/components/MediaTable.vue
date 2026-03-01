<script setup lang="ts">
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Checkbox from 'primevue/checkbox';
import { mediaStore } from '../stores/mediaStore';

const formatLang = (lang: string) => lang === 'unknown' ? 'UNK' : lang.toUpperCase();
</script>

<template>
  <div class="h-full overflow-auto">
    <div
      v-if="mediaStore.loading"
      class="p-4"
    >
      Loading...
    </div>
    <div
      v-else-if="mediaStore.error"
      class="p-4 text-red-500"
    >
      {{ mediaStore.error }}
    </div>
        
    <DataTable
      v-else
      :value="mediaStore.files"
      scrollable
      scroll-height="flex"
      table-style="min-width: 50rem"
    >
      <Column
        field="name"
        header="File"
      >
        <template #body="slotProps">
          <div class="flex align-items-center gap-2">
            <Checkbox
              v-model="slotProps.data.includeFile"
              :binary="true"
            />
            <span>{{ slotProps.data.name }}</span>
          </div>
        </template>
      </Column>
            
      <Column header="Audio">
        <template #body="slotProps">
          <div class="flex flex-wrap gap-3">
            <div
              v-for="stream in slotProps.data.audio_streams"
              :key="stream.id"
              class="flex align-items-center gap-1"
            >
              <Checkbox
                v-model="slotProps.data.selectedAudio"
                :value="stream.id"
              />
              <span>{{ formatLang(stream.language) }}</span>
              <span
                v-if="stream.title"
                class="text-xs text-color-secondary"
              >({{ stream.title }})</span>
            </div>
          </div>
        </template>
      </Column>

      <Column header="Subtitles">
        <template #body="slotProps">
          <div class="flex flex-wrap gap-3">
            <div
              v-for="stream in slotProps.data.subtitle_streams"
              :key="stream.id"
              class="flex align-items-center gap-1"
            >
              <Checkbox
                v-model="slotProps.data.selectedSubs"
                :value="stream.id"
              />
              <span>{{ formatLang(stream.language) }}</span>
              <span
                v-if="stream.title"
                class="text-xs text-color-secondary"
              >({{ stream.title }})</span>
            </div>
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>
