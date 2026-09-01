"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  Database,
  Download,
  FileSpreadsheet,
  FolderPlus,
  MoreVertical,
  PlayCircle,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  useCreateProject,
  useDeleteProject,
  useDuplicateProject,
  useProjects,
  useRun,
} from "@/lib/hooks";
import type { ProjectOut, RunStatus } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { AppShell } from "@/components/app-shell";
import { EmptyState } from "@/components/empty-state";
import { RequireAuth } from "@/components/require-auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

const STATUS_META: Record<
  RunStatus,
  { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }
> = {
  pending: { label: "Na fila", variant: "secondary" },
  running: { label: "Em execução", variant: "default" },
  done: { label: "Concluída", variant: "success" },
  failed: { label: "Falhou", variant: "destructive" },
  cancelled: { label: "Cancelada", variant: "warning" },
};

function LatestRunBadge({ runId }: { runId?: string | null }) {
  const { data, isLoading, isError } = useRun(runId ?? undefined);
  if (!runId) return <Badge variant="outline">Sem execução</Badge>;
  if (isLoading) return <Skeleton className="h-5 w-24" />;
  if (isError || !data) return <Badge variant="outline">Execução indisponível</Badge>;
  const meta = STATUS_META[data.status] ?? STATUS_META.pending;
  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}

function NewProjectDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const router = useRouter();
  const create = useCreateProject();
  const [name, setName] = useState("");
  const [client, setClient] = useState("");
  const [technicalLead, setTechnicalLead] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const project = await create.mutateAsync({
        name: name.trim(),
        client: client.trim(),
        technical_lead: technicalLead.trim(),
      });
      toast.success("Projeto criado.");
      onOpenChange(false);
      setName("");
      setClient("");
      setTechnicalLead("");
      router.push(`/projects/${project.id}/upload`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Não foi possível criar o projeto.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo projeto</DialogTitle>
          <DialogDescription>
            Defina a identificação do estudo. Você poderá ajustar os demais dados nas configurações.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="np-name">Nome do projeto</Label>
            <Input
              id="np-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex.: Levantamento geoquímico — Talhão 3"
              autoFocus
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="np-client">Cliente</Label>
            <Input
              id="np-client"
              value={client}
              onChange={(e) => setClient(e.target.value)}
              placeholder="Ex.: Fazenda Santa Rita"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="np-lead">Responsável técnico</Label>
            <Input
              id="np-lead"
              value={technicalLead}
              onChange={(e) => setTechnicalLead(e.target.value)}
              placeholder="Ex.: Eng. Agr. Maria Souza"
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={create.isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={create.isPending || !name.trim()}>
              {create.isPending ? "Criando…" : "Criar e enviar planilha"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ProjectCard({
  project,
  onDelete,
}: {
  project: ProjectOut;
  onDelete: (p: ProjectOut) => void;
}) {
  const router = useRouter();
  const duplicate = useDuplicateProject();

  return (
    <Card
      role="link"
      tabIndex={0}
      onClick={() => router.push(`/projects/${project.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter") router.push(`/projects/${project.id}`);
      }}
      className="group cursor-pointer transition-colors hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <CardHeader className="flex-row items-start justify-between gap-2 space-y-0">
        <div className="min-w-0">
          <CardTitle className="truncate">{project.name}</CardTitle>
          <p className="mt-1 truncate text-sm text-muted-foreground">
            {project.client || "Cliente não informado"}
          </p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0"
              aria-label="Ações do projeto"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
            <DropdownMenuItem onSelect={() => router.push(`/projects/${project.id}`)}>
              Abrir
            </DropdownMenuItem>
            <DropdownMenuItem
              onSelect={async () => {
                try {
                  await duplicate.mutateAsync(project.id);
                  toast.success("Projeto duplicado.");
                } catch (err) {
                  toast.error(
                    err instanceof Error ? err.message : "Falha ao duplicar o projeto.",
                  );
                }
              }}
            >
              Duplicar
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onSelect={() => onDelete(project)}
            >
              Excluir
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground tabular-nums">
          <span className="inline-flex items-center gap-1.5">
            <Database className="h-3.5 w-3.5" />
            {project.dataset_count} {project.dataset_count === 1 ? "base" : "bases"}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <PlayCircle className="h-3.5 w-3.5" />
            {project.run_count} {project.run_count === 1 ? "execução" : "execuções"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <LatestRunBadge runId={project.latest_run_id} />
          <span className="text-xs text-muted-foreground">{fmtDate(project.updated_at)}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function ProjectsView() {
  const { data: projects, isLoading, isError, error } = useProjects();
  const del = useDeleteProject();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<ProjectOut | null>(null);

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Análise Geoestatística</h1>
          <p className="mt-2 max-w-2xl text-muted-foreground">
            Da planilha ao relatório técnico: estatística descritiva, ESDA, índice de Moran, IDW,
            krigagem ordinária, krigagem com deriva externa, GWR e co-krigagem — executados
            automaticamente e reunidos em um dashboard e um PDF.
          </p>
        </div>
        <Button size="lg" className="shrink-0" onClick={() => setDialogOpen(true)}>
          <FolderPlus className="h-4 w-4" />
          Novo Projeto
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <a
          href={api.templateUrl()}
          className="inline-flex items-center gap-1.5 text-sm text-primary underline-offset-4 hover:underline"
        >
          <Download className="h-4 w-4" />
          Baixar modelo Excel
        </a>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-44 w-full rounded-lg" />
          ))}
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          Não foi possível carregar os projetos
          {error instanceof Error ? `: ${error.message}` : "."}
        </div>
      ) : !projects || projects.length === 0 ? (
        <EmptyState
          icon={<FileSpreadsheet />}
          title="Crie seu primeiro projeto"
          description="Um projeto reúne a planilha de amostras, as configurações da análise e todas as execuções."
          action={
            <Button size="lg" onClick={() => setDialogOpen(true)}>
              <FolderPlus className="h-4 w-4" />
              Novo Projeto
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onDelete={setPendingDelete} />
          ))}
        </div>
      )}

      <NewProjectDialog open={dialogOpen} onOpenChange={setDialogOpen} />

      <Dialog
        open={!!pendingDelete}
        onOpenChange={(v) => {
          if (!v) setPendingDelete(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Excluir projeto</DialogTitle>
            <DialogDescription>
              O projeto <span className="font-medium text-foreground">{pendingDelete?.name}</span> e
              todas as suas bases, execuções e resultados serão removidos permanentemente. Esta ação
              não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setPendingDelete(null)}
              disabled={del.isPending}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={del.isPending}
              onClick={async () => {
                if (!pendingDelete) return;
                try {
                  await del.mutateAsync(pendingDelete.id);
                  toast.success("Projeto excluído.");
                  setPendingDelete(null);
                } catch (err) {
                  toast.error(
                    err instanceof Error ? err.message : "Falha ao excluir o projeto.",
                  );
                }
              }}
            >
              {del.isPending ? "Excluindo…" : "Excluir"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function ProjectsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <ProjectsView />
      </AppShell>
    </RequireAuth>
  );
}
