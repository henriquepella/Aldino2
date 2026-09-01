"use client";

import { SectionRoute } from "@/components/section-route";

export default function GwrPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <SectionRoute
      params={params}
      stepKey="gwr"
      title="GWR / GWM"
      description="Regressão e estatísticas ponderadas geograficamente: coeficientes locais e R² local."
    />
  );
}
