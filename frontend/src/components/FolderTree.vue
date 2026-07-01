<script setup lang="ts">
import { computed, onMounted } from 'vue';
import Tree from 'primevue/tree';
import type { TreeNode } from 'primevue/treenode';
import { mediaStore } from '../stores/mediaStore';
import type { MediaNode } from '../types';

onMounted(() => {
    mediaStore.loadTree();
});

const treeValue = computed<TreeNode[]>(() => (
    mediaStore.tree ? [mediaStore.tree as unknown as TreeNode] : []
));

const onNodeSelect = (node: TreeNode) => {
    const relPath = (node as TreeNode & Partial<MediaNode>).rel_path;
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
      :value="treeValue"
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
