"""
Структурные тесты (White-box) для API Cyber Club v4.
Запуск: pytest tests/test_unit.py -v
"""

from fastapi.testclient import TestClient
from main import app, Base, engine, SessionLocal, Computer, User, Session
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


# ============================================================
# GET /pcs
# ============================================================

def test_get_pcs_returns_all_5():
    """GET /pcs возвращает 5 ПК."""
    response = client.get("/pcs")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_pcs_all_free_initially():
    """Все ПК изначально свободны."""
    response = client.get("/pcs")
    for pc in response.json():
        assert pc["is_busy"] == False
        assert pc["session_end"] is None
        assert pc["user"] is None


def test_get_pcs_structure():
    """Проверка структуры ответа."""
    response = client.get("/pcs")
    pc = response.json()[0]
    assert "id" in pc
    assert "is_busy" in pc
    assert "session_end" in pc
    assert "user" in pc


# ============================================================
# POST /book — успешные сценарии
# ============================================================

def test_book_pc_success():
    """Успешное бронирование."""
    response = client.post("/book/1?hours=2&name=Иван&phone=89001234567")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc1 = next(pc for pc in pcs if pc["id"] == 1)
    assert pc1["is_busy"] == True
    assert pc1["user"]["name"] == "Иван"
    assert pc1["user"]["phone"] == "89001234567"


def test_book_pc_with_email():
    """Бронирование с email."""
    response = client.post("/book/2?hours=1&name=Мария&phone=89007654321&email=maria@mail.ru")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc2 = next(pc for pc in pcs if pc["id"] == 2)
    assert pc2["user"]["email"] == "maria@mail.ru"


def test_book_pc_without_email():
    """Бронирование без email — поле null."""
    response = client.post("/book/1?hours=2&name=Иван&phone=89001234567")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc1 = next(pc for pc in pcs if pc["id"] == 1)
    assert pc1["user"]["email"] is None


def test_book_pc_with_plus7():
    """Телефон с +7 проходит."""
    response = client.post("/book/1?hours=2&name=Иван&phone=%2B79001234567")
    assert response.status_code == 200


def test_book_pc_with_8():
    """Телефон с 8 проходит."""
    response = client.post("/book/1?hours=2&name=Иван&phone=89001234567")
    assert response.status_code == 200


def test_book_pc_session_end_set():
    """session_end устанавливается корректно."""
    response = client.post("/book/1?hours=1.5&name=Иван&phone=89001234567")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc1 = next(pc for pc in pcs if pc["id"] == 1)
    assert pc1["session_end"] is not None

    session_end = datetime.fromisoformat(pc1["session_end"])
    expected = datetime.now() + timedelta(hours=1.5)
    diff = abs((session_end - expected).total_seconds())
    assert diff < 5  # Допуск 5 секунд


# ============================================================
# POST /book — валидация телефона
# ============================================================

def test_book_pc_invalid_phone_short():
    """Телефон меньше 11 цифр — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=8900123456")
    assert response.status_code == 400


def test_book_pc_invalid_phone_long():
    """Телефон больше 11 цифр — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=890012345678")
    assert response.status_code == 400


def test_book_pc_invalid_phone_letters():
    """Телефон с буквами — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=8900abcdefg")
    assert response.status_code == 400


def test_book_pc_invalid_phone_not_8_or_7():
    """Телефон не начинается с 8 или +7 — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=99001234567")
    assert response.status_code == 400


def test_book_pc_invalid_phone_empty():
    """Пустой телефон — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=")
    assert response.status_code == 400


# ============================================================
# POST /book — валидация email
# ============================================================

def test_book_pc_invalid_email_no_at():
    """Email без @ — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=89001234567&email=usermail.ru")
    assert response.status_code == 400


