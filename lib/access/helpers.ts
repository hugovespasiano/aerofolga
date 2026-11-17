import type { Profile } from "@/types/access";

export function isAdmin(profile: Profile): boolean {
  return profile.role === "admin";
}

export function isPremium(profile: Profile): boolean {
  return profile.plan === "premium";
}

export function isActive(profile: Profile): boolean {
  return profile.status === "active";
}

export interface AccessRules {
  requireAdmin?: boolean;
  requirePremium?: boolean;
  requireActive?: boolean;
}

/**
 * hasAccess
 * 
 * Agregador configurável para validar rapidamente múltiplas regras de roteamento simultâneas.
 * NÃO conhece regras específicas da aplicação. Apenas combina role, plan e status.
 */
export function hasAccess(profile: Profile | null, rules: AccessRules): boolean {
  if (!profile) {
    return false;
  }

  // Se a rota exige que a conta esteja ativa (maioria das rotas) e ela não está:
  if (rules.requireActive !== false && !isActive(profile)) {
    return false;
  }

  // Se a rota exige ser admin e o usuário não é:
  if (rules.requireAdmin && !isAdmin(profile)) {
    return false;
  }

  // Se a rota exige ser premium e o usuário não é:
  if (rules.requirePremium && !isPremium(profile)) {
    return false;
  }

  return true;
}
