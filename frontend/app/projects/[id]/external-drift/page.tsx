"use client";

import { SectionRoute } from "@/components/section-route";

export default function ExternalDriftPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <SectionRoute
      params={params}
      stepKey="external_drift"
      title="Krigagem com Deriva Externa"
      description="Krigagem que incorpora uma variável auxiliar como tendência (deriva externa)."
    />
  );
}
