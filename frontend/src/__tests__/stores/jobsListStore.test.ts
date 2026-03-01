import { describe, it, expect, beforeEach } from 'vitest'
import { jobsListStore } from '../../stores/jobsListStore'
import { MockEventSource } from '../setup'

function resetStore() {
    jobsListStore.eventSource?.close()
    Object.assign(jobsListStore, {
        jobs: [],
        eventSource: null,
    })
}

beforeEach(() => resetStore())

describe('connectEvents', () => {
    it('creates an EventSource', () => {
        jobsListStore.connectEvents()

        expect(jobsListStore.eventSource).not.toBeNull()
        expect((jobsListStore.eventSource as unknown as MockEventSource).url).toContain('/jobs/events')
    })

    it('does not create duplicate EventSource if already connected', () => {
        jobsListStore.connectEvents()
        const first = jobsListStore.eventSource

        jobsListStore.connectEvents()

        expect(jobsListStore.eventSource).toBe(first)
    })

    it('updates jobs list on jobs_list event', () => {
        jobsListStore.connectEvents()
        const es = jobsListStore.eventSource as unknown as MockEventSource

        const jobsData = [
            { job_id: '1', dir: '/movies', status: 'pending', overall_percent: 0, current_file: null, first_file: null },
        ]
        es.dispatchEvent('jobs_list', jobsData)

        expect(jobsListStore.jobs).toHaveLength(1)
        expect(jobsListStore.jobs[0].job_id).toBe('1')
    })

    it('clears eventSource and allows reconnect after error', () => {
        jobsListStore.connectEvents()
        const es = jobsListStore.eventSource as unknown as MockEventSource

        es.onerror?.(new Event('error'))

        expect(jobsListStore.eventSource).toBeNull()

        // Should be able to reconnect
        jobsListStore.connectEvents()
        expect(jobsListStore.eventSource).not.toBeNull()
    })
})

describe('disconnect', () => {
    it('closes eventSource and sets it to null', () => {
        jobsListStore.connectEvents()
        const es = jobsListStore.eventSource as unknown as MockEventSource

        jobsListStore.disconnect()

        expect(es.closed).toBe(true)
        expect(jobsListStore.eventSource).toBeNull()
    })

    it('is safe to call when not connected', () => {
        expect(() => jobsListStore.disconnect()).not.toThrow()
    })
})
