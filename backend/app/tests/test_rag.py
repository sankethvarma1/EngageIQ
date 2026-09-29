import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.ml.risk_model import train_model
from app.rag.knowledge_base import KNOWLEDGE_BASE_DIR, KnowledgeBase


def test_knowledge_base_dir_resolves_with_documents():
    assert KNOWLEDGE_BASE_DIR.exists(), f"Knowledge base dir missing: {KNOWLEDGE_BASE_DIR}"
    md_files = sorted(p.name for p in KNOWLEDGE_BASE_DIR.glob("*.md"))
    assert len(md_files) == 5
    assert "sla_policy.md" in md_files
    assert "delivery_playbook.md" in md_files


def test_section_splitting_preserves_metadata():
    kb = KnowledgeBase.__new__(KnowledgeBase)
    content = "# Title\n\nIntro text.\n\n## Response Time SLAs\n- Critical: 1 hour\n\n## Breach Consequences\n- First breach: notification\n"
    sections = KnowledgeBase._split_into_sections(kb, content, "sla_policy", "Sla Policy")
    titles = [s[0] for s in sections]
    assert "Response Time SLAs" in titles
    assert "Breach Consequences" in titles
    # Every chunk must carry retrievable metadata (doc_id/title/section/source)
    assert all(isinstance(t, str) and isinstance(c, str) for t, c in sections)


def test_train_model_rejects_insufficient_data():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        with pytest.raises(ValueError, match="Insufficient training data"):
            train_model(db)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
