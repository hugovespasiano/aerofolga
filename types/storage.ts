export type StorageBucketType = "system_public" | "system_private";

export interface StorageUploadOptions {
  maxSizeBytes?: number;
  allowedMimeTypes?: string[];
}

export interface StorageUploadResult {
  success: boolean;
  path?: string;
  url?: string;
  error?: string;
}

export interface FileMetadata {
  mimetype: string;
  size: number;
}
