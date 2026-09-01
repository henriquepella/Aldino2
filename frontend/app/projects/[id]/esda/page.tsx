"use client";

import { use } from "react";
import { SectionRoute } from "../_components/section-route";

export default function EsdaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <SectionRoute
      projectId={id}
      stepKey="esda_univariate"
      title="ESDA Univariada"
      description="Análise exploratória espacial de cada variável."
    />
  );
}
