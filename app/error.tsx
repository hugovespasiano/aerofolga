"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ui/error-state";
import { AppLayout } from "@/components/layout/app-layout";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global Error Boundary caught:", error);
  }, [error]);

  return (
    <AppLayout>
      <div className="flex h-full w-full items-center justify-center p-6">
        <ErrorState
          title="Ocorreu um erro inesperado"
          description={error.message || "Não foi possível carregar esta página. Nossa equipe já foi notificada."}
          actionLabel="Tentar novamente"
          onAction={() => reset()}
        />
      </div>
    </AppLayout>
  );
}
