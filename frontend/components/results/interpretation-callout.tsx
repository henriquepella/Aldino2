import { Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";

export function InterpretationCallout({
  text,
  className,
}: {
  text?: string | null;
  className?: string;
}) {
  const value = text?.trim();
  if (!value) return null;
  return (
    <div
      className={cn(
        "flex gap-3 rounded-md border-l-4 border-primary bg-accent/40 p-4 text-sm leading-relaxed text-foreground",
        className,
      )}
    >
      <Lightbulb className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
      <div className="space-y-2 whitespace-pre-line">{value}</div>
    </div>
  );
}
