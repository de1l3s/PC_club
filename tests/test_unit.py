"""
Структурные тесты (White-box) для API Cyber Club.
Запуск: pytest tests/test_unit.py -v
"""

from fastapi.testclient import TestClient
from main import app, Base, engine, SessionLocal, Computer
from datetime import datetime, timedelta

client = TestClient(app)


def setup_function():
    """Выполняется перед каждым тестом — сбрасывает БД."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    for i in range(5):
        db.add(Computer())
    db.commit()
    db.close()


# === GET /pcs ===

def test_get_pcs_returns_all_5():
    response = client.get("/pcs")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_pcs_all_free_initially():
    response = client.get("/pcs")
    for pc in response.json():
        assert pc["is_busy"] == False
        assert pc["session_end"] is None


# === POST /book ===

def test_book_pc_success():
    response = client.post("/book/1?hours=2")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc1 = next(pc for pc in pcs if pc["id"] == 1)
    assert pc1["is_busy"] == True
    assert pc1["session_end"] is not None


def test_book_pc_already_busy():
    client.post("/book/1?hours=2")
    response = client.post("/book/1?hours=1")
    assert response.status_code == 400


def test_book_pc_not_found():
    response = client.post("/book/999?hours=1")
    assert response.status_code == 404


# === POST /end ===

def test_end_session_success():
    client.post("/book/1?hours=2")
    response = client.post("/end/1")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc1 = next(pc for pc in pcs if pc["id"] == 1)
    assert pc1["is_busy"] == False


def test_end_session_not_found():
    response = client.post("/end/999")
    assert response.status_code == 404


# === Авто-освобождение ===

def test_auto_release_expired():
    db = SessionLocal()
    pc = db.query(Computer).filter(Computer.id == 1).first()
    pc.is_busy = True
    pc.session_end = datetime.now() - timedelta(hours=1)
    db.commit()
    db.close()

    response = client.get("/pcs")
    pc1 = next(pc for pc in response.json() if pc["id"] == 1)
    assert pc1["is_busy"] == False
