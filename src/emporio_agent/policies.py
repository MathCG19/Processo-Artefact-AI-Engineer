"""Retrieval over the store policy manual (PDF).

Pipeline:  PDF --pymupdf4llm--> Markdown --split by headings--> one chunk per (sub)section
           --embeddings--> in-memory matrix (numpy) cached on disk, keyed by PDF hash + model.

Why section-based chunks: the manual is already organized by topic (4.1 Direito de
Arrependimento, 5.2 Entregas para Outras Cidades...). Splitting on headings keeps each rule
intact and gives a human-readable source for every answer. With ~25 chunks a vector database
would add infrastructure without benefit; a numpy dot product is exact and instantaneous.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from .config import CACHE_DIR, POLICY_PDF

# Repeated page header/footer lines that carry no content.
NOISE_LINES = [
    re.compile(r"^\*\*Empório da Música\*\*\s+Manual de Políticas e Procedimentos\s*$"),
    re.compile(r"^Página \d+\s*$"),
]
SHORT_INTRO_CHARS = 300  # section intros shorter than this are merged into the first subsection


@dataclass
class PolicyChunk:
    id: str           # "4.1", "2", "0" (cover)
    title: str        # "4.1 Direito de Arrependimento (Compras Online)"
    breadcrumb: str   # "4. Política de Trocas e Devoluções > 4.1 Direito de Arrependimento ..."
    text: str

    def embedding_text(self) -> str:
        return f"{self.breadcrumb}\n{self.text}"


def extract_markdown(pdf_path: Path = POLICY_PDF) -> str:
    # pymupdf4llm prints parser warnings (e.g. optional OCR engine missing); keep the CLI clean.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import pymupdf4llm

        return pymupdf4llm.to_markdown(str(pdf_path), show_progress=False)


def _clean_heading(text: str) -> str:
    return re.sub(r"\*+", "", text).strip()


def _clean_body(lines: list[str]) -> str:
    kept = [ln.rstrip() for ln in lines if not any(p.match(ln.strip()) for p in NOISE_LINES)]
    text = "\n".join(kept)
    text = re.sub(r"^#\s+", "", text, flags=re.MULTILINE)    # cover title "# **EMPÓRIO...**"
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_chunks(markdown: str) -> list[PolicyChunk]:
    raw: list[tuple[str | None, str | None, list[str]]] = []  # (section, subsection, lines)
    section: str | None = None
    subsection: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            raw.append((section, subsection, buffer.copy()))
        buffer.clear()

    for line in markdown.splitlines():
        if line.startswith("### "):
            flush()
            subsection = _clean_heading(line[4:])
        elif line.startswith("## "):
            flush()
            section, subsection = _clean_heading(line[3:]), None
        else:
            buffer.append(line)
    flush()

    chunks: list[PolicyChunk] = []
    pending_intro = ""
    for i, (sec, sub, lines) in enumerate(raw):
        body = _clean_body(lines)
        if not body:
            continue
        next_is_same_section = i + 1 < len(raw) and raw[i + 1][0] == sec and raw[i + 1][1] is not None
        if sec and sub is None and next_is_same_section and len(body) < SHORT_INTRO_CHARS:
            pending_intro = body  # merge short section intro into its first subsection
            continue
        if pending_intro:
            body = f"{pending_intro}\n\n{body}"
            pending_intro = ""
        title = sub or sec or "Capa do manual — identificação e contato"
        match = re.match(r"^(\d+(?:\.\d+)?)", title)
        chunks.append(
            PolicyChunk(
                id=match.group(1) if match else "0",
                title=title,
                breadcrumb=" > ".join(x for x in (sec, sub) if x) or title,
                text=body,
            )
        )
    return chunks


class PolicyIndex:
    def __init__(self, chunks: list[PolicyChunk], embeddings: np.ndarray, embed_query: Callable[[str], np.ndarray]):
        self.chunks = chunks
        self.embeddings = embeddings
        self._embed_query = embed_query

    @classmethod
    def build_or_load(
        cls,
        embed: Callable[[list[str]], np.ndarray],
        embedding_model: str,
        pdf_path: Path = POLICY_PDF,
        cache_dir: Path = CACHE_DIR,
    ) -> "PolicyIndex":
        pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        cache_file = cache_dir / "policy_index.json"
        embed_query = lambda q: embed([q])[0]  # noqa: E731

        if cache_file.exists():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached.get("pdf_sha256") == pdf_hash and cached.get("embedding_model") == embedding_model:
                chunks = [PolicyChunk(**c) for c in cached["chunks"]]
                return cls(chunks, np.array(cached["embeddings"], dtype=np.float32), embed_query)

        markdown = extract_markdown(pdf_path)
        chunks = split_into_chunks(markdown)
        embeddings = embed([c.embedding_text() for c in chunks])

        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "policies.md").write_text(markdown, encoding="utf-8")  # for inspection
        cache_file.write_text(
            json.dumps(
                {
                    "pdf_sha256": pdf_hash,
                    "embedding_model": embedding_model,
                    "chunks": [asdict(c) for c in chunks],
                    "embeddings": embeddings.tolist(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return cls(chunks, embeddings, embed_query)

    def search(self, query: str, k: int = 3) -> list[tuple[PolicyChunk, float]]:
        scores = self.embeddings @ self._embed_query(query)
        top = np.argsort(-scores)[: max(1, k)]
        return [(self.chunks[i], float(scores[i])) for i in top]


def search_store_policies(index: PolicyIndex, query: str, k: int = 3) -> dict:
    k = max(1, min(int(k or 3), 5))
    return {
        "consulta": query,
        "trechos": [
            {"secao": chunk.breadcrumb, "relevancia": round(score, 3), "conteudo": chunk.text}
            for chunk, score in index.search(query, k)
        ],
        "instrucao": "Responda somente com base nestes trechos. Se não cobrirem a pergunta, diga que não tem a informação.",
    }
