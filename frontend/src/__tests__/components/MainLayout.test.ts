import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MainLayout from '../../components/MainLayout.vue'

// Shallow-mount: all child SFCs are auto-stubbed, no store setup needed
function mountLayout() {
    return mount(MainLayout, { shallow: true })
}

describe('MainLayout', () => {
    it('renders the application title', () => {
        const wrapper = mountLayout()
        expect(wrapper.text()).toContain('Video Cleaner Web')
    })

    it('renders the "Input Folders" panel header', () => {
        const wrapper = mountLayout()
        expect(wrapper.text()).toContain('Input Folders')
    })

    it('renders the "Processing Status" panel header', () => {
        const wrapper = mountLayout()
        expect(wrapper.text()).toContain('Processing Status')
    })

    it('includes FolderTree component', () => {
        const wrapper = mountLayout()
        expect(wrapper.findComponent({ name: 'FolderTree' }).exists()).toBe(true)
    })

    it('includes JobsList component', () => {
        const wrapper = mountLayout()
        expect(wrapper.findComponent({ name: 'JobsList' }).exists()).toBe(true)
    })

    it('includes TopToolbar component', () => {
        const wrapper = mountLayout()
        expect(wrapper.findComponent({ name: 'TopToolbar' }).exists()).toBe(true)
    })

    it('includes MediaTable component', () => {
        const wrapper = mountLayout()
        expect(wrapper.findComponent({ name: 'MediaTable' }).exists()).toBe(true)
    })

    it('includes JobProgress component', () => {
        const wrapper = mountLayout()
        expect(wrapper.findComponent({ name: 'JobProgress' }).exists()).toBe(true)
    })

    it('includes JobLogs component', () => {
        const wrapper = mountLayout()
        expect(wrapper.findComponent({ name: 'JobLogs' }).exists()).toBe(true)
    })
})
