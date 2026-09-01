"use client";

import { use } from "react";
import { SectionRoute } from "../_components/section-route";

export default function MoranPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <SectionRoute
      projectId={id}
      stepKey="moran_scatter"
      title="Moran Scatter Plot"
      description="Diagrama de dispersão de Moran e autocorrelação espacial global."
    />
  );
}
