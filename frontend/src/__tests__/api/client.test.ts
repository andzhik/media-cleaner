import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
    fetchTree,
    fetchList,
    startProcess,
    fetchJob,
    getJobEventsUrl,
    getJobsListEventsUrl,
    cancelJob,
} from '../../api/client'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function mockOk(body: unknown) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response)
}

function mockFail() {
    return Promise.resolve({ ok: false } as Response)
}

beforeEach(() => mockFetch.mockReset())

describe('fetchTree', () => {
    it('resolves with json on ok response', async () => {
        mockFetch.mockReturnValueOnce(mockOk({ name: 'root' }))
        const result = await fetchTree()
        expect(result).toEqual({ name: 'root' })
        expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/tree'))
    })

    it('throws on non-ok response', async () => {
        mockFetch.mockReturnValueOnce(mockFail())
        await expect(fetchTree()).rejects.toThrow('Failed to fetch tree')
    })
})

describe('fetchList', () => {
    it('sends dir as query param and returns json', async () => {
        mockFetch.mockReturnValueOnce(mockOk({ files: [], languages: [] }))
        const result = await fetchList('/movies')
        expect(result).toEqual({ files: [], languages: [] })
        expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('dir=%2Fmovies'))
    })

    it('throws on non-ok response', async () => {
        mockFetch.mockReturnValueOnce(mockFail())
        await expect(fetchList('/')).rejects.toThrow('Failed to fetch list')
    })
})

describe('startProcess', () => {
    it('sends POST with json body and returns json', async () => {
        const payload = { dir: '/input', output_dir: '/output' }
        mockFetch.mockReturnValueOnce(mockOk({ jobId: 'abc' }))
        const result = await startProcess(payload)
        expect(result).toEqual({ jobId: 'abc' })
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/process'),
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
        )
    })

    it('throws on non-ok response', async () => {
        mockFetch.mockReturnValueOnce(mockFail())
        await expect(startProcess({})).rejects.toThrow('Failed to start process')
    })
})

describe('fetchJob', () => {
    it('resolves with job data', async () => {
        mockFetch.mockReturnValueOnce(mockOk({ job_id: 'abc', status: 'pending' }))
        const result = await fetchJob('abc')
        expect(result).toEqual({ job_id: 'abc', status: 'pending' })
        expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/jobs/abc'))
    })

    it('throws on non-ok response', async () => {
        mockFetch.mockReturnValueOnce(mockFail())
        await expect(fetchJob('abc')).rejects.toThrow('Failed to fetch job')
    })
})

describe('getJobEventsUrl', () => {
    it('returns url containing job id and /events', () => {
        const url = getJobEventsUrl('my-job')
        expect(url).toContain('/jobs/my-job/events')
    })
})

describe('getJobsListEventsUrl', () => {
    it('returns url containing /jobs/events', () => {
        const url = getJobsListEventsUrl()
        expect(url).toContain('/jobs/events')
    })
})

describe('cancelJob', () => {
    it('sends DELETE request and returns json', async () => {
        mockFetch.mockReturnValueOnce(mockOk({ cancelled: true }))
        const result = await cancelJob('abc')
        expect(result).toEqual({ cancelled: true })
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/jobs/abc'),
            expect.objectContaining({ method: 'DELETE' })
        )
    })

    it('throws on non-ok response', async () => {
        mockFetch.mockReturnValueOnce(mockFail())
        await expect(cancelJob('abc')).rejects.toThrow('Failed to cancel job')
    })
})
