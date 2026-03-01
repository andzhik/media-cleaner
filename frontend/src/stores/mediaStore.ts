import { reactive } from 'vue';
import { fetchTree, fetchList } from '../api/client';
import type { MediaNode, MediaFile, Stream } from '../types';

export const mediaStore = reactive({
    tree: null as MediaNode | null,
    currentDir: null as string | null,
    files: [] as MediaFile[],
    languages: [] as string[],
    selectedLanguages: [] as string[],
    loading: false,
    error: null as string | null,
    expandedKeys: {} as Record<string, boolean>,

    async loadTree() {
        try {
            this.loading = true;
            const tree = await fetchTree();

            // Expand all nodes by default
            const keys: Record<string, boolean> = {};
            const expandNodes = (node: MediaNode) => {
                if (!node) return;
                node.key = node.rel_path;
                keys[node.rel_path] = true;
                if (node.children) {
                    node.children.forEach((c: MediaNode) => expandNodes(c));
                }
            };
            expandNodes(tree);
            this.expandedKeys = keys;

            this.tree = tree;
            // Automatically load the root directory
            if (this.tree) {
                await this.loadDirectory('/');
            }
        } catch (e: unknown) {
            this.error = (e as Error).message;
        } finally {
            this.loading = false;
        }
    },

    async loadDirectory(dir: string) {
        try {
            this.loading = true;
            this.currentDir = dir;
            const data = await fetchList(dir);

            // Enriched files with selection state
            this.files = (data.files as any[]).map((f): MediaFile => ({
                ...f,
                includeFile: true,
                selectedAudio: f.audio_streams.map((s: Stream) => s.id),
                selectedSubs: f.subtitle_streams.map((s: Stream) => s.id)
            }));
            this.languages = data.languages as string[];
            this.selectedLanguages = [...(data.languages as string[])];
        } catch (e: unknown) {
            this.error = (e as Error).message;
        } finally {
            this.loading = false;
        }
    },

    toggleLanguage(lang: string, type: 'audio' | 'subtitle' | 'both', selected: boolean) {
        this.files.forEach(f => {
            if (!f.includeFile) return;

            if (type === 'audio' || type === 'both') {
                const streamsOfLang = f.audio_streams.filter(s => s.language === lang);
                streamsOfLang.forEach(s => {
                    if (selected) {
                        if (!f.selectedAudio.includes(s.id)) f.selectedAudio.push(s.id);
                    } else {
                        f.selectedAudio = f.selectedAudio.filter((id: number) => id !== s.id);
                    }
                });
            }

            if (type === 'subtitle' || type === 'both') {
                const streamsOfLang = f.subtitle_streams.filter(s => s.language === lang);
                streamsOfLang.forEach(s => {
                    if (selected) {
                        if (!f.selectedSubs.includes(s.id)) f.selectedSubs.push(s.id);
                    } else {
                        f.selectedSubs = f.selectedSubs.filter((id: number) => id !== s.id);
                    }
                });
            }
        });
    }
});
