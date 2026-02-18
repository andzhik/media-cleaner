<script setup lang="ts">
import FolderTree from './components/FolderTree.vue';
import MediaTable from './components/MediaTable.vue';
import TopToolbar from './components/TopToolbar.vue';
import JobProgress from './components/JobProgress.vue';
import JobLogs from './components/JobLogs.vue';
import Splitter from 'primevue/splitter';
import SplitterPanel from 'primevue/splitterpanel';
</script>

<template>
  <div class="h-screen flex flex-column overflow-hidden surface-ground">
    <div class="p-3 surface-card border-bottom-1 surface-border flex align-items-center justify-content-between">
        <div class="text-xl font-bold text-900">Video Cleaner Web</div>
    </div>
    
    <div class="flex-grow-1 overflow-hidden flex">
        <div class="w-20rem border-right-1 surface-border h-full overflow-hidden flex flex-column surface-card">
            <div class="p-2 font-bold surface-section border-bottom-1 surface-border text-900">
                Input Folders
            </div>
            <FolderTree class="flex-grow-1" />
        </div>
        
        <div class="flex-grow-1 flex flex-column overflow-hidden">
            <TopToolbar />
            
            <Splitter layout="vertical" class="flex-grow-1 border-none surface-ground" stateKey="main-vertical-splitter" stateStorage="local">
                <SplitterPanel :size="60" :minSize="30" class="flex flex-column overflow-hidden">
                     <div class="flex-grow-1 relative overflow-auto surface-card p-2">
                         <MediaTable />
                     </div>
                </SplitterPanel>
                <SplitterPanel :size="40" :minSize="20" class="flex flex-column overflow-hidden surface-card border-top-1 surface-border">
                    <div class="p-2 border-bottom-1 surface-border font-bold text-900 surface-section">Processing Status</div>
                    <JobProgress class="p-3" />
                    <div class="flex-grow-1 relative overflow-hidden flex flex-column">
                        <JobLogs />
                    </div>
                </SplitterPanel>
            </Splitter>
        </div>
    </div>
  </div>
</template>

<style>
body { 
    margin: 0; 
    padding: 0; 
    font-family: var(--font-family); 
    background-color: var(--surface-ground);
    color: var(--text-color);
}
</style>
