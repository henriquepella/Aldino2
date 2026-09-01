"use client";

import type { CSSProperties } from "react";
import { useMemo } from "react";
import { CHART_COLORS } from "@/lib/utils";

/**
 * Confete discreto e efêmero para celebrar o fim de uma execução.
 * Autolimitado ao container relativo pai; respeita prefers-reduced-motion.
 */
export function ConfettiBurst({ count = 18 }: { count?: number }) {
  const pieces = useMemo(
    () =>
      Array.from({ length: count }).map((_, i) => {
        const style: CSSProperties = {
          left: `${Math.random() * 100}%`,
          background: CHART_COLORS[i % CHART_COLORS.length],
          transform: `rotate(${Math.round(Math.random() * 360)}deg)`,
          animation: `confetti-fall ${(2.2 + Math.random() * 1.6).toFixed(2)}s ${(
            Math.random() * 0.5
          ).toFixed(2)}s ease-in forwards`,
        };
        (style as Record<string, string>)["--drift"] =
          `${Math.round((Math.random() - 0.5) * 60)}px`;
        return style;
      }),
    [count],
  );

  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 overflow-hidden motion-reduce:hidden"
    >
      {pieces.map((style, i) => (
        <span key={i} className="absolute top-0 block h-2 w-1.5 rounded-[1px]" style={style} />
      ))}
      <style>{
        "@keyframes confetti-fall{0%{opacity:1;transform:translate(0,-12%) rotate(0)}100%{opacity:0;transform:translate(var(--drift,0),340px) rotate(400deg)}}"
      }</style>
    </div>
  );
}
