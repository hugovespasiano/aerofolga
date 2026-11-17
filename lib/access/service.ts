import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import type { Profile } from "@/types/access";

/**
 * AccessService
 * 
 * Única porta de entrada autorizada para obtenção do Profile de autorização.
 * Nenhum Middleware, Helper, Componente ou Server Action deve consultar 
 * diretamente a infraestrutura de autenticação no que diz respeito ao controle de acesso.
 * 
 * Isso garante que a Foundation não fique acoplada ao Supabase.
 */
export async function getAccessProfile(userId: string): Promise<Profile | null> {
  const cookieStore = await cookies();
  
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // Ignore if called from a Server Component.
          }
        },
      },
    }
  );

  const { data, error } = await supabase
    .from("profiles")
    .select("id, display_name, role, plan, status")
    .eq("id", userId)
    .single();

  if (error || !data) {
    return null;
  }

  // Fetch role-based permissions
  const { data: rolePerms } = await supabase
    .from("role_permissions")
    .select("permissions(name)")
    .eq("role", data.role);

  const permissions =
    rolePerms
      ?.map((rp: { permissions: { name: string } | { name: string }[] | null }) => {
        // Supabase join types can sometimes be arrays or single objects based on foreign keys.
        // Assuming role_permissions -> permissions is many-to-one, it's an object or null.
        if (!rp.permissions) return null;
        if (Array.isArray(rp.permissions)) return rp.permissions[0]?.name;
        return (rp.permissions as { name: string }).name;
      })
      .filter(Boolean) || [];

  // Type assertion ensures the DB matches our exact typescript definitions.
  return {
    ...data,
    permissions,
  } as Profile;
}
