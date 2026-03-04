import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import JobLogs from '../../components/JobLogs.vue'
import { jobStore } from '../../stores/jobStore'

beforeEach(() => {
    jobStore.fileProgress = {}
})

describe('JobLogs', () => {
    it('renders no rows when fileProgress is empty', () => {
        const wrapper = mount(JobLogs)
        expect(wrapper.findAll('.white-space-pre-wrap')).toHaveLength(0)
    })

    it('renders a queued row', () => {
        jobStore.fileProgress = {
            '/video/a.mkv': { status: 'queued' },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(1)
        expect(rows[0].text()).toBe('a.mkv: [queued]')
    })

    it('renders a done row with checkmark', () => {
        jobStore.fileProgress = {
            '/video/b.mkv': { status: 'done', frame: 300, total_frames: 300, fps: 25, q: -1.0, size_bytes: 10 * 1048576, total_size_bytes: 10 * 1048576, time: '00:00:12', total_time: '00:00:12', bitrate: '4500kbits/s', speed: 6.0, percent: 100 },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(1)
        expect(rows[0].text()).toContain('b.mkv:')
        expect(rows[0].text()).toContain('frame=300/300')
        expect(rows[0].text()).toContain('✓')
    })

    it('renders a processing row without checkmark', () => {
        jobStore.fileProgress = {
            '/video/c.mkv': { status: 'processing', frame: 100, total_frames: 300, fps: 25, q: -1.0, size_bytes: 3 * 1048576, total_size_bytes: 10 * 1048576, time: '00:00:04', total_time: '00:00:12', bitrate: '4500kbits/s', speed: 2.0, percent: 33 },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(1)
        expect(rows[0].text()).toContain('c.mkv:')
        expect(rows[0].text()).toContain('frame=100/300')
        expect(rows[0].text()).not.toContain('✓')
    })

    it('renders a failed row', () => {
        jobStore.fileProgress = {
            '/video/d.mkv': { status: 'failed' },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(1)
        expect(rows[0].text()).toBe('d.mkv: [failed]')
    })

    it('renders multiple files in order', () => {
        jobStore.fileProgress = {
            '/a.mkv': { status: 'done', percent: 100 },
            '/b.mkv': { status: 'processing', percent: 50 },
            '/c.mkv': { status: 'queued' },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(3)
        expect(rows[0].text()).toContain('a.mkv')
        expect(rows[1].text()).toContain('b.mkv')
        expect(rows[2].text()).toContain('c.mkv: [queued]')
    })

    it('shows metrics without totals when total_frames and total_time are null', () => {
        jobStore.fileProgress = {
            '/video/e.mkv': { status: 'processing', frame: 50, total_frames: null, fps: 25, q: -1.0, size_bytes: 1048576, total_size_bytes: null, time: '00:00:02', total_time: null, bitrate: '4000kbits/s', speed: 1.5, percent: 10 },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows[0].text()).toContain('frame=50')
        expect(rows[0].text()).not.toContain('frame=50/')
        expect(rows[0].text()).toContain('time=00:00:02')
        expect(rows[0].text()).not.toContain('time=00:00:02/')
    })

    it('shows cmd line above metrics when cmd is set', () => {
        jobStore.fileProgress = {
            '/video/f.mkv': { status: 'processing', frame: 10, fps: 25, q: -1.0, percent: 5, cmd: 'ffmpeg -y -i /input/f.mkv /output/f.mkv' },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(2)
        expect(rows[0].text()).toBe('$ ffmpeg -y -i /input/f.mkv /output/f.mkv')
        expect(rows[1].text()).toContain('f.mkv:')
    })

    it('shows done_line below metrics when done_line is set and status is done', () => {
        jobStore.fileProgress = {
            '/video/g.mkv': { status: 'done', frame: 300, total_frames: 300, fps: 25, q: -1.0, percent: 100, done_line: '/input/g.mkv -> /output/g.mkv' },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(2)
        expect(rows[0].text()).toContain('g.mkv:')
        expect(rows[0].text()).toContain('✓')
        expect(rows[1].text()).toBe('/input/g.mkv -> /output/g.mkv')
    })

    it('shows cmd, metrics, and done_line together when all are set', () => {
        jobStore.fileProgress = {
            '/video/h.mkv': {
                status: 'done', frame: 300, total_frames: 300, fps: 25, q: -1.0, percent: 100,
                cmd: 'ffmpeg -y -i /input/h.mkv /output/h.mkv',
                done_line: '/input/h.mkv -> /output/h.mkv',
            },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(3)
        expect(rows[0].text()).toContain('$ ffmpeg')
        expect(rows[1].text()).toContain('h.mkv:')
        expect(rows[2].text()).toContain('/input/h.mkv -> /output/h.mkv')
    })

    it('does not show cmd line when cmd is not set', () => {
        jobStore.fileProgress = {
            '/video/i.mkv': { status: 'processing', frame: 10, fps: 25, q: -1.0, percent: 5 },
        }

        const wrapper = mount(JobLogs)
        const rows = wrapper.findAll('.white-space-pre-wrap')
        expect(rows).toHaveLength(1)
        expect(rows[0].text()).not.toContain('$ ffmpeg')
    })
})
