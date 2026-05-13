import re
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, Column, Integer, Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

# === Валидация ===
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^[\d\s\-\+\(\)]{5,20}$")
DIGITS_REGEX = re.compile(r"\d")

def validate_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))

def validate_phone(phone: str) -> bool:
    """Проверяет, что телефон содержит только цифры, пробелы, +, -, () и минимум 5 цифр."""
    if not PHONE_REGEX.match(phone):
        return False
    # Проверяем, что есть хотя бы 5 цифр
    digits = DIGITS_REGEX.findall(phone)
    return len(digits) >= 5

# === DB настройка ===
DATABASE_URL = "sqlite:///./club.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# === МОДЕЛИ ===

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)

    sessions = relationship("Session", back_populates="user")


class Computer(Base):
    __tablename__ = "computers"

    id = Column(Integer, primary_key=True, index=True)
    is_busy = Column(Boolean, default=False)
    session_end = Column(DateTime, nullable=True)
    current_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    current_user = relationship("User")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pc_id = Column(Integer, ForeignKey("computers.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=False)
    hours = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="sessions")
    pc = relationship("Computer")


Base.metadata.create_all(bind=engine)


def init_computers():
    db = SessionLocal()
    if db.query(Computer).count() == 0:
        for i in range(10):
            db.add(Computer())
        db.commit()
    db.close()


init_computers()


def update_sessions(db):
    now = datetime.now()
    active_sessions = db.query(Session).filter(Session.is_active == True).all()

    for session in active_sessions:
        if now >= session.end_time:
            session.is_active = False
            pc = db.query(Computer).filter(Computer.id == session.pc_id).first()
            if pc:
                pc.is_busy = False
                pc.session_end = None
                pc.current_user_id = None

    db.commit()


# === API ===

@app.get("/pcs")
def get_pcs():
    db = SessionLocal()
    update_sessions(db)

    pcs = db.query(Computer).all()
    result = []

    for pc in pcs:
        user_info = None
        if pc.current_user:
            user_info = {
                "name": pc.current_user.name,
                "phone": pc.current_user.phone,
                "email": pc.current_user.email
            }

        result.append({
            "id": pc.id,
            "is_busy": pc.is_busy,
            "session_end": pc.session_end.isoformat() if pc.session_end else None,
            "user": user_info
        })

    db.close()
    return result


@app.post("/book/{pc_id}")
def book_pc(
    pc_id: int,
    hours: float,
    name: str = Query(...),
    phone: str = Query(...),
    email: str = Query(None)
):
    # Валидация телефона
    if not validate_phone(phone.strip()):
        raise HTTPException(
            status_code=400,
            detail="Некорректный номер телефона. Используйте цифры, пробелы, +, -, (). Минимум 5 цифр."
        )

    # Валидация email
    if email and email.strip() != "":
        if not validate_email(email.strip()):
            raise HTTPException(
                status_code=400,
                detail="Некорректный email. Пример: user@mail.ru"
            )

    db = SessionLocal()
    update_sessions(db)

    pc = db.query(Computer).filter(Computer.id == pc_id).first()

    if not pc:
        db.close()
        raise HTTPException(status_code=404, detail="ПК не найден")

    if pc.is_busy:
        db.close()
        raise HTTPException(status_code=400, detail="ПК уже занят")

    phone_clean = phone.strip()

    # Ищем или создаём пользователя
    user = db.query(User).filter(User.phone == phone_clean).first()
    if not user:
        user = User(name=name.strip(), phone=phone_clean, email=email.strip() if email and email.strip() else None)
        db.add(user)
        db.commit()
        # НЕ делаем refresh — просто получаем id сразу после commit
        user_id = user.id
    else:
        user.name = name.strip()
        if email and email.strip():
            user.email = email.strip()
        db.commit()
        user_id = user.id

    # Создаём сессию
    session_end = datetime.now() + timedelta(hours=hours)
    session = Session(
        user_id=user_id,
        pc_id=pc.id,
        end_time=session_end,
        hours=hours
    )
    db.add(session)

    # Обновляем ПК
    pc.is_busy = True
    pc.session_end = session_end
    pc.current_user_id = user_id

    db.commit()
    db.close()

    return {
        "message": f"ПК {pc_id} забронирован для {name.strip()}",
        "user_id": user_id
    }


@app.post("/end/{pc_id}")
def end_session(pc_id: int):
    db = SessionLocal()

    pc = db.query(Computer).filter(Computer.id == pc_id).first()

    if not pc:
        raise HTTPException(status_code=404, detail="ПК не найден")

    active_session = db.query(Session).filter(
        Session.pc_id == pc_id,
        Session.is_active == True
    ).first()

    if active_session:
        active_session.is_active = False
        active_session.end_time = datetime.now()

    pc.is_busy = False
    pc.session_end = None
    pc.current_user_id = None

    db.commit()
    db.close()

    return {"message": f"Сессия ПК {pc_id} завершена"}


@app.get("/history")
def get_history(phone: str = Query(...)):
    db = SessionLocal()

    user = db.query(User).filter(User.phone == phone.strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    sessions = db.query(Session).filter(
        Session.user_id == user.id
    ).order_by(Session.start_time.desc()).all()

    result = []
    for s in sessions:
        result.append({
            "id": s.id,
            "pc_id": s.pc_id,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "hours": s.hours,
            "is_active": s.is_active
        })

    db.close()
    return {
        "user": {"name": user.name, "phone": user.phone, "email": user.email},
        "sessions": result
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
