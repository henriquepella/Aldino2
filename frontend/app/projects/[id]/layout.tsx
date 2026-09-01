"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { use, useMemo, useState, type ReactNode } from "react";
import { AppShell } from "@/components/app-shell";
import { NavLink } from "@/components/nav-link";
import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useDataset, useProject, useRuns } from "@/lib/hooks";
import { SECTIONS, WIZARD_STEPS, sectionHref, wizardHref } from "@/lib/nav";
import type { ProjectOut } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ArrowLeft, Check, PanelLeft } from "lucide-react";

type StepState = "done" | "current" | "pending";

export default function ProjectLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return (
    <RequireAuth>
      <ProjectShell id={id}>{children}</ProjectShell>
    </RequireAuth>
  );
}

function ProjectShell({ id, children }: { id: string; children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const projectQ = useProject(id);
  const runsQ = useRuns(id);
  const datasetId = runsQ.data?.[0]?.dataset_id;
  const datasetQ = useDataset(datasetId);

  const project = projectQ.data;
  const ds = datasetQ.data;

  const wizard = useMemo(() => {
    const hasDataset = (project?.dataset_count ?? 0) > 0;
    const hasRun = (project?.run_count ?? 0) > 0;
    // Um run só existe se colunas foram confirmadas e a base validada,
    // por isso hasRun implica configure/diagnostics concluídos.
    const done: Record<string, boolean> = {
      upload: hasDataset,
      configure: hasRun || !!ds?.config,
      diagnostics: hasRun || !!ds?.validation,
      run: hasRun,
    };
    const current = WIZARD_STEPS.find((s) => !done[s.slug])?.slug;
    const state: Record<string, StepState> = {};
    for (const s of WIZARD_STEPS) {
      state[s.slug] = done[s.slug] ? "done" : s.slug === current ? "current" : "pending";
    }
    return state;
  }, [project?.dataset_count, project?.run_count, ds?.config, ds?.validation]);

  const title = projectQ.isLoading
    ? "Carregando projeto…"
    : projectQ.isError
      ? "Projeto indisponível"
      : (project?.name ?? "Projeto");

  const sidebar = (
    <SidebarBody
      projectId={id}
      project={project}
      loading={projectQ.isLoading}
      error={projectQ.isError}
      wizard={wizard}
    />
  );

  return (
    <>
      <AppShell
        title={title}
        sidebar={sidebar}
        right={
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Abrir navegação"
            onClick={() => setMobileOpen(true)}
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
        }
      >
        <div className="mx-auto max-w-6xl p-6">{children}</div>
      </AppShell>

      <Dialog open={mobileOpen} onOpenChange={setMobileOpen}>
        <DialogContent
          className={cn(
            "left-0 top-0 h-svh w-[17rem] max-w-[17rem] translate-x-0 translate-y-0 gap-0 overflow-y-auto rounded-none border-r p-0",
            "data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:rounded-none",
          )}
        >
          <DialogTitle className="sr-only">Navegação do projeto</DialogTitle>
          <SidebarBody
            projectId={id}
            project={project}
            loading={projectQ.isLoading}
            error={projectQ.isError}
            wizard={wizard}
            onNavigate={() => setMobileOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </>
  );
}

function SidebarBody({
  projectId,
  project,
  loading,
  error,
  wizard,
  onNavigate,
}: {
  projectId: string;
  project: ProjectOut | undefined;
  loading: boolean;
  error: boolean;
  wizard: Record<string, StepState>;
  onNavigate?: () => void;
}) {
  const pathname = usePathname() || "";

  return (
    <div className="flex h-full flex-col md:sticky md:top-14 md:h-[calc(100svh-3.5rem)]">
      {/* Cabeçalho: volta para a lista de projetos + nome do projeto */}
      <div className="p-3">
        <Link
          href="/projects"
          onClick={onNavigate}
          className="inline-flex items-center gap-1.5 rounded-md px-1.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Projetos
        </Link>
        <div className="mt-1.5 px-1.5">
          {loading ? (
            <>
              <Skeleton className="h-4 w-40" />
              <Skeleton className="mt-1.5 h-3 w-24" />
            </>
          ) : error ? (
            <p className="text-sm text-destructive">Falha ao carregar o projeto.</p>
          ) : (
            <>
              <div className="truncate text-sm font-semibold text-foreground">
                {project?.name ?? "Projeto"}
              </div>
              {project?.client ? (
                <div className="truncate text-xs text-muted-foreground">{project.client}</div>
              ) : null}
            </>
          )}
        </div>
      </div>

      <Separator />

      <div className="min-h-0 flex-1 overflow-y-auto py-3">
        {/* Assistente */}
        <div className="px-3">
          <div className="px-2.5 pb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Assistente
          </div>
          <ol className="space-y-0.5">
            {WIZARD_STEPS.map((step, i) => {
              const href = wizardHref(projectId, step.slug);
              const active = pathname === href || pathname.startsWith(`${href}/`);
              const state = wizard[step.slug] ?? "pending";
              return (
                <li key={step.slug}>
                  <Link
                    href={href}
                    onClick={onNavigate}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
                      active
                        ? "bg-accent font-medium text-accent-foreground"
                        : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                    )}
                  >
                    <span
                      className={cn(
                        "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[11px] font-semibold tabular",
                        state === "done" && "border-transparent bg-success/15 text-success",
                        state === "current" && "border-transparent bg-primary/15 text-primary",
                        state === "pending" && "border-border text-muted-foreground",
                      )}
                    >
                      {state === "done" ? <Check className="h-3 w-3" /> : i + 1}
                    </span>
                    <span className="truncate">{step.label}</span>
                  </Link>
                </li>
              );
            })}
          </ol>
        </div>

        <Separator className="my-3" />

        {/* Análise */}
        <div className="px-3">
          <div className="px-2.5 pb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Análise
          </div>
          <nav className="space-y-0.5">
            {SECTIONS.map((section) => {
              const Icon = section.icon;
              return (
                <NavLink
                  key={section.slug}
                  href={sectionHref(projectId, section.slug)}
                  exact={section.slug === "dashboard"}
                  onClick={onNavigate}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{section.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}
