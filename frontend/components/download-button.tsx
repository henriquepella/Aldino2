"use client";

import { Download, Loader2 } from "lucide-react";
import * as React from "react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { downloadFile } from "@/lib/api";

type DownloadButtonProps = Omit<ButtonProps, "onClick"> & {
  url: string;
  filename: string;
  /** Oculta o ícone padrão de download. */
  hideIcon?: boolean;
};

/** Botão que faz download autenticado (Bearer) de um arquivo do backend. */
export function DownloadButton({
  url,
  filename,
  hideIcon,
  children,
  disabled,
  ...props
}: DownloadButtonProps) {
  const [busy, setBusy] = React.useState(false);

  async function handle() {
    setBusy(true);
    try {
      await downloadFile(url, filename);
    } catch {
      /* erro silencioso — o backend pode recusar downloads sem sessão */
    } finally {
      setBusy(false);
    }
  }

  return (
    <Button {...props} disabled={disabled || busy} onClick={handle}>
      {busy ? <Loader2 className="animate-spin" /> : hideIcon ? null : <Download />}
      {children}
    </Button>
  );
}
