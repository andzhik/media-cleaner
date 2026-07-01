export interface MediaNode {
    name: string;
    rel_path: string;
    children?: MediaNode[] | null;
    key?: string;
}

export interface Stream {
    id: number;
    language: string;
    title?: string | null;
    codec_type: 'audio' | 'subtitle';
}

export interface ApiMediaFile {
    name: string;
    rel_path: string;
    audio_streams: Stream[];
    subtitle_streams: Stream[];
}

export interface MediaFile extends ApiMediaFile {
    includeFile: boolean;
    selectedAudio: number[];
    selectedSubs: number[];
}

export interface DirectoryContent {
    dir: string;
    files: ApiMediaFile[];
    languages: string[];
}

export interface FileSelection {
    rel_path: string;
    audio_stream_ids: number[];
    subtitle_stream_ids: number[];
}

export interface ProcessRequest {
    dir?: string | null;
    files?: string[] | null;
    output_dir: string;
    audio_languages: string[];
    subtitle_languages: string[];
    selections?: FileSelection[] | null;
}

export interface ProcessResponse {
    jobId: string;
}

export type JobStatusValue = 'pending' | 'processing' | 'completed' | 'failed';

export interface JobStatus {
    job_id: string;
    status: JobStatusValue;
    overall_percent: number;
    current_file: string | null;
    dir: string;
    first_file: string | null;
}

export type ActiveJob = JobStatus & {
    status: Extract<JobStatusValue, 'pending' | 'processing'>;
};

export interface CancelJobResponse {
    ok: boolean;
}
