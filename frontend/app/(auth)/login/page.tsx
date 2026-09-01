"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/lib/auth";

function errMessage(e: unknown): string {
  if (e instanceof Error && e.message) return e.message;
  return "Não foi possível entrar. Tente novamente.";
}

export default function LoginPage() {
  const router = useRouter();
  const { login, loginDemo } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<"form" | "demo" | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending("form");
    try {
      await login(email, password);
      router.push("/projects");
    } catch (err) {
      const msg = errMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setPending(null);
    }
  }

  async function onDemo() {
    setError(null);
    setPending("demo");
    try {
      await loginDemo();
      router.push("/projects");
    } catch (err) {
      const msg = errMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-base font-semibold text-foreground">Entrar</h1>
        <p className="text-sm text-muted-foreground">
          Acesse sua conta para continuar.
        </p>
      </div>

      <Button
        type="button"
        className="w-full"
        onClick={onDemo}
        disabled={pending !== null}
      >
        {pending === "demo" ? "Entrando…" : "Entrar com conta demo"}
      </Button>

      <div className="flex items-center gap-3">
        <Separator className="flex-1" />
        <span className="text-xs text-muted-foreground">ou</span>
        <Separator className="flex-1" />
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Senha</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && (
          <p className="rounded-md bg-destructive/15 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Button
          type="submit"
          variant="outline"
          className="w-full"
          disabled={pending !== null}
        >
          {pending === "form" ? "Entrando…" : "Entrar"}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Não tem conta?{" "}
        <Link href="/register" className="font-medium text-primary hover:underline">
          Criar conta
        </Link>
      </p>
    </div>
  );
}
