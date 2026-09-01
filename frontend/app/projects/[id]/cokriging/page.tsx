"use client";

import { SectionRoute } from "@/components/section-route";

export default function CokrigingPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <SectionRoute
      params={params}
      stepKey="cokriging"
      title="Co-Krigagem"
      description="Predição da variável primária usando a correlação com variáveis secundárias amostradas."
    />
  );
}
