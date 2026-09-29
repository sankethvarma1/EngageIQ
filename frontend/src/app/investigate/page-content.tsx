'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { aiApi } from '@/lib/api';
import { formatCurrency, formatPercent, truncate } from '@/lib/utils';
import { InvestigateResponse, Evidence, ToolCall } from '@/types';

const SAMPLE_QUESTIONS = [
  'Why is engagement ENG001 high risk?',
  'What are the main drivers of risk for ENG005?',
  'What changed recently for ENG010?',
  'What evidence supports the recommendation for ENG003?',
  'Why is the margin deteriorating for ENG007?',
  'What is causing the SLA breaches for ENG012?',
];

export default function InvestigatePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const defaultEngagement = searchParams.get('engagement') || '';

  const [question, setQuestion] = useState(defaultEngagement ? `Why is engagement ${defaultEngagement} high risk?` : '');
  const [engagementId, setEngagementId] = useState(defaultEngagement);
  const [response, setResponse] = useState<InvestigateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await aiApi.investigate({
        question: question.trim(),
        engagement_id: engagementId || undefined,
      });
      setResponse(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to investigate');
    } finally {
      setLoading(false);
    }
  };

  const handleSampleClick = (q: string) => {
    setQuestion(q);
    const match = q.match(/ENG\d+/);
    if (match) setEngagementId(match[0]);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">AI Investigation</h1>
        <p className="text-slate-500 mt-1">Ask questions about engagement risks, drivers, and evidence</p>
      </div>

      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Engagement ID (optional)</label>
              <input
                type="text"
                value={engagementId}
                onChange={(e) => setEngagementId(e.target.value.toUpperCase())}
                placeholder="ENG001"
                className="w-full max-w-xs px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Question</label>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={3}
                placeholder="e.g., Why is engagement ENG001 high risk? What are the main drivers? What changed recently?"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="btn-primary disabled:opacity-50"
            >
              {loading ? 'Investigating...' : 'Investigate'}
            </button>
          </form>

          <div className="mt-4">
            <p className="text-sm text-slate-500 mb-2">Sample questions:</p>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSampleClick(q)}
                  className="text-xs text-primary-600 hover:underline px-2 py-1 bg-primary-50 rounded"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="card p-4 bg-red-50 border-red-200 text-red-700">{error}</div>
      )}

      {response && (
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Investigation Result</h2>
              {response.answer.startsWith('[Mock Response]') && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1 mt-2">
                  Mock mode — no NEMOTRON_API_KEY configured. Tool results and evidence below are real;
                  the narrative above is a placeholder, not live Nemotron output.
                </p>
              )}
            </div>
            <div className="card-body prose prose-slate max-w-none">
              {response.answer.split('\n').map((paragraph, i) => (
                <p key={i} className="mb-3 whitespace-pre-wrap">{paragraph}</p>
              ))}
            </div>
          </div>

          {response.tool_calls.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-slate-900">Tools Used</h3>
              </div>
              <div className="card-body">
                <div className="space-y-2">
                  {response.tool_calls.map((call: ToolCall, i: number) => (
                    <details key={i} className="group">
                      <summary className="flex items-center gap-2 cursor-pointer text-sm font-medium text-slate-700">
                        <span className="badge bg-primary-100 text-primary-700">{call.tool}</span>
                        <code className="text-xs bg-slate-100 px-2 py-0.5 rounded">{JSON.stringify(call.args)}</code>
                        {call.error && <span className="badge bg-red-100 text-red-700">Error</span>}
                      </summary>
                      <div className="mt-2 ml-6 text-sm text-slate-600 border-l-2 border-slate-200 pl-3">
                        <pre className="whitespace-pre-wrap text-xs">{JSON.stringify(call.result, null, 2)}</pre>
                      </div>
                    </details>
                  ))}
                </div>
              </div>
            </div>
          )}

          {response.evidence.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-slate-900">Supporting Evidence</h3>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  {response.evidence.map((ev: Evidence, i: number) => (
                    <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="font-medium text-slate-900">{ev.title}</h4>
                          <p className="text-sm text-slate-500">{ev.section}</p>
                        </div>
                        <span className="badge bg-slate-100 text-slate-700">{ev.doc_id}</span>
                      </div>
                      <p className="text-sm text-slate-600 mt-2">{truncate(ev.content, 300)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}