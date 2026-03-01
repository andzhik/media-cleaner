import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import MediaTable from '../../components/MediaTable.vue'
import { mediaStore } from '../../stores/mediaStore'

vi.mock('../../stores/mediaStore', () => ({
    mediaStore: {
        loading: false,
        error: null as string | null,
        files: [] as any[],
    },
}))

// ── Simple stub for state/existence tests ──────────────────────────────────
const DataTableStub = defineComponent({
    name: 'DataTable',
    props: ['value', 'scrollable', 'scrollHeight', 'tableStyle'],
    template: '<div><slot /></div>',
})

const localStubs = { DataTable: DataTableStub, Column: true, Checkbox: true }

function mountTable() {
    return mount(MediaTable, { global: { stubs: localStubs } })
}

// ── Smart stub for column-slot content tests ───────────────────────────────
// Iterates rows and invokes each Column's #body slot so we can test
// formatLang, stream checkboxes, stream titles, etc.
const SmartDataTableStub = defineComponent({
    name: 'DataTable',
    props: ['value', 'scrollable', 'scrollHeight', 'tableStyle'],
    setup(props, { slots }) {
        return () => {
            const rows: any[] = props.value ?? []
            const colVnodes = slots.default?.() ?? []
            return h(
                'table',
                rows.map((row: any, ri: number) =>
                    h(
                        'tr',
                        { key: ri },
                        colVnodes.map((col: any, ci: number) => {
                            const bodyFn = col.children?.body
                            return h('td', { key: ci }, bodyFn ? bodyFn({ data: row }) : [])
                        })
                    )
                )
            )
        }
    },
})

const smartStubs = { DataTable: SmartDataTableStub, Column: true, Checkbox: true }

function mountSmartTable() {
    return mount(MediaTable, { global: { stubs: smartStubs } })
}

// ── Fixtures ───────────────────────────────────────────────────────────────
function makeFile(overrides: Partial<any> = {}) {
    return {
        name: 'movie.mkv',
        rel_path: 'movie.mkv',
        includeFile: true,
        selectedAudio: [1],
        selectedSubs: [10],
        audio_streams: [{ id: 1, language: 'en', title: null }],
        subtitle_streams: [{ id: 10, language: 'unknown', title: 'English SDH' }],
        ...overrides,
    }
}

beforeEach(() => {
    Object.assign(mediaStore, { loading: false, error: null, files: [] })
})

// ── State / existence tests ────────────────────────────────────────────────
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
        mediaStore.files = [makeFile()]

        const wrapper = mountTable()

        expect(wrapper.findComponent(DataTableStub).props('value')).toHaveLength(1)
    })

    it('passes all files when there are multiple', () => {
        mediaStore.files = [makeFile({ name: 'a.mkv' }), makeFile({ name: 'b.mkv' }), makeFile({ name: 'c.mkv' })]

        const wrapper = mountTable()

        expect(wrapper.findComponent(DataTableStub).props('value')).toHaveLength(3)
    })

    it('sets scrollable on DataTable', () => {
        const wrapper = mountTable()
        // `scrollable` without a colon binding passes "" (present but no value)
        expect(wrapper.findComponent(DataTableStub).props('scrollable')).not.toBeUndefined()
    })
})

// ── Column slot content tests ──────────────────────────────────────────────
describe('MediaTable - column content', () => {
    it('renders the file name in the File column', () => {
        mediaStore.files = [makeFile({ name: 'episode.mkv' })]
        const wrapper = mountSmartTable()
        expect(wrapper.text()).toContain('episode.mkv')
    })

    it('formats "unknown" language as "UNK"', () => {
        mediaStore.files = [makeFile({
            audio_streams: [{ id: 1, language: 'unknown', title: null }],
            subtitle_streams: [],
        })]
        const wrapper = mountSmartTable()
        expect(wrapper.text()).toContain('UNK')
    })

    it('formats known language codes as uppercase', () => {
        mediaStore.files = [makeFile({
            audio_streams: [{ id: 1, language: 'en', title: null }],
            subtitle_streams: [{ id: 10, language: 'fr', title: null }],
        })]
        const wrapper = mountSmartTable()
        expect(wrapper.text()).toContain('EN')
        expect(wrapper.text()).toContain('FR')
    })

    it('renders one audio checkbox per audio stream', () => {
        mediaStore.files = [makeFile({
            audio_streams: [
                { id: 1, language: 'en', title: null },
                { id: 2, language: 'fr', title: null },
            ],
            subtitle_streams: [],
        })]
        const wrapper = mountSmartTable()
        // Each audio stream should produce a checkbox-stub in the audio column
        const audioTd = wrapper.findAll('td')[1]
        expect(audioTd.findAll('checkbox-stub')).toHaveLength(2)
    })

    it('renders one subtitle checkbox per subtitle stream', () => {
        mediaStore.files = [makeFile({
            audio_streams: [],
            subtitle_streams: [
                { id: 10, language: 'en', title: null },
                { id: 11, language: 'fr', title: null },
            ],
        })]
        const wrapper = mountSmartTable()
        const subtitlesTd = wrapper.findAll('td')[2]
        expect(subtitlesTd.findAll('checkbox-stub')).toHaveLength(2)
    })

    it('shows audio stream title when present', () => {
        mediaStore.files = [makeFile({
            audio_streams: [{ id: 1, language: 'en', title: 'Director Commentary' }],
            subtitle_streams: [],
        })]
        const wrapper = mountSmartTable()
        expect(wrapper.text()).toContain('Director Commentary')
    })

    it('hides audio stream title when absent', () => {
        mediaStore.files = [makeFile({
            audio_streams: [{ id: 1, language: 'en', title: null }],
            subtitle_streams: [],
        })]
        const wrapper = mountSmartTable()
        // No parenthesized title should appear
        expect(wrapper.text()).not.toMatch(/\(.*\)/)
    })

    it('shows subtitle stream title when present', () => {
        mediaStore.files = [makeFile({
            audio_streams: [],
            subtitle_streams: [{ id: 10, language: 'en', title: 'English SDH' }],
        })]
        const wrapper = mountSmartTable()
        expect(wrapper.text()).toContain('English SDH')
    })

    it('renders multiple files as separate rows', () => {
        mediaStore.files = [
            makeFile({ name: 'ep1.mkv' }),
            makeFile({ name: 'ep2.mkv' }),
        ]
        const wrapper = mountSmartTable()
        expect(wrapper.findAll('tr')).toHaveLength(2)
        expect(wrapper.text()).toContain('ep1.mkv')
        expect(wrapper.text()).toContain('ep2.mkv')
    })
})
