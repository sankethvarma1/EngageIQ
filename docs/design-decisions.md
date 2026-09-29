# Design Decisions

## Data Model

### Engagement-Centric Design
All transactional data links to `engagements` table. This enables engagement-level analytics without complex joins.

### Time-Series in Relational Tables
Timesheets, SLA events, and feedback use date columns rather than separate time-series DB. Sufficient for MVP scale.

### Enum Types for Controlled Vocabularies
Status, priority, and type fields use SQLAlchemy Enum mappings with the bundled SQLite database.

## Analytics

### KPI Calculation Strategy
- **Pure functions** in `app/analytics/kpis.py` - testable without FastAPI
- **Database aggregation** via SQLAlchemy for performance
- **Pandas only for historical trends** - not for core KPIs

### Decimal Precision
All monetary values use `Decimal` with 2 decimal places. Avoids floating-point errors in financial calculations.

### Utilization Definition
`billable_hours / (billable + non_billable + overtime)` - standard professional services definition.

## Risk Model

### Hybrid Approach
60% interpretable baseline + 40% ML. Ensures explainability while capturing non-linear patterns.

### Risk Dimensions
1. **Financial** (30%): Margin, budget variance
2. **Delivery** (25%): Schedule variance, critical path delay
3. **Operational** (20%): SLA breaches, tickets, change requests, utilization
4. **Client** (15%): Satisfaction, NPS, trend
5. **Utilization and Overtime** (10%): Utilization anomalies, overtime

### Target Generation
Synthetic labels from business rules on historical engagements. No manual labeling needed.

### Evaluation Metrics
AUC-ROC primary, with precision/recall/F1 for class balance visibility.

## SHAP Implementation

### TreeExplainer
LightGBM native support. Fast computation (<50ms per engagement).

### UI Presentation
Top 10 features by |SHAP value|. Color-coded: red increases risk, green decreases.

### Disclaimer
UI explicitly states: "SHAP shows model behavior correlation, not causality."

## Anomaly Detection

### Statistical Thresholds
- Utilization: Z-score > 2.5
- Margin: < 10% (high), < 20% (medium)
- Tickets: > 50 total, > 5 critical
- SLA: > 20% breach rate
- Change Requests: > 15 count, > $100K cost impact
- Satisfaction: < 5 (high), < 6.5 (medium), declining trend

### Explainable Logic
Each anomaly includes: metric, value, expected range, severity, description.

## RAG Pipeline

### Document Chunking
Markdown headers (##) define sections. Each section = one chunk.

### Embeddings
all-MiniLM-L6-v2 (384 dim). Fast, good quality for technical text.

### Retrieval
Cosine similarity via numpy dot product. Top-K default 5.

### Metadata Preservation
Every chunk retains: doc_id, title, section, source file path.

## Agent Orchestration

### Tool Schema
OpenAI function-calling compatible JSON schemas for each tool.

### LLM Prompt
System prompt defines process: understand → select tools → analyze → synthesize.

### Iteration Limit
Max 5 tool call rounds to prevent infinite loops.

### Error Handling
Failed tool calls reported to LLM for adaptation.

## Frontend

### Component Structure
- Page components in `app/` (Next.js routes)
- Shared components in `components/`
- Types in `types/`
- API client in `lib/api.ts`

### State Management
React `useState`/`useEffect` for MVP. No Redux/Zustand needed yet.

### Charting
Recharts for all visualizations. Responsive containers.

### Styling
Tailwind CSS with custom color palette (primary, risk levels).

## API Design

### RESTful Conventions
- Plural nouns for collections
- Nested resources for engagement-scoped data
- Consistent error responses

### Response Models
Pydantic models for all responses. Automatic OpenAPI docs.

### Decimal Serialization
Convert to float in API layer (JSON doesn't support Decimal).

## Testing Strategy

### Unit Tests
- KPI calculations with known inputs
- Risk scoring logic
- Anomaly detection thresholds
- SHAP output structure

### Integration Tests
- API endpoints with test database
- Data generation reproducibility

### No E2E Tests Yet
Playwright/Cypress deferred to post-MVP.
