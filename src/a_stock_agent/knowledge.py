from __future__ import annotations

import hashlib
import math
import re
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .database import SQLiteRepository


@dataclass(frozen=True)
class ImportResult:
    document_id: int
    title: str
    chunks_count: int
    status: str
    skipped_reason: str | None = None


@dataclass(frozen=True)
class KnowledgeHit:
    document_id: int
    document_title: str
    chunk_index: int
    text: str
    score: float
    metadata: dict


class DeterministicEmbeddingService:
    def __init__(self, dimensions: int = 768):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        values = [0.0] * self.dimensions
        for token in _tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            values[index] += 1.0
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return values
        return [value / norm for value in values]


class SentenceTransformerEmbeddingService:
    def __init__(self, model_name: str, cache_folder: str | Path | None = None):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name, cache_folder=str(cache_folder) if cache_folder else None)

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return [float(value) for value in vector]


class KnowledgeService:
    def __init__(
        self,
        repository: SQLiteRepository,
        embedding_service,
        chunk_size: int = 900,
        chunk_overlap: int = 120,
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.repository.initialize()

    def import_file(self, path: str | Path, force: bool = False) -> ImportResult:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        source_type = file_path.suffix.lower().lstrip(".")
        if source_type not in {"pdf", "epub", "md", "markdown", "txt"}:
            raise ValueError("Supported document formats: PDF, EPUB, Markdown, TXT")

        digest = _sha256(file_path)
        existing = self.repository.find_document_by_hash(digest)
        if existing and not force:
            return ImportResult(
                document_id=int(existing["id"]),
                title=str(existing["title"]),
                chunks_count=int(existing.get("chunks_count", 0) or 0),
                status="skipped",
                skipped_reason="duplicate_document",
            )
        if existing and force:
            self.repository.delete_document(int(existing["id"]))

        sections = list(_extract_sections(file_path, source_type))
        text = "\n\n".join(section_text for _, section_text in sections).strip()
        if not text:
            raise ValueError("No extractable text found. OCR is not supported in v1.")

        document_id = self.repository.create_document(
            title=file_path.name,
            source_path=str(file_path),
            source_type="markdown" if source_type == "md" else source_type,
            sha256=digest,
        )

        chunks = list(_chunk_text(text, self.chunk_size, self.chunk_overlap))
        for index, chunk in enumerate(chunks):
            vector = self.embedding_service.embed(chunk)
            self.repository.add_chunk(
                document_id=document_id,
                chunk_index=index,
                text=chunk,
                metadata={"source": file_path.name},
                embedding=array("f", vector).tobytes(),
            )

        return ImportResult(
            document_id=document_id,
            title=file_path.name,
            chunks_count=len(chunks),
            status="imported",
        )

    def search(self, query: str, top_k: int = 8) -> list[KnowledgeHit]:
        query_vector = self.embedding_service.embed(query)
        rows = self.repository.search_chunks(query, limit=max(top_k * 4, top_k))
        hits = []
        for row in rows:
            score = _cosine(query_vector, _bytes_to_vector(row["embedding"]))
            hits.append(
                KnowledgeHit(
                    document_id=int(row["document_id"]),
                    document_title=str(row["document_title"]),
                    chunk_index=int(row["chunk_index"]),
                    text=str(row["text"]),
                    score=score,
                    metadata=row["metadata"],
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]


def _extract_sections(path: Path, source_type: str) -> Iterable[tuple[dict, str]]:
    if source_type in {"txt", "md", "markdown"}:
        yield {}, path.read_text(encoding="utf-8")
        return
    if source_type == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF import") from exc
        reader = PdfReader(str(path))
        for page_index, page in enumerate(reader.pages, start=1):
            yield {"page": page_index}, page.extract_text() or ""
        return
    if source_type == "epub":
        try:
            import ebooklib
            from bs4 import BeautifulSoup
            from ebooklib import epub
        except ImportError as exc:
            raise RuntimeError("ebooklib and beautifulsoup4 are required for EPUB import") from exc
        book = epub.read_epub(str(path))
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            yield {"chapter": item.get_name()}, soup.get_text("\n")


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> Iterable[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        yield clean[start:end]
        if end == len(clean):
            break
        start = max(end - chunk_overlap, start + 1)


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    return words or list(text.lower())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bytes_to_vector(blob: bytes | None) -> list[float]:
    if not blob:
        return []
    values = array("f")
    values.frombytes(blob)
    return list(values)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
