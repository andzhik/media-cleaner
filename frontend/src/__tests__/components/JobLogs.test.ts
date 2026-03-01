import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import JobLogs from '../../components/JobLogs.vue'
import { jobStore } from '../../stores/jobStore'

beforeEach(() => {
    jobStore.logs = []
})

describe('JobLogs', () => {
    it('renders no log entries when logs are empty', () => {
        const wrapper = mount(JobLogs)
        expect(wrapper.findAll('.white-space-pre-wrap')).toHaveLength(0)
    })

    it('renders each log line', () => {
        jobStore.logs = ['line one', 'line two', 'line three']

        const wrapper = mount(JobLogs)
        const entries = wrapper.findAll('.white-space-pre-wrap')

        expect(entries).toHaveLength(3)
        expect(entries[0].text()).toBe('line one')
        expect(entries[1].text()).toBe('line two')
        expect(entries[2].text()).toBe('line three')
    })
})
