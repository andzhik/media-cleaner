import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FolderTree from '../../components/FolderTree.vue'
import { mediaStore } from '../../stores/mediaStore'

vi.mock('../../stores/mediaStore', () => ({
    mediaStore: {
        tree: null,
        expandedKeys: {},
        loadTree: vi.fn(),
        loadDirectory: vi.fn(),
    },
}))

beforeEach(() => {
    vi.mocked(mediaStore.loadTree).mockReset()
    vi.mocked(mediaStore.loadDirectory).mockReset()
})

describe('FolderTree', () => {
    it('calls loadTree on mount', () => {
        mount(FolderTree)
        expect(mediaStore.loadTree).toHaveBeenCalledOnce()
    })

    it('calls loadDirectory with node rel_path on node-select', async () => {
        const wrapper = mount(FolderTree)
        const tree = wrapper.findComponent({ name: 'Tree' })

        await tree.vm.$emit('node-select', { rel_path: '/movies', name: 'movies' })

        expect(mediaStore.loadDirectory).toHaveBeenCalledWith('/movies')
    })
})
