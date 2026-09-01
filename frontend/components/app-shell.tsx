"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { UserMenu } from "@/components/user-menu";

interface AppShellProps {
  children: ReactNode;
  /** Slot opcional para a sidebar (páginas de projeto). */
  sidebar?: ReactNode;
  /** Título/breadcrumb exibido à esquerda na topbar (nome do projeto, etc.). */
  title?: ReactNode;
  /** Conteúdo extra à direita da topbar, antes do tema e do menu do usuário. */
  right?: ReactNode;
}

/**
 * Casca da aplicação: topbar fixa (h-14, borda inferior) com marca textual,
 * título/breadcrumb, alternância de tema e menu do usuário. Sidebar opcional.
 */
export function AppShell({ children, sidebar, title, right }: AppShellProps) {
  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground">
      <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <Link
          href="/projects"
          className="flex items-center gap-2 font-semibold tracking-tight"
        >
          <span className="grid h-7 w-7 place-items-center rounded-md bg-primary text-xs font-bold text-primary-foreground">
            AG
          </span>
          <span className="hidden sm:inline">Análise Geoestatística</span>
        </Link>

        {title ? (
          <>
            <span className="text-muted-foreground">/</span>
            <div className="min-w-0 truncate text-sm font-medium">{title}</div>
          </>
        ) : null}

        <div className="ml-auto flex items-center gap-1">
          {right}
          <ThemeToggle />
          <UserMenu />
        </div>
      </header>

      <div className="flex flex-1">
        {sidebar ? (
          <aside className="hidden w-64 shrink-0 border-r bg-card/40 md:block">
            {sidebar}
          </aside>
        ) : null}
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
