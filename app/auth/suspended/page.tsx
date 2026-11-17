import { Button } from "@/components/ui/button";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default function SuspendedPage() {
  async function logout() {
    "use server";
    
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
              // The `setAll` method was called from a Server Component.
              // This can be ignored if you have middleware refreshing
              // user sessions.
            }
          },
        },
      }
    );

    await supabase.auth.signOut();
    redirect("/login");
  }

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center p-4 text-center">
      <div className="max-w-md space-y-6">
        <h1 className="text-4xl font-bold tracking-tight">Conta Suspensa</h1>
        <p className="text-muted-foreground">
          O acesso a esta conta foi suspenso e você não pode acessar os recursos do sistema neste momento.
        </p>
        <form action={logout}>
          <Button type="submit" variant="destructive">
            Fazer Logout
          </Button>
        </form>
      </div>
    </div>
  );
}
