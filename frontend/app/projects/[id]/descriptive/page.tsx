"use client";

import { use } from "react";
import { SectionRoute } from "../_components/section-route";

export default function DescriptivePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <SectionRoute
      projectId={id}
      stepKey="descriptive"
      title="Estatística Descritiva"
      description="Resumo estatístico das variáveis analisadas."
    />
  );
}
