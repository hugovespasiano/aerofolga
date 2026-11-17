import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { generateSecurePath, validateFile } from "./helpers";
import type { StorageBucketType, StorageUploadOptions, StorageUploadResult } from "@/types/storage";

/**
 * Retorna uma instância do Supabase com a sessão atual do SSR.
 */
async function getStorageClient() {
  const cookieStore = await cookies();
  
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll() {
          // Utilizado primariamente em ambiente de leitura.
        },
      },
    }
  );
}

/**
 * Garante que a operação seja executada com uma identidade autenticada segura,
 * prevenindo spoofing de userId pelo cliente.
 */
async function getSecureUserId(): Promise<string> {
  const supabase = await getStorageClient();
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    throw new Error("Não autorizado. Usuário não autenticado.");
  }
  
  return user.id;
}

/**
 * Upload de arquivo público (bucket 'system_public')
 */
export async function uploadPublicFile(file: File, options?: StorageUploadOptions): Promise<StorageUploadResult> {
  return uploadFile("system_public", file, options);
}

/**
 * Upload de arquivo privado (bucket 'system_private')
 */
export async function uploadPrivateFile(file: File, options?: StorageUploadOptions): Promise<StorageUploadResult> {
  return uploadFile("system_private", file, options);
}

/**
 * Motor genérico de upload agnóstico ao negócio.
 */
async function uploadFile(bucket: StorageBucketType, file: File, options?: StorageUploadOptions): Promise<StorageUploadResult> {
  try {
    const error = validateFile(file, options);
    if (error) {
      return { success: false, error };
    }

    // Identidade derivada do token seguro, ignorando userId arbitrário do cliente
    const userId = await getSecureUserId();
    const path = generateSecurePath(userId, file.name);

    const supabase = await getStorageClient();
    const { data, error: uploadError } = await supabase.storage
      .from(bucket)
      .upload(path, file, { upsert: false });

    if (uploadError) {
      return { success: false, error: uploadError.message };
    }

    let url;
    if (bucket === "system_public") {
      const { data: publicUrlData } = supabase.storage.from(bucket).getPublicUrl(path);
      url = publicUrlData.publicUrl;
    }

    return { success: true, path: data?.path, url };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Erro desconhecido durante o upload";
    return { success: false, error: message };
  }
}

/**
 * Gera uma URL assinada (temporária) para um arquivo no 'system_private'
 */
export async function getSignedDownloadUrl(path: string, expiresInSeconds: number = 3600): Promise<string | null> {
  try {
    // Força a existência da sessão antes de solicitar a URL
    await getSecureUserId();
    
    const supabase = await getStorageClient();
    const { data, error } = await supabase.storage
      .from("system_private")
      .createSignedUrl(path, expiresInSeconds);

    if (error || !data) {
      console.error("Erro ao gerar Signed URL:", error.message);
      return null;
    }
    
    return data.signedUrl;
  } catch {
    return null;
  }
}

/**
 * Recupera a URL pública (permanente) de um arquivo no 'system_public'
 */
export function getPublicUrl(path: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  return `${baseUrl}/storage/v1/object/public/system_public/${path}`;
}

/**
 * Remove arquivo privado
 */
export async function deletePrivateFile(path: string): Promise<boolean> {
  return deleteFile("system_private", path);
}

/**
 * Remove arquivo público
 */
export async function deletePublicFile(path: string): Promise<boolean> {
  return deleteFile("system_public", path);
}

/**
 * Motor genérico de remoção
 */
async function deleteFile(bucket: StorageBucketType, path: string): Promise<boolean> {
  try {
    // A deleção também requer validação de identidade (ou RBAC verificado no RLS via sessão)
    await getSecureUserId(); 
    
    const supabase = await getStorageClient();
    const { error } = await supabase.storage
      .from(bucket)
      .remove([path]);
    
    return !error;
  } catch {
    return false;
  }
}
