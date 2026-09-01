"use client";

import { SectionRoute } from "@/components/section-route";

export default function KrigingPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <SectionRoute
      params={params}
      stepKey="kriging"
      title="Krigagem Ordinária"
      description="Ajuste do variograma, predição por krigagem ordinária e mapas de estimativa e variância."
    />
  );
}
