"use client";

import { Download } from "lucide-react";
import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { downloadFile } from "@/lib/api";
import { fmtNum } from "@/lib/format";
import type { ArtifactOut, TablePayload } from "@/lib/types";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 25;

function renderCell(value: string | number | null | undefined): React.ReactNode {
  if (value == null || value === "") return <span className="text-muted-foreground">—</span>;
  if (typeof value === "number") return fmtNum(value);
  return value;
}

export function DataTableView({ table, className }: { table: ArtifactOut; className?: string }) {
  const payload: TablePayload | undefined = table.data?.payload;
  const [page, setPage] = React.useState(0);
  const [busy, setBusy] = React.useState(false);

  const title = table.title || payload?.title || table.name;
  const caption = table.caption || payload?.caption || "";
  const columns = payload?.columns ?? [];
  const rows = payload?.rows ?? [];
  const highlight = new Set<number>(
    payload?.highlight_rows ?? table.data?.highlight_rows ?? [],
  );

  const paginated = rows.length > PAGE_SIZE;
  const pageCount = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const current = Math.min(page, pageCount - 1);
  const start = current * PAGE_SIZE;
  const visible = paginated ? rows.slice(start, start + PAGE_SIZE) : rows;

  async function handleDownload() {
    if (!table.url) return;
    setBusy(true);
    try {
      const base = (table.name || title || "tabela").replace(/[^\w.-]+/g, "_");
      await downloadFile(table.url, base.endsWith(".csv") ? base : `${base}.csv`);
    } catch {
      /* erro silencioso: o botão volta ao normal */
    } finally {
      setBusy(false);
    }
  }

  if (!payload || columns.length === 0) {
    return (
      <div className={cn("rounded-lg border bg-card p-4 text-sm text-muted-foreground", className)}>
        {title ? <p className="mb-1 font-medium text-foreground">{title}</p> : null}
        Sem dados tabulares para exibir.
      </div>
    );
  }

  return (
    <figure className={cn("rounded-lg border bg-card", className)}>
      <div className="flex flex-wrap items-start justify-between gap-2 border-b p-4">
        <div>
          {title ? <p className="text-sm font-semibold text-foreground">{title}</p> : null}
          <p className="text-xs text-muted-foreground">
            {rows.length} {rows.length === 1 ? "linha" : "linhas"}
          </p>
        </div>
        {table.url ? (
          <Button variant="outline" size="sm" onClick={handleDownload} disabled={busy}>
            <Download />
            CSV
          </Button>
        ) : null}
      </div>

      <div className="max-w-full overflow-x-auto scrollbar-thin">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((c) => (
                <TableHead key={c.key} className="whitespace-nowrap">
                  {c.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {visible.map((row, i) => {
              const absoluteIndex = (paginated ? start : 0) + i;
              const isHi = highlight.has(absoluteIndex);
              return (
                <TableRow
                  key={absoluteIndex}
                  className={cn(isHi && "bg-success/10 font-semibold hover:bg-success/15")}
                >
                  {columns.map((c) => (
                    <TableCell key={c.key} className="whitespace-nowrap">
                      {renderCell(row[c.key])}
                    </TableCell>
                  ))}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {paginated ? (
        <div className="flex items-center justify-between gap-2 border-t p-3 text-xs text-muted-foreground">
          <span>
            {start + 1}–{Math.min(start + PAGE_SIZE, rows.length)} de {rows.length}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={current === 0}
            >
              Anterior
            </Button>
            <span className="tabular">
              {current + 1} / {pageCount}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              disabled={current >= pageCount - 1}
            >
              Próxima
            </Button>
          </div>
        </div>
      ) : null}

      {caption ? (
        <figcaption className="border-t p-3 text-xs text-muted-foreground">{caption}</figcaption>
      ) : null}
    </figure>
  );
}
