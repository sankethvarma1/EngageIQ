import { engagementApi } from '@/lib/api';
import { Engagement, EngagementKPIs, RiskFactors } from '@/types';

export type EnrichedEngagement = Engagement & { kpis?: EngagementKPIs; risk?: RiskFactors };

// Keep SQLite-backed KPI and model requests at a manageable concurrency.
export async function enrichEngagements(engagements: Engagement[]): Promise<EnrichedEngagement[]> {
  const enriched: EnrichedEngagement[] = [];
  for (let offset = 0; offset < engagements.length; offset += 5) {
    const batch = await Promise.all(engagements.slice(offset, offset + 5).map(async (eng) => {
      const [kpisRes, riskRes] = await Promise.all([
        engagementApi.getKPIs(eng.id).catch(() => null),
        engagementApi.getRisk(eng.id).catch(() => null),
      ]);
      return { ...eng, kpis: kpisRes?.data, risk: riskRes?.data };
    }));
    enriched.push(...batch);
  }
  return enriched;
}
