"use client";

import { SectionRoute } from "@/components/section-route";

export default function BivariatePage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <SectionRoute
      params={params}
      stepKey="esda_bivariate"
      title="ESDA Bivariada"
      description="Associação espacial entre pares de variáveis: Moran bivariado, LISA e mapas de clusters."
    />
  );
}
