from fastapi.testclient import TestClient

from a_stock_agent.api.app import create_app


def test_health_endpoint_reports_sqlite_and_agent(tmp_path):
    app = create_app(database_path=tmp_path / "agent.sqlite3")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_knowledge_import_and_list_documents(tmp_path):
    app = create_app(database_path=tmp_path / "agent.sqlite3")
    client = TestClient(app)
    book = tmp_path / "book.txt"
    book.write_text("Value investing requires discipline.", encoding="utf-8")

    response = client.post("/api/v1/knowledge/import", json={"file_path": str(book)})
    docs_response = client.get("/api/v1/knowledge/documents")

    assert response.status_code == 200
    assert response.json()["status"] == "imported"
    assert docs_response.json()["documents"][0]["title"] == "book.txt"


def test_chat_endpoint_returns_research_boundary_disclaimer(tmp_path):
    app = create_app(database_path=tmp_path / "agent.sqlite3")
    client = TestClient(app)

    response = client.post("/api/v1/chat", json={"message": "分析一下600519"})

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert "research" in body["disclaimer"].lower()
    assert body["answer"]
