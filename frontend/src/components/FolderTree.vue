<script setup lang="ts">
import { onMounted } from 'vue';
import Tree from 'primevue/tree';
import type { TreeNode } from 'primevue/treenode';
import { mediaStore } from '../stores/mediaStore';

onMounted(() => {
    mediaStore.loadTree();
});

const onNodeSelect = (node: TreeNode) => {
    // node from PrimeVue's tree component
    // we use any here carefully if needed or just cast property
    const relPath = (node as any).rel_path;
    if (typeof relPath === 'string') {
        mediaStore.loadDirectory(relPath);
    }
};

const onNodeExpand = () => {
    // If we were lazy loading, we'd fetch here.
    // But our backend returns full tree for now.
};
</script>

<template>
  <div class="h-full overflow-auto">
    <Tree 
      v-model:expanded-keys="mediaStore.expandedKeys" 
      :value="mediaStore.tree ? [mediaStore.tree] : []"
      selection-mode="single"
      class="w-full"
      @node-select="onNodeSelect"
      @node-expand="onNodeExpand"
    >
      <template #default="slotProps">
        <span>{{ slotProps.node.name }}</span>
      </template>
    </Tree>
  </div>
</template>
