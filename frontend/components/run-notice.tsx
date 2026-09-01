"use client";

import { AlertTriangle, Loader2 } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

/** Aviso padrão para seções que dependem de uma execução concluída. */
export function RunNotice({
  title,
  children,
  runHref,
  spin,
}: {
  title: string;
  children?: ReactNode;
  runHref?: string;
  spin?: boolean;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-3 p-6">
        <div className="flex items-center gap-2 text-foreground">
          {spin ? (
            <Loader2 className="size-5 animate-spin text-muted-foreground" aria-hidden />
          ) : (
            <AlertTriangle className="size-5 text-muted-foreground" aria-hidden />
          )}
          <span className="font-semibold">{title}</span>
        </div>
        {children ? <p className="text-sm text-muted-foreground">{children}</p> : null}
        {runHref ? (
          <Button asChild variant="outline" size="sm">
            <Link href={runHref}>Ir para a execução</Link>
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
