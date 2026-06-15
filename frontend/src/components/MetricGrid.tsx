import React from "react";
import type { MetricCard } from "../types/dashboardPayload";

interface MetricGridProps {
  metricCards: MetricCard[];
}

export default function MetricGrid({ metricCards }: MetricGridProps) {
  return (
    <div className="metric-grid">
      {metricCards.map((card) => (
        <div className={`metric-card tone-${card.tone}`} key={card.id}>
          <div className="metric-label">{card.label}</div>
          <div className="metric-value">{card.value}</div>
          <div className="metric-sub">{card.sublabel}</div>
        </div>
      ))}
    </div>
  );
}