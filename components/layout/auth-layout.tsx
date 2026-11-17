import { ThemeSwitcher } from "@/components/theme-switcher";
import Link from "next/link";
import { Home } from "lucide-react";

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-muted/40">
      <header className="absolute top-0 w-full flex items-center justify-between p-4 md:p-6">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <Home className="h-5 w-5" />
          Foundation
        </Link>
        <ThemeSwitcher />
      </header>
      
      <main className="flex flex-1 items-center justify-center p-4">
        {children}
      </main>
    </div>
  );
}
