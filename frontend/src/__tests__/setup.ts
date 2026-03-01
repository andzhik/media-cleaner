import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// Stub all PrimeVue components so tests don't need PrimeVue installed
config.global.stubs = {
    ProgressBar: true,
    DataTable: true,
    Column: true,
    Checkbox: true,
    Button: true,
    InputText: true,
    RadioButton: true,
    Tree: true,
}

// Mock EventSource (not provided by jsdom)
class MockEventSource {
    url: string
    listeners: Record<string, ((e: MessageEvent) => void)[]> = {}
    onerror: ((e: Event) => void) | null = null
    closed = false

    constructor(url: string) {
        this.url = url
    }

    addEventListener(type: string, handler: (e: MessageEvent) => void) {
        if (!this.listeners[type]) this.listeners[type] = []
        this.listeners[type].push(handler)
    }

    dispatchEvent(type: string, data: unknown) {
        const event = { data: JSON.stringify(data) } as MessageEvent
        this.listeners[type]?.forEach(h => h(event))
    }

    close() {
        this.closed = true
    }
}

vi.stubGlobal('EventSource', MockEventSource)

export { MockEventSource }
