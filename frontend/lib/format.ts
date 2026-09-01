const NF = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 3 });
const NF0 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

export function fmtNum(v: number | null | undefined, digits = 3): string {
  if (v == null || !Number.isFinite(v)) return "—";
  if (v !== 0 && (Math.abs(v) >= 1e6 || Math.abs(v) < 1e-4)) {
    return v.toExponential(digits).replace(".", ",");
  }
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: digits }).format(v);
}

export function fmtInt(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return NF0.format(v);
}

export function fmtPct(v: number | null | undefined, digits = 1): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: digits }).format(v)}%`;
}

export function fmtPValue(p: number | null | undefined): string {
  if (p == null || !Number.isFinite(p)) return "—";
  if (p < 0.001) return "< 0,001";
  return fmtNum(p, 3);
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export function fmtBytes(n: number): string {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), u.length - 1);
  return `${NF.format(n / 1024 ** i)} ${u[i]}`;
}

export { NF };
