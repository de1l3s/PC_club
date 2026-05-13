Архитектура системы Cyber Club

Диаграмма компонентов (PlantUML)

```plantuml
@startuml
skinparam componentStyle rectangle
skinparam backgroundColor #FFFFFF

title Диаграмма компонентов Cyber Club

package "Клиент (Браузер)" {
    [index.html] as html
    [style.css] as css
    [script.js] as js
    html ..> js
    css ..> html
}

package "Сервер (FastAPI)" {
    [main.py] as api
    [update_sessions()] as updater
    [SQLite (club.db)] as db
    api ..> updater
    api ..> db
    updater ..> db
}

js -down-> api : HTTP Fetch

note right of js
  loadPCs()
  bookPC(id)
  endSession(id)
  setInterval 5 сек
end note

note bottom of db
  computers: id, is_busy, session_end
end note

@enduml
```

Описание связей

| Компонент | Связь | Компонент | Протокол |
|-----------|-------|-----------|----------|
| script.js | вызывает | main.py | HTTP Fetch API |
| main.py | читает/пишет | computers | SQL (SQLAlchemy) |
| main.py | вызывает | update_sessions() | Прямой вызов |
| update_sessions() | обновляет | computers | SQL (SQLAlchemy) |

Схема базы данных

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Первичный ключ |
| is_busy | BOOLEAN | Занят ли ПК (по умолчанию False) |
| session_end | DATETIME | Время окончания брони (NULL если свободен) |

Соответствие имён диаграммы и кода

| На диаграмме | В коде | Файл |
|-------------|--------|------|
| script.js / loadPCs() | async function loadPCs() | static/script.js |
| script.js / bookPC() | async function bookPC(id) | static/script.js |
| script.js / endSession() | async function endSession(id) | static/script.js |
| main.py (GET /pcs) | @app.get("/pcs") def get_pcs() | main.py |
| main.py (POST /book) | @app.post("/book/{pc_id}") def book_pc() | main.py |
| main.py (POST /end) | @app.post("/end/{pc_id}") def end_session() | main.py |
| update_sessions() | def update_sessions(db) | main.py |
| computers | class Computer(Base) | main.py |
