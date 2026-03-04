import { describe, it, expect, vi, beforeEach } from 'vitest'
import { jobStore } from '../../stores/jobStore'
import { MockEventSource } from '../setup'

vi.mock('../../api/client', () => ({
    startProcess: vi.fn(),
    getJobEventsUrl: vi.fn((id: string) => `http://localhost/api/jobs/${id}/events`),
}))

import { startProcess } from '../../api/client'

const mockStartProcess = vi.mocked(startProcess)

function resetStore() {
    jobStore.eventSource?.close()
    Object.assign(jobStore, {
        activeJobId: null,
        status: null,
        progress: 0,
        currentFile: null,
        logs: [],
        fileProgress: {},
        error: null,
        eventSource: null,
    })
}

beforeEach(() => {
    resetStore()
    mockStartProcess.mockReset()
    vi.mocked(EventSource as unknown as typeof MockEventSource)
})

describe('startJob', () => {
    it('resets state and starts a new job', async () => {
        mockStartProcess.mockResolvedValueOnce({ jobId: 'job-1' })

        await jobStore.startJob({ dir: '/input' })

        expect(jobStore.activeJobId).toBe('job-1')
        expect(jobStore.status).toBeDefined()
        expect(jobStore.error).toBeNull()
        expect(jobStore.logs).toEqual([])
        expect(jobStore.fileProgress).toEqual({})
    })

    it('sets error when startProcess throws', async () => {
        mockStartProcess.mockRejectedValueOnce(new Error('server error'))

        await jobStore.startJob({ dir: '/input' })

        expect(jobStore.error).toBe('server error')
        expect(jobStore.activeJobId).toBeNull()
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
            logs: ['log line 1'],
            file_progress: { '/movie.mkv': { status: 'processing', percent: 42 } },
        })

        expect(jobStore.status).toBe('processing')
        expect(jobStore.progress).toBe(42)
        expect(jobStore.currentFile).toBe('movie.mkv')
        expect(jobStore.logs).toEqual(['log line 1'])
        expect(jobStore.fileProgress).toEqual({ '/movie.mkv': { status: 'processing', percent: 42 } })
    })

    it('sets fileProgress from status event', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.dispatchEvent('status', {
            status: 'processing',
            overall_percent: 50,
            current_file: 'a.mkv',
            logs: [],
            file_progress: {
                '/a.mkv': { status: 'processing', percent: 50, frame: 100 },
                '/b.mkv': { status: 'queued' },
            },
        })

        expect(jobStore.fileProgress['/a.mkv'].status).toBe('processing')
        expect(jobStore.fileProgress['/b.mkv'].status).toBe('queued')
    })

    it('defaults fileProgress to empty object when field absent', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.dispatchEvent('status', {
            status: 'processing',
            overall_percent: 10,
            current_file: null,
            logs: [],
        })

        expect(jobStore.fileProgress).toEqual({})
    })

    it('closes eventSource on completed status', () => {
        jobStore.connectEvents('job-1')
        const es = jobStore.eventSource as unknown as MockEventSource

        es.dispatchEvent('status', {
            status: 'completed',
            overall_percent: 100,
            current_file: null,
            logs: [],
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
            logs: [],
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
})
