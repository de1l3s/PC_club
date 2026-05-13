# Контракты взаимодействия (API Contracts)

## 1. Получение списка ПК

**Прототип:**
```python
@app.get("/pcs")
def get_pcs() -> List[dict]
```

**Формат ответа:**
```json
[
  {"id": 1, "is_busy": false, "session_end": null},
  {"id": 2, "is_busy": true, "session_end": "2025-05-20T15:00:00"}
]
```

**Заглушка для фронтенда:**
```javascript
const mockPCs = [
    {id: 1, is_busy: false, session_end: null},
    {id: 2, is_busy: true, session_end: "2025-05-20T15:00:00"}
];
```

---

## 2. Бронирование ПК

**Прототип:**
```python
@app.post("/book/{pc_id}")
def book_pc(pc_id: int, hours: float) -> dict
```

**Параметры:**
- `pc_id` (int) — из URL
- `hours` (float) — query-параметр

**Формат ответа (успех):**
```json
{"message": "ПК 1 забронирован"}
```

**Возможные ошибки:**
- 404: ПК не найден
- 400: ПК уже занят

**Заглушка:**
```javascript
async function bookPCMock(id, hours) {
    return {message: `ПК ${id} забронирован`};
}
```

---

## 3. Завершение сессии

**Прототип:**
```python
@app.post("/end/{pc_id}")
def end_session(pc_id: int) -> dict
```

**Формат ответа:**
```json
{"message": "Сессия ПК 3 завершена"}
```

**Возможные ошибки:**
- 404: ПК не найден

**Заглушка:**
```javascript
async function endSessionMock(id) {
    return {message: `Сессия ПК ${id} завершена`};
}
```
