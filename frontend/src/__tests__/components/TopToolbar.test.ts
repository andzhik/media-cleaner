import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import TopToolbar from '../../components/TopToolbar.vue'
import { mediaStore } from '../../stores/mediaStore'
import { jobStore } from '../../stores/jobStore'

vi.mock('../../stores/mediaStore', () => ({
    mediaStore: {
        currentDir: null as string | null,
        files: [] as any[],
        languages: [] as string[],
        selectedLanguages: [] as string[],
        toggleLanguage: vi.fn(),
    },
}))

vi.mock('../../stores/jobStore', () => ({
    jobStore: {
        activeJobId: null as string | null,
        status: null as string | null,
        startJob: vi.fn(),
    },
}))

// Proper stubs so .props() is available
const ButtonStub = defineComponent({
    name: 'Button',
    props: ['label', 'icon', 'loading', 'disabled'],
    template: '<button />',
})
const InputTextStub = defineComponent({
    name: 'InputText',
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<input />',
})
const RadioButtonStub = defineComponent({
    name: 'RadioButton',
    props: ['modelValue', 'inputId', 'name', 'value'],
    template: '<input type="radio" />',
})

const localStubs = {
    Button: ButtonStub,
    InputText: InputTextStub,
    RadioButton: RadioButtonStub,
    Checkbox: true,
}

function mountToolbar() {
    return mount(TopToolbar, { global: { stubs: localStubs } })
}

function resetStores() {
    Object.assign(mediaStore, { currentDir: null, files: [], languages: [], selectedLanguages: [] })
    Object.assign(jobStore, { activeJobId: null, status: null })
    vi.mocked(jobStore.startJob).mockReset()
    vi.mocked(mediaStore.toggleLanguage).mockReset()
}

beforeEach(() => resetStores())

describe('TopToolbar', () => {
    it('sets outputDir from currentDir on mount (immediate watch)', () => {
        // Watch has { immediate: true }, so it runs with the initial value
        mediaStore.currentDir = '/input/shows'
        const wrapper = mountToolbar()

        const input = wrapper.findComponent(InputTextStub)
        const val = input.props('modelValue') as string
        expect(val).toContain('/input/shows')
    })

    it('Process button is disabled when no currentDir', () => {
        mediaStore.currentDir = null
        const wrapper = mountToolbar()
        const btn = wrapper.findComponent(ButtonStub)
        expect(btn.props('disabled')).toBe(true)
    })

    it('Process button is enabled when currentDir is set', () => {
        mediaStore.currentDir = '/movies'
        const wrapper = mountToolbar()
        const btn = wrapper.findComponent(ButtonStub)
        expect(btn.props('disabled')).toBe(false)
    })

    it('calls jobStore.startJob with correct payload on process click', async () => {
        vi.mocked(jobStore.startJob).mockResolvedValueOnce(undefined)

        mediaStore.currentDir = '/input'
        mediaStore.selectedLanguages = ['en']
        mediaStore.files = [
            {
                rel_path: 'a.mkv',
                includeFile: true,
                selectedAudio: [1],
                selectedSubs: [10],
                audio_streams: [],
                subtitle_streams: [],
            },
            {
                rel_path: 'b.mkv',
                includeFile: false,
                selectedAudio: [],
                selectedSubs: [],
                audio_streams: [],
                subtitle_streams: [],
            },
        ]

        const wrapper = mountToolbar()
        await wrapper.findComponent(ButtonStub).vm.$emit('click')

        expect(jobStore.startJob).toHaveBeenCalledWith(
            expect.objectContaining({
                dir: '/input',
                audio_languages: ['en'],
                subtitle_languages: ['en'],
                selections: [
                    { rel_path: 'a.mkv', audio_stream_ids: [1], subtitle_stream_ids: [10] },
                ],
            })
        )
    })

    it('Process button is never in loading state regardless of job state', () => {
        mediaStore.currentDir = '/movies'
        jobStore.activeJobId = 'job-1'
        jobStore.status = 'processing'
        const wrapper = mountToolbar()
        expect(wrapper.findComponent(ButtonStub).props('loading')).toBeFalsy()
    })

    it('Process button is disabled when output directory is manually cleared', async () => {
        // currentDir is set, so watch sets outputDir — button should be enabled
        mediaStore.currentDir = '/movies'
        const wrapper = mountToolbar()
        expect(wrapper.findComponent(ButtonStub).props('disabled')).toBe(false)

        // User clears the output dir field
        await wrapper.findComponent(InputTextStub).vm.$emit('update:modelValue', '')
        await nextTick()

        // Now button must be disabled even though currentDir is still set
        expect(wrapper.findComponent(ButtonStub).props('disabled')).toBe(true)
    })
})
