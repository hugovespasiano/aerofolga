import type { OrgRole } from "@/types/organizations";

/**
 * Normaliza um nome para formato slug URL-safe.
 * Ex: "Minha Empresa Inc" -> "minha-empresa-inc"
 */
export function generateSlug(name: string): string {
  const baseSlug = name
    .toLowerCase()
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // remove acentos
    .replace(/[^a-z0-9\s-]/g, "") // remove caracteres especiais
    .replace(/\s+/g, "-") // substitui espacos por hifens
    .replace(/-+/g, "-"); // remove hifens duplicados

  const randomSuffix = Math.random().toString(36).substring(2, 6);
  return `${baseSlug}-${randomSuffix}`;
}

/**
 * Checa se o papel na organização possui privilégios de administração (owner ou admin).
 */
export function isOrgAdmin(role: OrgRole): boolean {
  return role === "owner" || role === "admin";
}

/**
 * Checa se o papel na organização é o dono supremo (owner).
 */
export function isOrgOwner(role: OrgRole): boolean {
  return role === "owner";
}
