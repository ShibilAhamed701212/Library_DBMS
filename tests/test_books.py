"""Regression tests for book creation (books.author is NOT NULL)."""


def test_add_book_populates_author_name(monkeypatch):
    import backend.services.book_service as book_service

    calls = []
    monkeypatch.setattr(book_service, "execute", lambda q, p=None: calls.append((q, p)) or 42)
    assert book_service.add_book("Dune", 3, "Fiction", 2) == 42

    query, params = calls[0]
    columns = query.split("(", 1)[1].split(")", 1)[0]
    assert [c.strip() for c in columns.split(",")][:3] == ["title", "author", "author_id"]
    assert "SELECT name FROM authors WHERE author_id = %s" in query
    assert params[:3] == ("Dune", 3, 3)
    assert query.count("%s") == len(params)


def test_update_book_keeps_author_name_in_sync(monkeypatch):
    import backend.services.book_service as book_service

    calls = []
    monkeypatch.setattr(book_service, "get_book", lambda bid: {"total_copies": 2, "available_copies": 2})
    monkeypatch.setattr(book_service, "execute", lambda q, p=None: calls.append((q, p)))
    book_service.update_book(1, "Dune", 4, "Fiction", 3)

    query, params = calls[0]
    assert "author = COALESCE((SELECT name FROM authors WHERE author_id = %s), author)" in query
    assert query.count("%s") == len(params)


def _admin_add_book(client, monkeypatch, tmp_path, **files):
    import io
    import backend.services.book_service as book_service
    import backend.services.enrichment_service as enrichment_service
    import backend.services.audit_service as audit_service
    from tests.conftest import login_as

    added = []
    monkeypatch.chdir(tmp_path)  # e-books are saved relative to the working directory
    monkeypatch.setattr(book_service, "add_book", lambda *a: added.append(a) or 1)
    monkeypatch.setattr(enrichment_service, "enrich_book_metadata", lambda book_id: "")
    monkeypatch.setattr(audit_service, "log_action", lambda *a, **k: None)
    login_as(client, 1, role="admin")
    data = {"title": "Dune", "author_id": "3", "category": "Fiction", "copies": "2"}
    for name, (content, filename) in files.items():
        data[name] = (io.BytesIO(content), filename)
    response = client.post("/admin/book/add", data=data, content_type="multipart/form-data")
    return response, added


def test_admin_add_book_without_pdf(client, monkeypatch, tmp_path):
    response, added = _admin_add_book(client, monkeypatch, tmp_path)
    assert response.status_code == 302
    assert added == [("Dune", 3, "Fiction", 2, None, None, None)]


def test_admin_add_book_rejects_non_pdf_ebook(client, monkeypatch, tmp_path):
    response, added = _admin_add_book(client, monkeypatch, tmp_path, pdf_file=(b"<script>", "book.html"))
    assert response.status_code == 302
    assert added == []
    assert not (tmp_path / "static").exists()


def test_admin_add_book_saves_pdf_into_missing_dir(client, monkeypatch, tmp_path):
    response, added = _admin_add_book(client, monkeypatch, tmp_path, pdf_file=(b"%PDF-1.4", "dune.pdf"))
    assert response.status_code == 302
    pdf_src = added[0][4]
    assert pdf_src.startswith("uploads/ebooks/") and pdf_src.endswith(".pdf")
    assert (tmp_path / "static" / pdf_src).exists()
