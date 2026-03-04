import { describe, it, expect, vi, beforeEach } from 'vitest'
import { jobStore } from '../../stores/jobStore'
import { MockEventSource } from '../setup'

vi.mock('../../api/client', () => ({
    startProcess: vi.fn(),
    getJobEventsUrl: vi.fn((id: string) => `http://localhost/api/jobs/${id}/events`),
}))

vi.mock('../../stores/jobsListStore', () => ({
    jobsListStore: { jobs: [] as any[] },
}))

import { startProcess } from '../../api/client'
import { jobsListStore } from '../../stores/jobsListStore'

const mockStartProcess = vi.mocked(startProcess)

function resetStore() {
    jobStore.eventSource?.close()
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

beforeEach(() => {
    resetStore()
    mockStartProcess.mockReset()
    ;(jobsListStore as any).jobs = []
    vi.mocked(EventSource as unknown as typeof MockEventSource)
})

describe('startJob', () => {
    it('resets state and starts a new job when no job is active', async () => {
        mockStartProcess.mockResolvedValueOnce({ jobId: 'job-1' })

        await jobStore.startJob({ dir: '/input' })

        expect(jobStore.activeJobId).toBe('job-1')
        expect(jobStore.status).toBe('starting')
        expect(jobStore.error).toBeNull()
        expect(jobStore.logs).toEqual([])
    })

    it('sets error when startProcess throws', async () => {
        mockStartProcess.mockRejectedValueOnce(new Error('server error'))

        await jobStore.startJob({ dir: '/input' })

        expect(jobStore.error).toBe('server error')
        expect(jobStore.activeJobId).toBeNull()
    })

    it('does not clear logs or switch when a job is actively running', async () => {
        // Simulate an active running job
        jobStore.activeJobId = 'job-1'
        jobStore.status = 'processing'
        jobStore.logs = ['existing log line']
        jobStore.progress = 50

        mockStartProcess.mockResolvedValueOnce({ jobId: 'job-2' })

        await jobStore.startJob({ dir: '/input2' })

        // Should keep watching job-1
        expect(jobStore.activeJobId).toBe('job-1')
        expect(jobStore.logs).toEqual(['existing log line'])
        expect(jobStore.progress).toBe(50)
        expect(jobStore.status).toBe('processing')
    })

    it('switches to new job when current job is completed', async () => {
        jobStore.activeJobId = 'job-1'
        jobStore.status = 'completed'

        mockStartProcess.mockResolvedValueOnce({ jobId: 'job-2' })

        await jobStore.startJob({ dir: '/input2' })

        expect(jobStore.activeJobId).toBe('job-2')
        expect(jobStore.status).toBe('starting')
        expect(jobStore.logs).toEqual([])
    })

    it('switches to new job when current job is failed', async () => {
        jobStore.activeJobId = 'job-1'
        jobStore.status = 'failed'

        mockStartProcess.mockResolvedValueOnce({ jobId: 'job-2' })

        await jobStore.startJob({ dir: '/input2' })

        expect(jobStore.activeJobId).toBe('job-2')
        expect(jobStore.status).toBe('starting')
    })
})

describe('connectEvents', () => {
    it('creates an EventSource for the job', () => {
        jobStore.connectEvents('job-42')

        expect(jobStore.eventSource).not.toBeNull()
        expect((jobStore.eventSource as unknown as MockEventSource).url).toContain('job-42')
    })

    it('closes previous eventSource before opening a new one', () => {
        jobStore.connectEvents('job-1')
        const first = jobStore.eventSource as unknown as MockEventSource

        jobStore.connectEvents('job-2')

        expect(first.closed).toBe(true)
        expect((jobStore.eventSource as unknown as MockEventSource).url).toContain('job-2')
    })

    it('updates status and progress on status event', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.dispatchEvent('status', {
            status: 'processing',
            overall_percent: 42,
            current_file: 'movie.mkv',
        })

        expect(jobStore.status).toBe('processing')
        expect(jobStore.progress).toBe(42)
        expect(jobStore.currentFile).toBe('movie.mkv')
    })

    it('appends log lines on log event', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.dispatchEvent('log', ['line 1', 'line 2'])

        expect(jobStore.logs).toEqual(['line 1', 'line 2'])

        es.dispatchEvent('log', ['line 3'])

        expect(jobStore.logs).toEqual(['line 1', 'line 2', 'line 3'])
    })

    it('closes eventSource on completed status', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.dispatchEvent('status', {
            status: 'completed',
            overall_percent: 100,
            current_file: null,
        })

        expect(es.closed).toBe(true)
        expect(jobStore.eventSource).toBeNull()
    })

    it('closes eventSource on failed status', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.dispatchEvent('status', {
            status: 'failed',
            overall_percent: 0,
            current_file: null,
        })

        expect(es.closed).toBe(true)
        expect(jobStore.eventSource).toBeNull()
    })

    it('closes eventSource on SSE error', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.onerror?.(new Event('error'))

        expect(es.closed).toBe(true)
    })

    it('auto-switches to next processing job when current job completes', () => {
        jobStore.activeJobId = 'job-1'
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        // Simulate another job running in jobsListStore
        ;(jobsListStore as any).jobs = [
            { job_id: 'job-2', status: 'processing', overall_percent: 30, current_file: 'vid.mp4' },
        ]

        es.dispatchEvent('status', {
            status: 'completed',
            overall_percent: 100,
            current_file: null,
        })

        expect(es.closed).toBe(true)
        expect(jobStore.activeJobId).toBe('job-2')
        expect(jobStore.status).toBe('processing')
        expect(jobStore.progress).toBe(30)
        expect(jobStore.currentFile).toBe('vid.mp4')
        expect(jobStore.logs).toEqual([])
        // New EventSource should be connected
        expect(jobStore.eventSource).not.toBeNull()
        expect((jobStore.eventSource as unknown as MockEventSource).url).toContain('job-2')
    })

    it('auto-switches to next pending job when no processing job exists', () => {
        jobStore.activeJobId = 'job-1'
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        ;(jobsListStore as any).jobs = [
            { job_id: 'job-2', status: 'pending', overall_percent: 0, current_file: null },
        ]

        es.dispatchEvent('status', {
            status: 'completed',
            overall_percent: 100,
            current_file: null,
        })

        expect(es.closed).toBe(true)
        expect(jobStore.activeJobId).toBe('job-2')
        expect(jobStore.status).toBe('pending')
        expect(jobStore.logs).toEqual([])
        expect(jobStore.eventSource).not.toBeNull()
        expect((jobStore.eventSource as unknown as MockEventSource).url).toContain('job-2')
    })

    it('does not auto-switch when no other processing job exists', () => {
        jobStore.activeJobId = 'job-1'
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        ;(jobsListStore as any).jobs = []

        es.dispatchEvent('status', {
            status: 'completed',
            overall_percent: 100,
            current_file: null,
        })

        expect(jobStore.activeJobId).toBe('job-1')
        expect(jobStore.eventSource).toBeNull()
    })
})
