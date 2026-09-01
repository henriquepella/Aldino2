"use client";

import { SectionRoute } from "@/components/section-route";

export default function IdwPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <SectionRoute
      params={params}
      stepKey="idw"
      title="IDW — Inverse Distance Weighting"
      description="Interpolação determinística por ponderação do inverso da distância e validação cruzada."
    />
  );
}
