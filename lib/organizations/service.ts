import { cookies } from "next/headers";
import { createClient } from "@/lib/supabase/server";
import { generateSlug } from "./helpers";
import type {
  Organization,
  UserOrganization,
  CreateOrganizationInput,
  OrgRole,
  OrgMemberStatus,
} from "@/types/organizations";

export const CURRENT_ORG_COOKIE = "foundation_current_org";

interface OrgMemberQueryResult {
  role: OrgRole;
  status: OrgMemberStatus;
  organization: Organization | Organization[] | null;
}

/**
 * Retorna todas as organizações às quais o usuário logado pertence ativamente.
 */
export async function getUserOrganizations(): Promise<UserOrganization[]> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return [];
  }

  const { data, error } = await supabase
    .from("organization_members")
    .select("role, status, organization:organizations(*)")
    .eq("user_id", user.id)
    .eq("status", "active");

  if (error || !data) {
    return [];
  }

  const rows = data as unknown as OrgMemberQueryResult[];

  return rows
    .map((item) => {
      const org = Array.isArray(item.organization)
        ? item.organization[0]
        : item.organization;
      if (!org) return null;
      return {
        role: item.role,
        status: item.status,
        organization: org,
      };
    })
    .filter(Boolean) as UserOrganization[];
}

/**
 * Retorna o ID da organização ativa no contexto da sessão.
 * Prevenção de IDOR: Valida estritamente se o usuário logado realmente
 * é membro ativo da organização informada no cookie antes de aceitá-la.
 */
export async function getActiveOrganizationId(): Promise<string | null> {
  const cookieStore = await cookies();
  const requestedOrgId = cookieStore.get(CURRENT_ORG_COOKIE)?.value;
  const userOrgs = await getUserOrganizations();

  if (userOrgs.length === 0) {
    return null;
  }

  if (requestedOrgId) {
    const isMember = userOrgs.some(
      (item) => item.organization.id === requestedOrgId
    );
    if (isMember) {
      return requestedOrgId;
    }
  }

  // Fallback: se o cookie não existir ou for inválido, usa a primeira organização
  return userOrgs[0].organization.id;
}

/**
 * Define a organização ativa para a sessão atual.
 */
export async function setActiveOrganizationId(orgId: string): Promise<boolean> {
  const cookieStore = await cookies();
  const userOrgs = await getUserOrganizations();

  const isMember = userOrgs.some((item) => item.organization.id === orgId);
  if (!isMember) {
    return false;
  }

  try {
    cookieStore.set(CURRENT_ORG_COOKIE, orgId, {
      path: "/",
      httpOnly: true,
      sameSite: "lax",
    });
    return true;
  } catch {
    // Silencia se chamado em contexto somente-leitura de Server Component
    return false;
  }
}

/**
 * Cria uma nova organização no sistema.
 * O criador autenticado é associado atômica e automaticamente como 'owner'
 * através da trigger on_organization_created no PostgreSQL.
 */
export async function createOrganization(
  input: CreateOrganizationInput
): Promise<{ success: boolean; organization?: Organization; error?: string }> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { success: false, error: "Usuário não autenticado." };
  }

  const slug = input.slug || generateSlug(input.name);

  const { data, error } = await supabase
    .from("organizations")
    .insert({
      name: input.name,
      slug,
    })
    .select()
    .single();

  if (error || !data) {
    return { success: false, error: error?.message || "Erro ao criar organização." };
  }

  const organization = data as Organization;

  // Atualiza a organização ativa para a recém-criada
  await setActiveOrganizationId(organization.id);

  return { success: true, organization };
}
