"use client";

import { Download } from "lucide-react";
import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { downloadFile } from "@/lib/api";
import type { ArtifactOut } from "@/lib/types";
import { cn } from "@/lib/utils";

function collectVariants(fig: ArtifactOut): { label: string; url: string }[] {
  const out: { label: string; url: string }[] = [];
  const seen = new Set<string>();
  const variants = fig.data?.variants ?? {};
  for (const [fmt, url] of Object.entries(variants)) {
    if (!url || seen.has(url)) continue;
    seen.add(url);
    out.push({ label: fmt.toUpperCase(), url });
  }
  if (fig.url && !seen.has(fig.url)) {
    const ext = fig.url.split("?")[0].split(".").pop();
    out.push({ label: ext ? ext.toUpperCase() : "Original", url: fig.url });
  }
  return out;
}

export function FigureViewer({ fig, className }: { fig: ArtifactOut; className?: string }) {
  const [busy, setBusy] = React.useState<string | null>(null);
  const src = fig.url;
  const title = fig.title || fig.name;
  const caption = fig.caption || "";
  const variants = collectVariants(fig);

  async function download(label: string, url: string) {
    setBusy(label);
    try {
      const ext = (url.split("?")[0].split(".").pop() || label).toLowerCase();
      const base = (fig.name || title || "figura").replace(/[^\w.-]+/g, "_");
      await downloadFile(url, base.includes(".") ? base : `${base}.${ext}`);
    } catch {
      /* erro silencioso */
    } finally {
      setBusy(null);
    }
  }

  return (
    <Dialog>
      <figure className={cn("flex flex-col overflow-hidden rounded-lg border bg-card", className)}>
        <DialogTrigger asChild>
          <button
            type="button"
            className="group relative block w-full cursor-zoom-in bg-muted/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={src}
              alt={title}
              loading="lazy"
              className="mx-auto max-h-[320px] w-full object-contain transition-transform duration-200 group-hover:scale-[1.01]"
            />
          </button>
        </DialogTrigger>
        {(title || caption) && (
          <figcaption className="space-y-1 border-t p-3">
            {title ? <p className="text-sm font-medium text-foreground">{title}</p> : null}
            {caption ? <p className="text-xs text-muted-foreground">{caption}</p> : null}
          </figcaption>
        )}
      </figure>

      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="max-h-[70vh] overflow-auto rounded-md bg-muted/30 p-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={src} alt={title} className="mx-auto h-auto w-full object-contain" />
        </div>
        {caption ? <p className="text-xs text-muted-foreground">{caption}</p> : null}
        {variants.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {variants.map((v) => (
              <Button
                key={v.label + v.url}
                variant="outline"
                size="sm"
                disabled={busy !== null}
                onClick={() => download(v.label, v.url)}
              >
                <Download />
                {busy === v.label ? "Baixando…" : v.label}
              </Button>
            ))}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
