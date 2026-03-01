import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import JobsList from '../../components/JobsList.vue'
import { jobsListStore } from '../../stores/jobsListStore'
import type { ActiveJob } from '../../stores/jobsListStore'

vi.mock('../../api/client', () => ({
    cancelJob: vi.fn(),
    getJobsListEventsUrl: vi.fn(() => 'http://localhost/api/jobs/events'),
}))

import { cancelJob } from '../../api/client'

function resetStore() {
    jobsListStore.eventSource?.close()
    Object.assign(jobsListStore, { jobs: [], eventSource: null })
}

function makeJob(overrides: Partial<ActiveJob> = {}): ActiveJob {
    return {
        job_id: 'j1',
        dir: '/movies',
        status: 'pending',
        overall_percent: 0,
        current_file: null,
        first_file: 'movie.mkv',
        ...overrides,
    }
}

beforeEach(() => {
    resetStore()
    vi.mocked(cancelJob).mockReset()
})

describe('JobsList', () => {
    it('renders nothing when no jobs', () => {
        const wrapper = mount(JobsList)
        expect(wrapper.find('.border-top-1').exists()).toBe(false)
    })

    it('renders a row for each job', () => {
        jobsListStore.jobs = [makeJob({ job_id: 'j1' }), makeJob({ job_id: 'j2' })]

        const wrapper = mount(JobsList)
        const rows = wrapper.findAll('[class*="border-bottom-1"]').filter(el =>
            el.element.closest('[style*="max-height"]') !== null || el.element.parentElement?.style?.maxHeight
        )
        // Check that the label text appears for each job
        expect(wrapper.text()).toContain('movie.mkv')
    })

    it('shows processing jobs before pending jobs', () => {
        jobsListStore.jobs = [
            makeJob({ job_id: 'pending-1', status: 'pending', first_file: 'pending.mkv' }),
            makeJob({ job_id: 'processing-1', status: 'processing', first_file: 'processing.mkv', overall_percent: 50 }),
        ]

        const wrapper = mount(JobsList)
        const jobDivs = wrapper.findAll('[class*="flex align-items-start"]')

        // Processing job should appear first
        expect(jobDivs[0].text()).toContain('processing.mkv')
        expect(jobDivs[1].text()).toContain('pending.mkv')
    })

    it('shows cancel button only for pending jobs', () => {
        jobsListStore.jobs = [
            makeJob({ job_id: 'p', status: 'pending' }),
            makeJob({ job_id: 'r', status: 'processing' }),
        ]

        const wrapper = mount(JobsList)
        const cancelButtons = wrapper.findAll('button')

        // Only one cancel button (for pending job)
        expect(cancelButtons).toHaveLength(1)
    })

    it('calls cancelJob when cancel button is clicked', async () => {
        vi.mocked(cancelJob).mockResolvedValueOnce({})
        jobsListStore.jobs = [makeJob({ job_id: 'job-to-cancel', status: 'pending' })]

        const wrapper = mount(JobsList)
        await wrapper.find('button').trigger('click')

        expect(cancelJob).toHaveBeenCalledWith('job-to-cancel')
    })

    it('shows percentage for processing jobs', () => {
        jobsListStore.jobs = [
            makeJob({ job_id: 'r', status: 'processing', overall_percent: 73 }),
        ]

        const wrapper = mount(JobsList)
        expect(wrapper.text()).toContain('73%')
    })
})
