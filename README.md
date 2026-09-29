# EngageIQ

**Client Delivery Intelligence & Outcome Assurance Platform**

An enterprise-style analytics platform for monitoring client engagements across financial performance, delivery performance, operational performance, workforce utilization, SLA performance, and client satisfaction.

## Problem

Professional services organizations struggle to maintain visibility across their engagement portfolio. Risk signals are scattered across multiple systems (timesheets, budgets, tickets, milestones, client feedback), making it difficult to identify deteriorating engagements early. This platform consolidates data, computes KPIs, scores risk, explains drivers, and enables AI-assisted investigation.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  SQLite         │────▶│  FastAPI        │────▶│  Next.js        │
│  (Data Layer)   │     │  (Backend)      │     │  (Frontend)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  ML Pipeline    │
                    │  (Risk Model +  │
                    │   SHAP)         │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  RAG / Agents   │
                    │  (Knowledge     │
                    │   Base + LLM)   │
                    └─────────────────┘
```

## Features

- **Data Layer**: SQLite with 12 tables modeling clients, engagements, employees, timesheets, budgets, invoices, milestones, tickets, SLAs, change requests, and client feedback
- **Synthetic Data Generator**: Reproducible data with realistic patterns (healthy, financially deteriorating, delayed, high-change, high-ticket, SLA degradation, declining satisfaction, utilization issues)
- **KPI Analytics**: Revenue, cost, margin, budget variance, schedule variance, ticket backlog, SLA breach rate, change request rate, utilization, client satisfaction
- **Risk Model**: Interpretable baseline + LightGBM with configurable weights (financial 30%, delivery 25%, operational 20%, client 15%, data quality 10%)
- **SHAP Explanations**: Top feature contributions to the LightGBM model's predicted risk probability (the ML part of the blended score, not the final composite)
- **Anomaly Detection**: Statistical detection of utilization spikes, margin deterioration, ticket surges, SLA degradation, change request growth, satisfaction declines
- **RAG Knowledge Base**: 5 policy documents with semantic search (delivery playbook, SLA policy, escalation policy, margin management, project governance)
- **AI Investigation**: Tool-based agent orchestration for natural-language queries when an LLM key is configured; otherwise a labeled mock answer
- **Dashboard**: Portfolio overview, engagement details, investigation UI, model performance

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic 2 |
| Database | SQLite (bundled synthetic dataset) |
| Analytics | Pandas, NumPy |
| ML | scikit-learn, LightGBM, SHAP |
| RAG | sentence-transformers, in-memory embeddings |
| Frontend | Next.js 16, React 18, TypeScript, Tailwind CSS, HTML/CSS charts |
| Infrastructure | Docker, Docker Compose |

## Quick Start

### Prerequisites

- Python 3.11+ and Node.js 20+ for manual setup (Docker images use Python 3.12), or Docker & Docker Compose
- (Optional) NVIDIA Nemotron API key for LLM investigation

### Local Development

```bash
# Clone and navigate
git clone https://github.com/sankethvarma1/EngageIQ.git
cd EngageIQ

# Optional: cp .env.example backend/.env and set NEMOTRON_API_KEY

# Start all services
docker compose -f docker/docker-compose.yml up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

> **Port note:** 3000 is the default. If Next.js reports that 3000 is occupied
> and serves the app on port 3001 instead, open
> **http://localhost:3001/dashboard** and start the backend with
> `FRONTEND_URL=http://localhost:3001` (e.g.
> `FRONTEND_URL=http://localhost:3001 python -m uvicorn app.main:app --reload`)
> so the backend CORS policy matches the frontend origin. An app already
> listening on port 3000 may be a different, unrelated process — check with
> `lsof -i :3000` (macOS) before assuming it is EngageIQ.

The Docker backend uses the bundled SQLite dataset and saved LightGBM model.
The database inside the container is reset when the container is recreated.

### Run locally in two terminals (without Docker)

Start both terminals from the project directory (`EngageIQ` after cloning). Use Python 3.11+ and Node.js 20 or newer.

Terminal 1 — backend:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# The bundled backend/engageiq.db already contains 40 synthetic engagements.
python -m uvicorn app.main:app --reload
```

Terminal 2 — frontend:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000/dashboard**. The backend health check is
**http://localhost:8000/health**. Keep both terminals open while using the dashboard.
The investigation page returns a labeled mock response unless you set
`NEMOTRON_API_KEY` in Terminal 1 or in `backend/.env`.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLite URL (defaults to `sqlite:///./engageiq.db` when run from `backend/`) | No |
| `NEMOTRON_API_KEY` | NVIDIA API key for LLM | No (uses mock) |
| `NEMOTRON_BASE_URL` | Nemotron API endpoint | No |
| `RISK_MODEL_WEIGHTS` | JSON string of risk component weights | No |
| `NEXT_PUBLIC_API_URL` | Backend API URL (defaults to `http://localhost:8000/api`) | No |

## Database Schema

