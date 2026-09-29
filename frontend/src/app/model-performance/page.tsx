'use client';

import { useEffect, useState } from 'react';
import { modelApi } from '@/lib/api';
import { ModelMetrics } from '@/types';
import { formatPercent } from '@/lib/utils';

export default function ModelPerformancePage() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retraining, setRetraining] = useState(false);

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const res = await modelApi.getMetrics();
        setMetrics(res.data);
      } catch (err) {
        setError('Model not trained yet. Click "Retrain Model" to train.');
      } finally {
        setLoading(false);
      }
    }
    fetchMetrics();
  }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    try {
      const res = await modelApi.retrain();
      setMetrics(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to retrain model');
    } finally {
      setRetraining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="space-y-4">
        <div className="card p-8 text-center text-red-600">{error}</div>
        <button onClick={handleRetrain} disabled={retraining} className="btn-primary mx-auto">
          {retraining ? 'Training...' : 'Retrain Model'}
        </button>
      </div>
    );
  }

  if (!metrics) {
    return <div className="card p-8 text-center text-slate-500">No model metrics available</div>;
  }

  const importanceData = Object.entries(metrics.feature_importance)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([feature, importance]) => ({
      name: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: importance,
    }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Model Performance</h1>
          <p className="text-slate-500 mt-1">Engagement Risk Model Metrics & Feature Importance</p>
        </div>
        {process.env.NEXT_PUBLIC_ALLOW_RETRAIN !== 'false' ? (
          <button onClick={handleRetrain} disabled={retraining} className="btn-primary">
            {retraining ? 'Training...' : 'Retrain Model'}
          </button>
        ) : (
          <p className="text-xs text-slate-500 max-w-xs">
            Retraining is disabled in the public demo to protect the bundled model.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card">
          <div className="card-body text-center">
            <p className="text-3xl font-bold text-primary-600">{metrics.auc.toFixed(3)}</p>
            <p className="text-sm text-slate-500">AUC-ROC</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body text-center">
            <p className="text-3xl font-bold text-green-600">{formatPercent(metrics.accuracy * 100)}</p>
            <p className="text-sm text-slate-500">Accuracy</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body text-center">
            <p className="text-3xl font-bold text-blue-600">{formatPercent(metrics.precision * 100)}</p>
            <p className="text-sm text-slate-500">Precision</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body text-center">
            <p className="text-3xl font-bold text-purple-600">{formatPercent(metrics.recall * 100)}</p>
            <p className="text-sm text-slate-500">Recall</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body text-center">
            <p className="text-3xl font-bold text-orange-600">{formatPercent(metrics.f1 * 100)}</p>
            <p className="text-sm text-slate-500">F1 Score</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-slate-900">Feature Importance (LightGBM)</h3>
          </div>
          <div className="card-body">
            <div className="space-y-2">
              {(() => {
                const maxImportance = Math.max(...importanceData.map((d) => d.value), 0) || 1;
                return importanceData.map((d) => (
                  <div key={d.name} className="flex items-center gap-2">
                    <div className="w-44 shrink-0 truncate text-xs text-slate-600" title={d.name}>
                      {d.name}
                    </div>
                    <div className="relative flex-1 h-5 bg-slate-100 rounded overflow-hidden">
                      <div
                        className="absolute left-0 top-1 bottom-1 rounded bg-primary-500"
                        style={{ width: `${(d.value / maxImportance) * 100}%` }}
                      />
                    </div>
                    <div className="w-16 shrink-0 text-right text-xs tabular-nums text-slate-700">
                      {d.value.toFixed(1)}
                    </div>
                  </div>
                ));
              })()}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-slate-900">Training Details</h3>
          </div>
          <div className="card-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-500">Training Samples</p>
                <p className="font-medium text-slate-900">{metrics.n_train}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Test Samples</p>
                <p className="font-medium text-slate-900">{metrics.n_test}</p>
              </div>
            </div>
            <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded">
              Small synthetic dataset (40 engagements; typically ~30 labeled samples). Metrics verify the training pipeline runs end-to-end — they are not production model validation.
            </p>

            <div className="border-t border-slate-200 pt-4">
              <h4 className="font-medium text-slate-900 mb-3">Model Configuration</h4>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-slate-500">Algorithm</dt>
                  <dd className="font-medium">LightGBM</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Estimators</dt>
                  <dd className="font-medium">200</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Max Depth</dt>
                  <dd className="font-medium">5</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Learning Rate</dt>
                  <dd className="font-medium">0.05</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Num Leaves</dt>
                  <dd className="font-medium">31</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Class Weight</dt>
                  <dd className="font-medium">Balanced</dd>
                </div>
              </dl>
            </div>

            <div className="border-t border-slate-200 pt-4">
              <h4 className="font-medium text-slate-900 mb-3">Risk Component Weights (Baseline)</h4>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-slate-500">Financial Risk</dt>
                  <dd className="font-medium">30%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Delivery Risk</dt>
                  <dd className="font-medium">25%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Operational Risk</dt>
                  <dd className="font-medium">20%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Client Risk</dt>
                  <dd className="font-medium">15%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Utilization and Overtime Risk</dt>
                  <dd className="font-medium">10%</dd>
                </div>
              </dl>
              <p className="text-xs text-slate-500 mt-3">
                Final score blends baseline (60%) with ML prediction (40%).
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="font-semibold text-slate-900">SHAP Explanation Methodology</h3>
        </div>
        <div className="card-body text-sm text-slate-600 space-y-2">
          <p>
            SHAP (SHapley Additive exPlanations) values show each feature's contribution to pushing the risk score
            away from the baseline (average model output).
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>Positive SHAP (red):</strong> Feature increases risk prediction</li>
            <li><strong>Negative SHAP (green):</strong> Feature decreases risk prediction</li>
            <li><strong>Magnitude:</strong> Absolute value indicates strength of influence</li>
          </ul>
          <p className="text-amber-700 bg-amber-50 p-2 rounded">
            <strong>Important:</strong> SHAP shows model behavior correlation, not causality.
            Features may be proxies for underlying causes. Always validate with domain knowledge.
          </p>
        </div>
      </div>
    </div>
  );
}