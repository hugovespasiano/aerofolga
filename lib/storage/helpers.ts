import type { StorageUploadOptions } from "@/types/storage";

export function sanitizeFilename(filename: string): string {
  // Mantém apenas alfanuméricos, hífens, underlines e pontos.
  return filename.replace(/[^a-zA-Z0-9.\-_]/g, "").replace(/\.+/g, ".");
}

export function generateSecurePath(userId: string, originalFilename: string): string {
  const sanitized = sanitizeFilename(originalFilename);
  // Usa o UUID (ex: crypto.randomUUID se client-side, ou apenas timestamp se não houver acesso)
  // Como isso pode ser chamado em ambiente Edge/Server, usamos um gerador simples
  const uniqueId = crypto.randomUUID();
  
  const parts = sanitized.split(".");
  const ext = parts.length > 1 ? `.${parts.pop()}` : "";
  
  return `${userId}/${uniqueId}${ext}`;
}

export function validateFile(file: File, options?: StorageUploadOptions): string | null {
  if (options?.maxSizeBytes && file.size > options.maxSizeBytes) {
    return `O tamanho do arquivo excede o limite máximo de ${options.maxSizeBytes} bytes.`;
  }
  
  if (options?.allowedMimeTypes && !options.allowedMimeTypes.includes(file.type)) {
    return `O tipo de arquivo ${file.type} não é permitido.`;
  }
  
  return null;
}
