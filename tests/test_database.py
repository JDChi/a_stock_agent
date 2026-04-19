from array import array

from a_stock_agent.database import SQLiteRepository


def test_repository_initializes_schema_and_fts(tmp_path):
    repo = SQLiteRepository(tmp_path / "agent.sqlite3")
    repo.initialize()

    document_id = repo.create_document(
        title="margin of safety",
        source_path="/books/mos.txt",
        source_type="txt",
        sha256="abc123",
    )
    repo.add_chunk(
        document_id=document_id,
        chunk_index=0,
        text="safety margin and intrinsic value",
        metadata={"chapter": "one"},
        embedding=array("f", [1.0, 0.0, 0.0]).tobytes(),
    )

    rows = repo.search_chunks("intrinsic", limit=5)

    assert rows[0]["document_id"] == document_id
    assert rows[0]["text"] == "safety margin and intrinsic value"
    assert rows[0]["metadata"]["chapter"] == "one"


def test_document_hash_is_idempotent(tmp_path):
    repo = SQLiteRepository(tmp_path / "agent.sqlite3")
    repo.initialize()

    first_id = repo.create_document("Book", "/books/book.txt", "txt", "same")
    second_id = repo.create_document("Book", "/books/book.txt", "txt", "same")

    assert first_id == second_id
    assert len(repo.list_documents()) == 1
