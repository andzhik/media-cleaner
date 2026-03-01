import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import JobProgress from '../../components/JobProgress.vue'
import { jobStore } from '../../stores/jobStore'

function resetStore() {
    Object.assign(jobStore, {
        activeJobId: null,
        status: null,
        progress: 0,
        currentFile: null,
        logs: [],
        error: null,
        eventSource: null,
    })
}

beforeEach(() => resetStore())

describe('JobProgress', () => {
    it('renders nothing when no active job', () => {
        const wrapper = mount(JobProgress)
        expect(wrapper.find('.p-2').exists()).toBe(false)
    })

    it('renders progress info when a job is active', () => {
        jobStore.activeJobId = 'job-1'
        jobStore.progress = 55.5
        jobStore.currentFile = 'ep1.mkv'

        const wrapper = mount(JobProgress)

        expect(wrapper.text()).toContain('55.5%')
        expect(wrapper.text()).toContain('ep1.mkv')
    })

    it('shows "Done" when status is completed', () => {
        jobStore.activeJobId = 'job-1'
        jobStore.status = 'completed'
        jobStore.progress = 100

        const wrapper = mount(JobProgress)

        expect(wrapper.text()).toContain('Done')
    })

    it('shows "Failed" when status is failed', () => {
        jobStore.activeJobId = 'job-1'
        jobStore.status = 'failed'

        const wrapper = mount(JobProgress)

        expect(wrapper.text()).toContain('Failed')
    })

    it('shows "Initializing..." when no currentFile and not terminal', () => {
        jobStore.activeJobId = 'job-1'
        jobStore.status = 'starting'
        jobStore.currentFile = null

        const wrapper = mount(JobProgress)

        expect(wrapper.text()).toContain('Initializing...')
    })
})