def test_book_pc_invalid_email_no_domain():
    """Email без домена — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=89001234567&email=user@mail")
    assert response.status_code == 400


def test_book_pc_invalid_email_no_name():
    """Email без имени до @ — ошибка 400."""
    response = client.post("/book/1?hours=2&name=Иван&phone=89001234567&email=@mail.ru")
    assert response.status_code == 400


def test_book_pc_valid_email_complex():
    """Сложный email проходит."""
    response = client.post("/book/1?hours=2&name=Иван&phone=89001234567&email=ivan.petrov123@sub.mail.ru")
    assert response.status_code == 200


# ============================================================
# POST /book — занятый ПК и несуществующий ПК
# ============================================================

def test_book_pc_already_busy():
    """Повторное бронирование занятого ПК — ошибка 400."""
    client.post("/book/1?hours=2&name=Иван&phone=89001234567")
    response = client.post("/book/1?hours=1&name=Петр&phone=89009999999")
    assert response.status_code == 400


def test_book_pc_not_found():
    """Бронирование несуществующего ПК — ошибка 404."""
    response = client.post("/book/999?hours=1&name=Иван&phone=89001234567")
    assert response.status_code == 404


# ============================================================
# POST /book — повторный пользователь
# ============================================================

def test_book_pc_repeat_user():
    """Повторное бронирование тем же пользователем."""
    client.post("/book/1?hours=1&name=Иван&phone=89001234567")
    client.post("/end/1")
    response = client.post("/book/2?hours=2&name=Иван Обновленный&phone=89001234567")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc2 = next(pc for pc in pcs if pc["id"] == 2)
    assert pc2["user"]["name"] == "Иван Обновленный"
    assert pc2["user"]["phone"] == "89001234567"


def test_book_pc_repeat_user_updates_email():
    """Повторный пользователь — email обновляется."""
    client.post("/book/1?hours=1&name=Иван&phone=89001234567&email=old@mail.ru")
    client.post("/end/1")
    client.post("/book/2?hours=2&name=Иван&phone=89001234567&email=new@mail.ru")

    pcs = client.get("/pcs").json()
    pc2 = next(pc for pc in pcs if pc["id"] == 2)
    assert pc2["user"]["email"] == "new@mail.ru"


# ============================================================
# POST /end
# ============================================================

def test_end_session_success():
    """Успешное завершение сессии."""
    client.post("/book/1?hours=2&name=Иван&phone=89001234567")
    response = client.post("/end/1")
    assert response.status_code == 200

    pcs = client.get("/pcs").json()
    pc1 = next(pc for pc in pcs if pc["id"] == 1)
    assert pc1["is_busy"] == False
    assert pc1["user"] is None
    assert pc1["session_end"] is None


def test_end_session_free_pc():
    """Завершение на свободном ПК — не ломается."""
    response = client.post("/end/1")
    assert response.status_code == 200


def test_end_session_not_found():
    """Завершение на несуществующем ПК — ошибка 404."""
    response = client.post("/end/999")
    assert response.status_code == 404


def test_end_session_deactivates_session():
    """Завершение сессии делает её неактивной в БД."""
    client.post("/book/1?hours=2&name=Иван&phone=89001234567")
    client.post("/end/1")

    db = SessionLocal()
    s = db.query(Session).filter(Session.user.has(phone="89001234567")).first()
    assert s.is_active == False
    db.close()


# ============================================================
# GET /history
# ============================================================

def test_history_existing_user():
    """История существующего пользователя."""
    client.post("/book/1?hours=2&name=Иван&phone=89001234567")
    client.post("/book/2?hours=1&name=Иван&phone=89001234567")

    response = client.get("/history?phone=89001234567")
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["name"] == "Иван"
    assert data["user"]["phone"] == "89001234567"
    assert len(data["sessions"]) == 2


def test_history_not_found():
    """История несуществующего пользователя — ошибка 404."""
    response = client.get("/history?phone=89009999999")
    assert response.status_code == 404


def test_history_structure():
    """Проверка структуры ответа истории."""
    client.post("/book/1?hours=2&name=Иван&phone=89001234567")

    response = client.get("/history?phone=89001234567")
    data = response.json()
    session = data["sessions"][0]

    assert "id" in session
    assert "pc_id" in session
    assert "start_time" in session
    assert "end_time" in session
    assert "hours" in session
    assert "is_active" in session


def test_history_no_sessions():
    """История нового пользователя — пустой список сессий."""
    # Создаём сессию и сразу завершаем
    client.post("/book/3?hours=1&name=Петр&phone=89001112233")
    client.post("/end/3")

    response = client.get("/history?phone=89001112233")
    data = response.json()
    assert data["user"]["name"] == "Петр"
    # Сессия есть, но неактивна
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["is_active"] == False


# ============================================================
# Авто-освобождение
# ============================================================

def test_auto_release_expired_session():
    """ПК с истекшей сессией автоматически освобождается."""
    db = SessionLocal()
    user = User(name="Тест", phone="89000000000")
    db.add(user)
    db.commit()

    pc = db.query(Computer).filter(Computer.id == 1).first()
    pc.is_busy = True
    pc.session_end = datetime.now() - timedelta(hours=1)
    pc.current_user_id = user.id

    session = Session(
        user_id=user.id,
        pc_id=1,
        end_time=datetime.now() - timedelta(hours=1),
        hours=1,
        is_active=True
    )
    db.add(session)
    db.commit()
    db.close()

    response = client.get("/pcs")
    pc1 = next(pc for pc in response.json() if pc["id"] == 1)
    assert pc1["is_busy"] == False
    assert pc1["user"] is None


def test_auto_release_deactivates_session():
    """Авто-освобождение помечает сессию is_active = False."""
    db = SessionLocal()
    user = User(name="Тест2", phone="89000000002")
    db.add(user)
    db.commit()
    db.refresh(user)

    pc = db.query(Computer).filter(Computer.id == 2).first()
    pc.is_busy = True
    pc.session_end = datetime.now() - timedelta(hours=1)
    pc.current_user_id = user.id

    session = Session(
        user_id=user.id,
        pc_id=2,
        end_time=datetime.now() - timedelta(hours=1),
        hours=1,
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    session_id = session.id
    db.close()

    # Вызываем GET, который должен завершить сессию
    client.get("/pcs")

    db = SessionLocal()
    s = db.query(Session).filter(Session.id == session_id).first()
    assert s is not None, "Сессия не найдена в БД"
    assert s.is_active == False, "Сессия должна быть неактивной"
    db.close()

def test_active_session_not_released():
    """Активная сессия не завершается раньше времени."""
    client.post("/book/1?hours=24&name=Иван&phone=89001234567")

    pcs = client.get("/pcs").json()
    pc1 = next(pc for pc in pcs if pc["id"] == 1)
    assert pc1["is_busy"] == True
    assert pc1["user"] is not None


# ============================================================
# Интеграционные проверки
# ============================================================

def test_full_booking_cycle():
    """Полный цикл: бронь → проверка → завершение → проверка."""
    # Бронь
    r = client.post("/book/3?hours=1&name=Анна&phone=89003334455&email=anna@mail.ru")
    assert r.status_code == 200

    # Проверка
    pcs = client.get("/pcs").json()
    pc3 = next(pc for pc in pcs if pc["id"] == 3)
    assert pc3["is_busy"] == True
    assert pc3["user"]["name"] == "Анна"
    assert pc3["user"]["email"] == "anna@mail.ru"

    # Завершение
    r = client.post("/end/3")
    assert r.status_code == 200

    # Проверка после завершения
    pcs = client.get("/pcs").json()
    pc3 = next(pc for pc in pcs if pc["id"] == 3)
    assert pc3["is_busy"] == False
    assert pc3["user"] is None
