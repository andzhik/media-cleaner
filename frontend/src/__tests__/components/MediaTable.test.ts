import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import MediaTable from '../../components/MediaTable.vue'
import { mediaStore } from '../../stores/mediaStore'

vi.mock('../../stores/mediaStore', () => ({
    mediaStore: {
        loading: false,
        error: null as string | null,
        files: [] as any[],
    },
}))

// Proper stub so .props('value') is available
const DataTableStub = defineComponent({
    name: 'DataTable',
    props: ['value', 'scrollable', 'scrollHeight'],
    template: '<div><slot /></div>',
})

const localStubs = { DataTable: DataTableStub, Column: true, Checkbox: true }

function mountTable() {
    return mount(MediaTable, { global: { stubs: localStubs } })
}

beforeEach(() => {
    Object.assign(mediaStore, { loading: false, error: null, files: [] })
})

describe('MediaTable', () => {
    it('shows loading indicator when loading', () => {
        mediaStore.loading = true

        const wrapper = mountTable()

        expect(wrapper.text()).toContain('Loading...')
        expect(wrapper.findComponent(DataTableStub).exists()).toBe(false)
    })

    it('shows error message when error is set', () => {
        mediaStore.error = 'Failed to load files'

        const wrapper = mountTable()

        expect(wrapper.text()).toContain('Failed to load files')
        expect(wrapper.findComponent(DataTableStub).exists()).toBe(false)
    })

    it('renders DataTable when not loading and no error', () => {
        const wrapper = mountTable()

        expect(wrapper.findComponent(DataTableStub).exists()).toBe(true)
        expect(wrapper.text()).not.toContain('Loading...')
    })

    it('passes files to DataTable', () => {
        mediaStore.files = [
            { name: 'ep1.mkv', audio_streams: [], subtitle_streams: [], includeFile: true, selectedAudio: [], selectedSubs: [] },
        ]

        const wrapper = mountTable()
        const table = wrapper.findComponent(DataTableStub)

        expect(table.props('value')).toHaveLength(1)
        expect((table.props('value') as any[])[0].name).toBe('ep1.mkv')
    })
})
