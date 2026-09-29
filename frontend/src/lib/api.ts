import axios from 'axios';
import { Engagement, EngagementList, EngagementKPIs, RiskFactors, Anomaly, SHAPExplanation, InvestigateRequest, InvestigateResponse, ModelMetrics } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const engagementApi = {
  list: (params?: { skip?: number; limit?: number; status?: string; client_id?: string }) =>
    api.get<EngagementList>('/engagements', { params }),

  get: (id: string) =>
    api.get<Engagement>(`/engagements/${id}`),

  getKPIs: (id: string) =>
    api.get<EngagementKPIs>(`/engagements/${id}/kpis`),

  getRisk: (id: string) =>
    api.get<RiskFactors>(`/engagements/${id}/risk`),

  getAnomalies: (id: string) =>
    api.get<Anomaly[]>(`/engagements/${id}/anomalies`),

  getExplanation: (id: string) =>
    api.get<SHAPExplanation>(`/engagements/${id}/explanation`),
};

export const aiApi = {
  // Free-tier backends sleep and cold-start (plus first-use embedding
  // download), so investigation gets a longer timeout than the default.
  investigate: (data: InvestigateRequest) =>
    api.post<InvestigateResponse>('/ai/investigate', data, { timeout: 120000 }),
};

export const modelApi = {
  getMetrics: () =>
    api.get<ModelMetrics>('/engagements/model/metrics'),

  retrain: () =>
    api.post<ModelMetrics>('/engagements/model/retrain'),
};

export default api;