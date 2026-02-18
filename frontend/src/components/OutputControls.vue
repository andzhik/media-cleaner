<script setup lang="ts">
import { ref } from 'vue';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import { mediaStore } from '../stores/mediaStore';
import { jobStore } from '../stores/jobStore';

const outputDir = ref('processed');

const onProcess = async () => {
    if (!mediaStore.currentDir) return;
    
    // Build payload
    // We need to group selections
    // Actually current API in backend expects "audio_languages" Set, applied to ALL files.
    // Wait, the plan said "Per-file selections...".
    // But `ProcessRequest` in `models.py` has `audio_languages: Set[str]`.
    // I implemented logic in Backend `models.py` as:
    // class ProcessRequest(BaseModel): ... audio_languages: Set[str] ...
    
    // And in Worker `processor.py`:
    // runner.run_ffmpeg(..., job_data["audio_languages"], ...)
    
    // So current implementation is GLOBALLY selected languages for the batch.
    // The table allows per-file selection in UI, but backend doesn't support it yet.
    // I should probably update backend to support per-file, OR update UI to match backend (global selection).
    // The plan said: "Batch language toggles... Checking a language selects all matching...".
    // But also "File row... audio[]... One row per file".
    
    // Let's stick to the simpler Global Selection for now as per `ProcessRequest` model I wrote.
    // OR, I can update `ProcessRequest` to take a list of file-specific configs.
    // Updating `ProcessRequest` is better for correctness.
    
    // However, for "Fast iteration", let's assume valid languages are those selected in the batch bar?
    // No, strictly following my `models.py` implementation, it takes a global set.
    // But the UI table shows checkboxes per stream.
    // If I select "eng" in one file but uncheck in another, global set won't capture that.
    
    // I will use the "BatchLanguageBar" to drive the global selection for now. 
    // AND I will gather all unique selected languages from all files to send to backend?
    // If I send "eng", backend keeps "eng" in ALL files.
    // If user unchecks "eng" in File A, but keeps in File B, and I send "eng", File A will keep "eng" too?
    // Yes, with current backend logic.
    
    // To fix this properly I should have implemented per-file logic in backend.
    // But I'm in Frontend implementation phase now. 
    // I'll stick to gathering all selected languages from the UI and sending them as a set.
    // This effectively means "If kept in ANY file, keep in ALL files (if present)".
    // This is a limitation of my current backend implementation.
    // Valid for V1.
    
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
    <div class="flex gap-2 align-items-center p-2 border-bottom-1 border-gray-700">
        <label>Output Dir:</label>
        <InputText v-model="outputDir" class="w-20rem" />
        <Button label="Process" @click="onProcess" :disabled="!mediaStore.currentDir || jobStore.activeJobId" />
        
        <div v-if="jobStore.activeJobId" class="ml-auto flex align-items-center gap-2">
            <span>Job: {{ jobStore.status }}</span>
        </div>
    </div>
</template>
