<script setup lang="ts">
import FolderTree from './FolderTree.vue';
import MediaTable from './MediaTable.vue';
import TopToolbar from './TopToolbar.vue';
import JobProgress from './JobProgress.vue';
import JobLogs from './JobLogs.vue';
import JobsList from './JobsList.vue';

</script>

<template>
  <div class="h-screen flex flex-column overflow-hidden surface-ground">
    <div class="p-3 surface-card border-bottom-1 surface-border flex align-items-center justify-content-between">
      <div class="text-xl font-bold text-900">
        Video Cleaner Web
      </div>
    </div>
    
    <div class="flex-grow-1 overflow-hidden flex">
      <div class="w-30rem border-right-1 surface-border h-full flex flex-column surface-card">
        <div class="p-2 font-bold surface-section border-bottom-1 surface-border text-900">
          Input Folders
        </div>
        <FolderTree class="flex-grow-1 min-h-0" />
        <JobsList />
      </div>
        
      <div class="flex-grow-1 flex flex-column overflow-hidden">
        <TopToolbar />
            
        <div class="flex-grow-1 flex flex-column overflow-hidden surface-ground">
          <div class="flex-1 flex flex-column overflow-hidden">
            <div class="flex-grow-1 relative overflow-auto surface-card p-2 min-h-0">
              <MediaTable />
            </div>
          </div>
          <div class="flex-1 flex flex-column overflow-hidden surface-card border-top-1 surface-border">
            <div class="p-2 border-bottom-1 surface-border font-bold text-900 surface-section">
              Processing Status
            </div>
            <JobProgress class="p-3" />
            <div class="flex-grow-1 relative overflow-hidden flex flex-column min-h-0">
              <JobLogs class="flex-grow-1 min-h-0" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
