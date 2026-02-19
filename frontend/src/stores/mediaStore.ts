import { reactive } from 'vue';
import { fetchTree, fetchList } from '../api/client';

export const mediaStore = reactive({
    tree: null as any,
    currentDir: null as string | null,
    files: [] as any[],
    languages: [] as string[],
    loading: false,
    error: null as string | null,
    expandedKeys: {} as Record<string, boolean>,

    async loadTree() {
        try {
            this.loading = true;
            const tree = await fetchTree();

            // Expand all nodes by default
            const keys: Record<string, boolean> = {};
            const expandNodes = (node: any) => {
                if (!node) return;
                node.key = node.rel_path;
                keys[node.rel_path] = true;
                if (node.children) {
                    node.children.forEach((c: any) => expandNodes(c));
                }
            };
            expandNodes(tree);
            this.expandedKeys = keys;

            this.tree = tree;
            // Automatically load the root directory
            if (this.tree) {
                await this.loadDirectory('/');
            }
        } catch (e: any) {
            this.error = e.message;
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
            this.files = data.files.map((f: any) => ({
                ...f,
                includeFile: true,
                // Default: select all audio/subs? Or none?
                // Plan says: "bulk-select streams to keep".
                // Let's default to selecting 'unknown' + maybe 'eng'?
                // Better: Select ALL by default, user unchecks? 
                // Or select NONE? 
                // "Stream-pruned" implies removing stuff.
                // Let's start with nothing selected, user selects what to keep.
                // OR select everything, user removes.
                // Let's select "unknown" and English by default?
                // Simplest: Empty selection.
                selectedAudio: [],
                selectedSubs: []
            }));
            this.languages = data.languages;
        } catch (e: any) {
            this.error = e.message;
        } finally {
            this.loading = false;
        }
    },

    toggleLanguage(lang: string, type: 'audio' | 'subtitle' | 'both', selected: boolean) {
        this.files.forEach(f => {
            if (!f.includeFile) return;

            if (type === 'audio' || type === 'both') {
                const hasLang = f.audio_streams.some((s: any) => s.language === lang);
                if (hasLang) {
                    if (selected) {
                        if (!f.selectedAudio.includes(lang)) f.selectedAudio.push(lang);
                    } else {
                        f.selectedAudio = f.selectedAudio.filter((l: string) => l !== lang);
                    }
                }
            }

            if (type === 'subtitle' || type === 'both') {
                const hasLang = f.subtitle_streams.some((s: any) => s.language === lang);
                if (hasLang) {
                    if (selected) {
                        if (!f.selectedSubs.includes(lang)) f.selectedSubs.push(lang);
                    } else {
                        f.selectedSubs = f.selectedSubs.filter((l: string) => l !== lang);
                    }
                }
            }
        });
    }
});
