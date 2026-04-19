from a_stock_agent.database import SQLiteRepository
from a_stock_agent.knowledge import DeterministicEmbeddingService, KnowledgeService


def test_import_text_document_chunks_and_retrieves(tmp_path):
    book = tmp_path / "book.txt"
    book.write_text("Margin of safety protects investors.\nIntrinsic value matters.", encoding="utf-8")
    repo = SQLiteRepository(tmp_path / "agent.sqlite3")
    service = KnowledgeService(
        repository=repo,
        embedding_service=DeterministicEmbeddingService(dimensions=8),
        chunk_size=32,
        chunk_overlap=4,
    )

    result = service.import_file(book)
    hits = service.search("intrinsic value", top_k=3)

    assert result.status == "imported"
    assert result.chunks_count >= 1
    assert hits[0].document_title == "book.txt"
    assert "Intrinsic value" in hits[0].text


def test_import_same_document_skips_without_force(tmp_path):
    book = tmp_path / "book.md"
    book.write_text("# Notes\n\nLong-term investing.", encoding="utf-8")
    repo = SQLiteRepository(tmp_path / "agent.sqlite3")
    service = KnowledgeService(
        repository=repo,
        embedding_service=DeterministicEmbeddingService(dimensions=8),
    )

    first = service.import_file(book)
    second = service.import_file(book)

    assert first.status == "imported"
    assert second.status == "skipped"
    assert second.skipped_reason == "duplicate_document"
