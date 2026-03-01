import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import BatchLanguageBar from '../../components/BatchLanguageBar.vue'
import { mediaStore } from '../../stores/mediaStore'

vi.mock('../../stores/mediaStore', () => ({
    mediaStore: {
        languages: [] as string[],
        toggleLanguage: vi.fn(),
    },
}))

// Must render a real <input> so @change receives a proper e.target.checked
const CheckboxStub = defineComponent({
    name: 'Checkbox',
    props: ['binary', 'modelValue', 'value'],
    emits: ['change', 'update:modelValue'],
    template: '<input type="checkbox" @change="$emit(\'change\', $event)" />',
})

function mountBar() {
    return mount(BatchLanguageBar, { global: { stubs: { Checkbox: CheckboxStub } } })
}

beforeEach(() => {
    mediaStore.languages = []
    vi.mocked(mediaStore.toggleLanguage).mockReset()
})

describe('BatchLanguageBar', () => {
    it('renders no checkboxes when languages list is empty', () => {
        const wrapper = mountBar()
        expect(wrapper.findAll('input[type="checkbox"]')).toHaveLength(0)
    })

    it('renders one audio and one subtitle checkbox per language', () => {
        mediaStore.languages = ['en', 'fr']
        const wrapper = mountBar()
        // 2 audio + 2 subtitle = 4
        expect(wrapper.findAll('input[type="checkbox"]')).toHaveLength(4)
    })

    it('shows each language label in both sections', () => {
        mediaStore.languages = ['en', 'fr']
        const wrapper = mountBar()
        const labels = wrapper.findAll('span.ml-1')
        // 2 in audio section + 2 in subtitle section
        expect(labels).toHaveLength(4)
        expect(labels[0].text()).toBe('en')
        expect(labels[1].text()).toBe('fr')
        expect(labels[2].text()).toBe('en')
        expect(labels[3].text()).toBe('fr')
    })

    it('calls toggleLanguage with "audio" type when audio checkbox is checked', async () => {
        mediaStore.languages = ['en']
        const wrapper = mountBar()
        const checkboxes = wrapper.findAll('input[type="checkbox"]')

        checkboxes[0].element.checked = true
        await checkboxes[0].trigger('change')

        expect(mediaStore.toggleLanguage).toHaveBeenCalledWith('en', 'audio', true)
    })

    it('calls toggleLanguage with "audio" type when audio checkbox is unchecked', async () => {
        mediaStore.languages = ['en']
        const wrapper = mountBar()
        const checkboxes = wrapper.findAll('input[type="checkbox"]')

        checkboxes[0].element.checked = false
        await checkboxes[0].trigger('change')

        expect(mediaStore.toggleLanguage).toHaveBeenCalledWith('en', 'audio', false)
    })

    it('calls toggleLanguage with "subtitle" type when subtitle checkbox is checked', async () => {
        mediaStore.languages = ['en']
        const wrapper = mountBar()
        const checkboxes = wrapper.findAll('input[type="checkbox"]')
        // index 0 = audio 'en', index 1 = subtitle 'en'
        checkboxes[1].element.checked = true
        await checkboxes[1].trigger('change')

        expect(mediaStore.toggleLanguage).toHaveBeenCalledWith('en', 'subtitle', true)
    })

    it('calls toggleLanguage with correct language when second language checkbox is toggled', async () => {
        mediaStore.languages = ['en', 'fr']
        const wrapper = mountBar()
        const checkboxes = wrapper.findAll('input[type="checkbox"]')
        // Order: audio-en, audio-fr, subtitle-en, subtitle-fr
        checkboxes[1].element.checked = true
        await checkboxes[1].trigger('change')

        expect(mediaStore.toggleLanguage).toHaveBeenCalledWith('fr', 'audio', true)
    })

    it('renders "Batch Audio:" and "Batch Subs:" section labels', () => {
        const wrapper = mountBar()
        expect(wrapper.text()).toContain('Batch Audio:')
        expect(wrapper.text()).toContain('Batch Subs:')
    })
})
