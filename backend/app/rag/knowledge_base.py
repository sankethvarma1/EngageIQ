from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np


_THIS_FILE = Path(__file__).resolve()
_KB_CANDIDATES = [
    Path("/app/docs/knowledge_base"),  # Docker layout
    _THIS_FILE.parent.parent.parent.parent / "docs" / "knowledge_base",  # local repo root
    _THIS_FILE.parent.parent.parent / "docs" / "knowledge_base",  # legacy/back-compat
]
KNOWLEDGE_BASE_DIR = next((p for p in _KB_CANDIDATES if p.exists()), _KB_CANDIDATES[1])


@dataclass
class DocumentChunk:
    doc_id: str
    title: str
    section: str
    content: str
    source: str
    embedding: Optional[np.ndarray] = None


class KnowledgeBase:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.chunks: List[DocumentChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self._load_documents()

    def _load_documents(self):
        if not KNOWLEDGE_BASE_DIR.exists():
            return

        for md_file in KNOWLEDGE_BASE_DIR.glob("*.md"):
            content = md_file.read_text()
            doc_id = md_file.stem
            title = doc_id.replace("_", " ").title()

            sections = self._split_into_sections(content, doc_id, title)
            for sec_title, sec_content in sections:
                chunk = DocumentChunk(
                    doc_id=doc_id,
                    title=title,
                    section=sec_title,
                    content=sec_content,
                    source=str(md_file),
                )
                self.chunks.append(chunk)

        if self.chunks:
            self._compute_embeddings()

    def _split_into_sections(self, content: str, doc_id: str, title: str) -> List[tuple]:
        sections = []
        current_section = "Introduction"
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_content:
                    sections.append((current_section, "\n".join(current_content).strip()))
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append((current_section, "\n".join(current_content).strip()))

        if not sections:
            sections = [(title, content)]

        return sections

    def _compute_embeddings(self):
        texts = [f"{c.title}. {c.section}. {c.content}" for c in self.chunks]
        self.embeddings = self.model.encode(texts, show_progress_bar=False)

    def search(self, query: str, top_k: int = 5) -> List[DocumentChunk]:
        if not self.chunks or self.embeddings is None:
            return []

        query_embedding = self.model.encode([query])
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            chunk.embedding = self.embeddings[idx]
            results.append(chunk)

        return results


_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base


def retrieve_evidence(query: str, top_k: int = 5) -> List[DocumentChunk]:
    kb = get_knowledge_base()
    return kb.search(query, top_k)