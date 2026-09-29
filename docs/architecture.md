# Architecture Decision Records

## ADR-001: Monolithic Backend with Modular Internal Structure

**Status**: Accepted

**Context**: Need to build an MVP quickly while maintaining separation of concerns.

**Decision**: Single FastAPI application with clear module boundaries (api, analytics, ml, rag, agents) rather than microservices.

**Consequences**:
- Simpler deployment and debugging
- Clear module interfaces enable future extraction
- Shared database is a coupling point

## ADR-002: SQLAlchemy 2.0 with Declarative Models

**Status**: Accepted

**Context**: Need type-safe database access with good IDE support.

**Decision**: Use SQLAlchemy 2.0 ORM with Mapped annotations and DeclarativeBase.

**Consequences**:
- Type hints work with Pydantic
- Explicit relationships
- Migration via Alembic when needed

## ADR-003: LightGBM for Risk Modeling

**Status**: Accepted

**Context**: Need interpretable, fast-to-train model for tabular data with good SHAP support.

**Decision**: LightGBM over XGBoost or Random Forest.

**Consequences**:
- Native SHAP support via TreeExplainer
- Fast training on small datasets
- Handles categorical features well

## ADR-004: SHAP for Explainability

**Status**: Accepted

**Context**: Stakeholders need to understand risk drivers.

**Decision**: Use SHAP TreeExplainer for LightGBM model.

**Consequences**:
- Consistent local and global explanations
- Computationally efficient for tree models
- Must clarify SHAP ≠ causality in UI

## ADR-005: In-Memory Vector Search for RAG

**Status**: Accepted

**Context**: Need semantic search for knowledge base without adding infrastructure complexity.

**Decision**: sentence-transformers + numpy dot product for MVP.

**Consequences**:
- No pgvector/Redis/Weaviate dependency
- Scales to ~10k chunks comfortably
- Easy to swap for pgvector later

## ADR-006: Tool-Based Agent Architecture

**Status**: Accepted

**Context**: Need AI investigation without full autonomous agent framework.

**Decision**: Deterministic tool functions + LLM orchestration.

**Consequences**:
- Predictable, testable behavior
- Easy to add/remove tools
- LLM only selects tools, doesn't execute logic

## ADR-007: Next.js App Router with Server Components

**Status**: Accepted

**Context**: Modern React framework with good TypeScript support.

**Decision**: Next.js 16 App Router, client components for interactivity.

**Consequences**:
- Streaming SSR for dashboard
- Type-safe API contracts
- Tailwind for consistent styling

## ADR-008: Docker Compose for Local Development

**Status**: Accepted

**Context**: Need reproducible environment matching production-like setup.

**Decision**: Two-container demo with the bundled SQLite dataset, backend, and frontend. PostgreSQL is a future deployment option.

**Consequences**:
- One-command startup
- Mirrors production topology
- Volumes for hot reload

## ADR-009: Synthetic Data with Fixed Seed

**Status**: Accepted

**Context**: Need reproducible, realistic test data for demos.

**Decision**: Faker + custom patterns with seed=42.

**Consequences**:
- Consistent demos
- Realistic patterns (not random noise)
- Easy to extend patterns

## ADR-010: No Authentication in MVP

**Status**: Accepted

**Context**: Focus on core analytics and AI features.

**Decision**: Defer auth to post-MVP.

**Consequences**:
- Simpler development
- Not production-ready
- Clear boundary for future work
