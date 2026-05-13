# Контракты взаимодействия (API Contracts)

## 1. Получение списка ПК

**Прототип:**
@app.get("/pcs")
def get_pcs() -> List[dict]

**Формат ответа:**
[
  {
    "id": 1,
    "is_busy": false,
    "session_end": null,
    "user": null
  },
  {
    "id": 2,
    "is_busy": true,
    "session_end": "2025-05-20T15:00:00",
    "user": {
      "name": "Иван",
      "phone": "89001234567",
      "email": "ivan@mail.ru"
    }
  }
]

**Заглушка для фронтенда:**
const mockPCs = [
    {id: 1, is_busy: false, session_end: null, user: null},
    {id: 2, is_busy: true, session_end: "2025-05-20T15:00:00", user: {name: "Иван", phone: "89001234567", email: "ivan@mail.ru"}}
];

---

## 2. Бронирование ПК

**Прототип:**
@app.post("/book/{pc_id}")
def book_pc(pc_id: int, hours: float, name: str, phone: str, email: str = None) -> dict

**Параметры:**
- pc_id (int) — из URL
- hours (float) — query-параметр, часы бронирования
- name (str) — query-параметр, имя пользователя
- phone (str) — query-параметр, 11 цифр, начиная с 8 или +7
- email (str) — query-параметр, необязательный, должен содержать @ и домен

**Валидация:**
- Телефон: ровно 11 цифр, первая цифра 8 или +7
- Email: формат user@domain.com (необязательно)

**Формат ответа (успех):**
{"message": "ПК 1 забронирован для Иван", "user_id": 1}

**Возможные ошибки:**
- 400: Некорректный номер телефона
- 400: Некорректный email
- 400: ПК уже занят
- 404: ПК не найден

**Заглушка для фронтенда:**
async function bookPCMock(id, hours, name, phone) {
    return {message: `ПК ${id} забронирован для ${name}`, user_id: 1};
}

---

## 3. Завершение сессии

**Прототип:**
@app.post("/end/{pc_id}")
def end_session(pc_id: int) -> dict

**Формат ответа:**
{"message": "Сессия ПК 3 завершена"}

**Возможные ошибки:**
- 404: ПК не найден

**Заглушка для фронтенда:**
async function endSessionMock(id) {
    return {message: `Сессия ПК ${id} завершена`};
}

---

## 4. История бронирований

**Прототип:**
@app.get("/history")
def get_history(phone: str) -> dict

**Параметры:**
- phone (str) — query-параметр, номер телефона

**Формат ответа:**
{
  "user": {"name": "Иван", "phone": "89001234567", "email": "ivan@mail.ru"},
  "sessions": [
    {
      "id": 1,
      "pc_id": 1,
      "start_time": "2025-05-20T12:00:00",
      "end_time": "2025-05-20T14:00:00",
      "hours": 2,
      "is_active": false
    }
  ]
}

**Возможные ошибки:**
- 404: Пользователь не найден

**Заглушка для фронтенда:**
async function historyMock(phone) {
    return {
        user: {name: "Иван", phone: "89001234567", email: null},
        sessions: []
    };
}

---

## 5. Авто-освобождение ПК

Функция update_sessions(db) вызывается при каждом GET-запросе /pcs и /book.
Проверяет все активные сессии: если текущее время >= end_time, сессия завершается:
- session.is_active = False
- pc.is_busy = False
- pc.session_end = None
- pc.current_user_id = None
