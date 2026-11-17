import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// This check can be removed, it is just for tutorial purposes
export const hasEnvVars =
  process.env.NEXT_PUBLIC_SUPABASE_URL &&
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

/**
 * Valida a URL de redirecionamento para prevenir ataques de Open Redirect.
 * Permite apenas caminhos locais absolutos seguros (iniciados com / e não com // ou /\).
 * Rejeita URLs externas absolutas.
 */
export function getSafeRedirectUrl(next: string | null): string {
  if (!next) return "/";
  if (next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/\\")) {
    return next;
  }
  return "/";
}
