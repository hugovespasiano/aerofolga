import Link from "next/link";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { AppLayout } from "@/components/layout/app-layout";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <AppLayout>
      <div className="flex h-full w-full items-center justify-center p-6">
        <EmptyState
          title="Página não encontrada"
          description="A página que você está procurando não existe ou foi movida."
          icon={FileQuestion}
          action={
            <Button asChild>
              <Link href="/">Voltar ao início</Link>
            </Button>
          }
        />
      </div>
    </AppLayout>
  );
}
