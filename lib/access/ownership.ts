import type { Profile } from "@/types/access";
import { isAdmin } from "./helpers";

/**
 * AVISO ARQUITETURAL:
 * Estes helpers NÃO SÃO MECANISMOS DE SEGURANÇA DEFINITIVOS.
 * Eles servem exclusivamente para otimização de UX (ex: renderizar ou esconder botões na UI) 
 * e para validações secundárias de fluxo no servidor.
 * 
 * A autoridade final e inquestionável sobre a segurança e acesso aos dados é SEMPRE 
 * o Row Level Security (RLS) no PostgreSQL. Se o Next.js falhar em checar isso, 
 * o banco de dados bloqueará qualquer transação não autorizada.
 */

/**
 * isOwner
 * 
 * Verifica se o usuário atual é o proprietário direto do recurso.
 * Utilizado para comparações simples 1:1.
 */
export function isOwner(profileId: string, resourceOwnerId: string): boolean {
  if (!profileId || !resourceOwnerId) return false;
  return profileId === resourceOwnerId;
}

/**
 * canManageResource
 * 
 * Verifica se o perfil tem permissão para gerenciar (ler/editar/deletar) um recurso.
 * Retorna true se:
 * - O usuário for o dono do recurso.
 * - OU o usuário for um Administrador global (role === 'admin').
 */
export function canManageResource(profile: Profile | null, resourceOwnerId: string): boolean {
  if (!profile) return false;

  // 1. O próprio dono tem acesso total
  if (isOwner(profile.id, resourceOwnerId)) {
    return true;
  }

  // 2. Administradores têm acesso a gerenciar os recursos
  if (isAdmin(profile)) {
    return true;
  }

  return false;
}
