import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mediaStore } from '../../stores/mediaStore'

vi.mock('../../api/client', () => ({
    fetchTree: vi.fn(),
    fetchList: vi.fn(),
}))

import { fetchTree, fetchList } from '../../api/client'

const mockFetchTree = vi.mocked(fetchTree)
const mockFetchList = vi.mocked(fetchList)

function resetStore() {
    Object.assign(mediaStore, {
        tree: null,
        currentDir: null,
        files: [],
        languages: [],
        selectedLanguages: [],
        loading: false,
        error: null,
        expandedKeys: {},
    })
}

const sampleTree = {
    rel_path: '/',
    name: 'root',
    children: [
        { rel_path: '/movies', name: 'movies', children: [] },
    ],
}

const sampleListData = {
    files: [
        {
            rel_path: 'movie.mkv',
            name: 'movie.mkv',
            audio_streams: [{ id: 1, language: 'en' }, { id: 2, language: 'fr' }],
            subtitle_streams: [{ id: 10, language: 'en' }],
        },
    ],
    languages: ['en', 'fr'],
}

beforeEach(() => {
    resetStore()
    mockFetchTree.mockReset()
    mockFetchList.mockReset()
})

describe('loadTree', () => {
    it('sets tree and expands all nodes', async () => {
        mockFetchTree.mockResolvedValueOnce(sampleTree)
        mockFetchList.mockResolvedValueOnce({ files: [], languages: [] })

        await mediaStore.loadTree()

        expect(mediaStore.tree).toMatchObject({ name: 'root' })
        expect(mediaStore.expandedKeys['/']).toBe(true)
        expect(mediaStore.expandedKeys['/movies']).toBe(true)
    })

    it('calls loadDirectory("/") after loading tree', async () => {
        mockFetchTree.mockResolvedValueOnce(sampleTree)
        mockFetchList.mockResolvedValueOnce(sampleListData)

        await mediaStore.loadTree()

        expect(mockFetchList).toHaveBeenCalledWith('/')
    })

    it('sets error on fetch failure', async () => {
        mockFetchTree.mockRejectedValueOnce(new Error('network error'))

        await mediaStore.loadTree()

        expect(mediaStore.error).toBe('network error')
        expect(mediaStore.loading).toBe(false)
    })

    it('clears loading on completion', async () => {
        mockFetchTree.mockResolvedValueOnce(sampleTree)
        mockFetchList.mockResolvedValueOnce({ files: [], languages: [] })

        await mediaStore.loadTree()

        expect(mediaStore.loading).toBe(false)
    })
})

describe('loadDirectory', () => {
    it('enriches files with includeFile and selectedAudio/selectedSubs', async () => {
        mockFetchList.mockResolvedValueOnce(sampleListData)

        await mediaStore.loadDirectory('/movies')

        expect(mediaStore.currentDir).toBe('/movies')
        expect(mediaStore.files).toHaveLength(1)

        const file = mediaStore.files[0]
        expect(file.includeFile).toBe(true)
        expect(file.selectedAudio).toEqual([1, 2])
        expect(file.selectedSubs).toEqual([10])
    })

    it('sets languages and selectedLanguages', async () => {
        mockFetchList.mockResolvedValueOnce(sampleListData)

        await mediaStore.loadDirectory('/')

        expect(mediaStore.languages).toEqual(['en', 'fr'])
        expect(mediaStore.selectedLanguages).toEqual(['en', 'fr'])
    })

    it('sets error on fetch failure', async () => {
        mockFetchList.mockRejectedValueOnce(new Error('list failed'))

        await mediaStore.loadDirectory('/bad')

        expect(mediaStore.error).toBe('list failed')
        expect(mediaStore.loading).toBe(false)
    })
})

describe('toggleLanguage', () => {
    beforeEach(async () => {
        mockFetchList.mockResolvedValueOnce(sampleListData)
        await mediaStore.loadDirectory('/')
    })

    it('deselects audio streams of a given language', () => {
        mediaStore.toggleLanguage('en', 'audio', false)

        const file = mediaStore.files[0]
        expect(file.selectedAudio).not.toContain(1)
        expect(file.selectedAudio).toContain(2) // 'fr' unchanged
    })

    it('reselects audio streams of a given language', () => {
        mediaStore.files[0].selectedAudio = []

        mediaStore.toggleLanguage('en', 'audio', true)

        expect(mediaStore.files[0].selectedAudio).toContain(1)
    })

    it('deselects subtitle streams of a given language', () => {
        mediaStore.toggleLanguage('en', 'subtitle', false)

        expect(mediaStore.files[0].selectedSubs).not.toContain(10)
    })

    it('toggles both audio and subtitle when type is "both"', () => {
        mediaStore.toggleLanguage('en', 'both', false)

        const file = mediaStore.files[0]
        expect(file.selectedAudio).not.toContain(1)
        expect(file.selectedSubs).not.toContain(10)
    })

    it('skips files with includeFile=false', () => {
        mediaStore.files[0].includeFile = false

        mediaStore.toggleLanguage('en', 'audio', false)

        // selectedAudio unchanged because file is excluded
        expect(mediaStore.files[0].selectedAudio).toContain(1)
    })
})
