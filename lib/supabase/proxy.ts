import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { hasEnvVars } from "../utils";
import { hasAccess } from "@/lib/access/helpers";
import type { Profile } from "@/types/access";

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  // If the env vars are not set, skip proxy check.
  if (!hasEnvVars) {
    return supabaseResponse;
  }

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          supabaseResponse = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  const { data } = await supabase.auth.getClaims();
  const user = data?.claims;

  const isProtected = request.nextUrl.pathname.startsWith("/protected");

  if (isProtected) {
    // 1. Autenticação
    if (!user) {
      const url = request.nextUrl.clone();
      url.pathname = "/auth/login";
      return NextResponse.redirect(url);
    }

    // 2. Ler Profile via cliente Supabase do próprio request (Edge-safe)
    const { data: profileData } = await supabase
      .from("profiles")
      .select("id, display_name, role, plan, status")
      .eq("id", user.sub)
      .maybeSingle();

    const profile = profileData ? (profileData as Profile) : null;

    // 3. Verificar regras utilizando hasAccess()
    // A rota "/protected" genérica exige apenas que a conta esteja ativa.
    if (!hasAccess(profile, { requireActive: true })) {
      const url = request.nextUrl.clone();
      url.pathname = "/auth/suspended";
      return NextResponse.redirect(url);
    }
  }

  return supabaseResponse;
}