Key tables:
- `clients` - Client master data
- `engagements` - Core engagement records
- `employees` - Staff directory
- `employee_assignments` - Staffing allocations
- `timesheets` - Weekly hours (billable/non-billable/overtime)
- `budgets` - Planned vs actual by category
- `invoices` - Billing records
- `milestones` - Delivery milestones with dates
- `tickets` - Support/defect tickets
- `sla_events` - SLA measurements and breaches
- `change_requests` - Scope change tracking
- `client_feedback` - Survey responses (1-10 scales + NPS)

## ML Pipeline

### Risk Scoring

The risk model combines:
1. **Interpretable Baseline** (60% weight): Rule-based scoring across 5 risk dimensions
2. **LightGBM Model** (40% weight): Trained on synthetic historical engagement outcomes (rule-derived labels, see target variable below)

Target variable: Binary high-risk label derived from margin < 10%, schedule variance > 30 days, SLA breach > 20%, satisfaction < 5.

**Dataset size disclaimer**: The bundled synthetic dataset is small (40 engagements; typical retrain yields ~30 labeled samples, e.g. 21 train / 9 test). Reported metrics (AUC, accuracy, precision, recall, F1) are computed from real predictions but are not statistically meaningful at this sample size. Treat them as pipeline verification, not production model validation.

### SHAP Explanations

TreeSHAP provides per-engagement feature contributions for the trained LightGBM model output (the 40% ML component of the risk score, not the blended composite). The UI shows top 10 drivers with directionality (red = increases risk, green = decreases risk).

**Important**: SHAP explains model behavior, not causality. Features may be correlated proxies.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/engagements` | List engagements |
| GET | `/api/engagements/{id}` | Get engagement |
| GET | `/api/engagements/{id}/kpis` | Calculate all KPIs |
| GET | `/api/engagements/{id}/risk` | Get risk score & breakdown |
| GET | `/api/engagements/{id}/anomalies` | Detect anomalies |
| GET | `/api/engagements/{id}/explanation` | SHAP feature contributions |
| POST | `/api/ai/investigate` | AI-powered investigation |
| GET | `/api/engagements/model/metrics` | Model performance metrics |
| POST | `/api/engagements/model/retrain` | Retrain risk model |

## Agent Tools

The AI investigator orchestrates these deterministic tools:
- `query_engagement` - Basic engagement info
- `calculate_kpis` - Full KPI computation
- `calculate_risk` - Risk score with breakdown
- `get_shap_explanation` - SHAP feature contributions
- `detect_anomalies` - Statistical anomaly detection
- `retrieve_evidence` - RAG knowledge base search

**LLM mode**: Without `NEMOTRON_API_KEY`, `/api/ai/investigate` runs in mock mode — the endpoint, tool schemas, and evidence plumbing are real, but the final narrative is a labeled placeholder (`[Mock Response]...`), not Nemotron output. Set the key to enable real Nemotron responses. Never present mock output as model-generated analysis.
In mock mode, the provider returns a placeholder without calling the investigation tools; the response has empty `tool_calls` and `evidence` arrays. Semantic retrieval downloads the embedding model on first use and requires internet access then.

## Testing

```bash
# Backend tests
cd backend
pytest app/tests -v

# Frontend production build and TypeScript check
cd frontend
npm ci
npm run build
npm run typecheck
```

## Project Structure

```
engageiq/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routes
│   │   ├── analytics/       # KPI & anomaly calculations
│   │   ├── agents/          # Tool-based agent orchestration
│   │   ├── core/            # Config, LLM provider
│   │   ├── db/              # SQLAlchemy models, session
│   │   ├── ml/              # Risk model, SHAP
│   │   ├── rag/             # Knowledge base, embeddings
│   │   └── main.py          # FastAPI app
│   ├── scripts/
│   │   └── generate_data.py # Synthetic data generator
│   ├── requirements.txt
│   ├── engageiq.db      # Bundled synthetic data
│   └── models/          # Saved LightGBM model and metrics
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # API client, utilities
│   │   └── types/           # TypeScript types
│   └── package.json
├── docs/
│   ├── knowledge_base/      # RAG documents
│   └── architecture.md
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── .env.example
└── README.md
```

## Limitations

- No authentication/authorization implemented
- SQLite is used for the bundled demo; PostgreSQL and pgvector are not used in this version
- RAG uses in-memory embeddings; the embedding model needs a first-time download
- Nemotron integration uses mock provider without API key
- No background job processing (retraining is synchronous)
- Single-tenant; no multi-organization support
- No audit logging or data lineage

## Future Work

- [ ] Authentication (OAuth2/OIDC)
- [ ] pgvector integration for production RAG
- [ ] Background job queue (Celery/Redis) for model retraining
- [ ] Alerting engine (webhook/email on risk threshold breach)
- [ ] Engagement comparison views
- [ ] What-if scenario modeling
- [ ] Export to PDF/PowerPoint
- [ ] Multi-tenant support
- [ ] Audit trail and data lineage

## License

MIT License — see [LICENSE](LICENSE). Portfolio project for demonstration purposes.
