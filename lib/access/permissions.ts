import { redirect } from "next/navigation";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { getAccessProfile } from "@/lib/access/service";
import type { Profile } from "@/types/access";

/**
 * hasPermission
 * 
 * Verifica se o usuário possui determinada permissão no seu array de permissões.
 * 
 * AVISO IMPORTANTE:
 * Quando utilizada no client-side ou para lógica condicional de renderização,
 * esta função serve APENAS para controle de interface (UX). Ela esconde botões 
 * ou desabilita links, mas NÃO deve ser considerada um mecanismo de segurança real.
 * A segurança real (autorização absoluta) ocorrerá sempre no PostgreSQL (RLS) 
 * ou via validação server-side com protectPermission().
 */
export function hasPermission(profile: Profile | null, permission: string): boolean {
  if (!profile || !profile.permissions) {
    return false;
  }
  return profile.permissions.includes(permission);
}

/**
 * protectPermission
 * 
 * Helper Server-Side genérico.
 * Garante que a Rota (Server Component) ou Server Action atual só será
 * executada se o usuário logado possuir a permissão exigida.
 * 
 * Exemplo de uso em page.tsx:
 * await protectPermission("users.edit"); // Se não tiver, redireciona para /forbidden.
 */
export async function protectPermission(permission: string) {
  const cookieStore = await cookies();
  
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll() {
          // Ignorado pois isso é apenas checagem de leitura de Server Component
        },
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    redirect("/auth/login");
  }

  const profile = await getAccessProfile(user.id);
  
  if (!hasPermission(profile, permission)) {
    redirect("/forbidden"); // Rota genérica de acesso negado semanticamente correta
  }
}
