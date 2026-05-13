from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

# === DB настройка ===
DATABASE_URL = "sqlite:///./club.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# === МОДЕЛЬ ===
class Computer(Base):
    __tablename__ = "computers"

    id = Column(Integer, primary_key=True, index=True)
    is_busy = Column(Boolean, default=False)
    session_end = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)

# === ИНИЦИАЛИЗАЦИЯ ПК ===
def init_computers():
    db = SessionLocal()
    if db.query(Computer).count() == 0:
        for i in range(10):
            db.add(Computer())
        db.commit()
    db.close()

init_computers()

# === ОБНОВЛЕНИЕ СЕССИЙ ===
def update_sessions(db):
    pcs = db.query(Computer).all()
    now = datetime.now()

    for pc in pcs:
        if pc.is_busy and pc.session_end and now >= pc.session_end:
            pc.is_busy = False
            pc.session_end = None

    db.commit()

# === API ===

@app.get("/pcs")
def get_pcs():
    db = SessionLocal()
    update_sessions(db)

    pcs = db.query(Computer).all()
    result = []

    for pc in pcs:
        result.append({
            "id": pc.id,
            "is_busy": pc.is_busy,
            "session_end": pc.session_end
        })

    db.close()
    return result


@app.post("/book/{pc_id}")
def book_pc(pc_id: int, hours: float):
    db = SessionLocal()
    update_sessions(db)

    pc = db.query(Computer).filter(Computer.id == pc_id).first()

    if not pc:
        raise HTTPException(status_code=404, detail="ПК не найден")

    if pc.is_busy:
        raise HTTPException(status_code=400, detail="ПК уже занят")

    pc.is_busy = True
    pc.session_end = datetime.now() + timedelta(hours=hours)

    db.commit()
    db.close()

    return {"message": f"ПК {pc_id} забронирован"}


@app.post("/end/{pc_id}")
def end_session(pc_id: int):
    db = SessionLocal()

    pc = db.query(Computer).filter(Computer.id == pc_id).first()

    if not pc:
        raise HTTPException(status_code=404, detail="ПК не найден")

    pc.is_busy = False
    pc.session_end = None

    db.commit()
    db.close()

    return {"message": f"Сессия ПК {pc_id} завершена"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )