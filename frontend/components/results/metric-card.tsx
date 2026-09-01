import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type MetricAccent = "default" | "primary" | "success" | "warning" | "destructive";

const ACCENT: Record<MetricAccent, string> = {
  default: "text-foreground",
  primary: "text-primary",
  success: "text-success",
  warning: "text-warning",
  destructive: "text-destructive",
};

export function MetricCard({
  label,
  value,
  hint,
  accent = "default",
  className,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  accent?: MetricAccent;
  className?: string;
}) {
  return (
    <Card className={cn("p-4", className)}>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-2xl font-semibold tabular leading-tight", ACCENT[accent])}>
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </Card>
  );
}
