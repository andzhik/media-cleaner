<script setup lang="ts">
import { onMounted } from 'vue';
import Tree from 'primevue/tree';
import { mediaStore } from '../stores/mediaStore';

onMounted(() => {
    mediaStore.loadTree();
});

const onNodeSelect = (node: any) => {
    if (node.is_dir) {
        mediaStore.loadDirectory(node.rel_path);
    }
};

const onNodeExpand = (node: any) => {
    // If we were lazy loading, we'd fetch here.
    // But our backend returns full tree for now.
};
</script>

<template>
    <div class="h-full overflow-auto">
        <Tree 
            :value="mediaStore.tree ? [mediaStore.tree] : []" 
            v-model:expandedKeys="mediaStore.expandedKeys"
            selectionMode="single"
            @node-select="onNodeSelect"
            @node-expand="onNodeExpand"
            class="w-full"
        >
            <template #default="slotProps">
                <span>{{ slotProps.node.name }}</span>
            </template>
        </Tree>
    </div>
</template>
