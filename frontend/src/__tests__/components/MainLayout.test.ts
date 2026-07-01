import { afterEach, describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import type { Component } from 'vue'

// Shallow-mount: all child SFCs are auto-stubbed, no store setup needed.
async function mountLayout(showLogs = 'false') {
    vi.resetModules()
    vi.stubEnv('VITE_SHOW_LOGS', showLogs)
    const { default: MainLayout } = await import('../../components/MainLayout.vue')
    return mount(MainLayout as Component, { shallow: true })
}

afterEach(() => {
    vi.unstubAllEnvs()
})

describe('MainLayout', () => {
    it('renders the application title', async () => {
        const wrapper = await mountLayout()
        expect(wrapper.text()).toContain('Video Cleaner Web')
    })

    it('renders the "Input Folders" panel header', async () => {
        const wrapper = await mountLayout()
        expect(wrapper.text()).toContain('Input Folders')
    })

    it('hides the processing log panel by default', async () => {
        const wrapper = await mountLayout()
        expect(wrapper.text()).not.toContain('Processing Status')
        expect(wrapper.findComponent({ name: 'JobProgress' }).exists()).toBe(false)
        expect(wrapper.findComponent({ name: 'JobLogs' }).exists()).toBe(false)
    })

    it('includes FolderTree component', async () => {
        const wrapper = await mountLayout()
        expect(wrapper.findComponent({ name: 'FolderTree' }).exists()).toBe(true)
    })

    it('includes JobsList component', async () => {
        const wrapper = await mountLayout()
        expect(wrapper.findComponent({ name: 'JobsList' }).exists()).toBe(true)
    })

    it('includes TopToolbar component', async () => {
        const wrapper = await mountLayout()
        expect(wrapper.findComponent({ name: 'TopToolbar' }).exists()).toBe(true)
    })

    it('includes MediaTable component', async () => {
        const wrapper = await mountLayout()
        expect(wrapper.findComponent({ name: 'MediaTable' }).exists()).toBe(true)
    })

    it('renders the processing log panel when enabled', async () => {
        const wrapper = await mountLayout('true')
        expect(wrapper.text()).toContain('Processing Status')
        expect(wrapper.findComponent({ name: 'JobProgress' }).exists()).toBe(true)
        expect(wrapper.findComponent({ name: 'JobLogs' }).exists()).toBe(true)
    })
})
