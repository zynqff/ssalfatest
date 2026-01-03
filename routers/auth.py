from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from passlib.context import CryptContext

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

router = APIRouter()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- РОУТЕРЫ ---

# 1. Вход (POST)
@router.post("/login")
async def login(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    # Проверка пользователя и пароля
    if not user or not verify_password(password, user.password):
        # Возвращаем страницу ЛОГИНА с красивой ошибкой
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверный логин или пароль"
        })

    # Если всё ок — логиним (здесь должна быть твоя логика сессий или куки)
    response = Response(status_code=303)
    response.headers["Location"] = "/"
    response.set_cookie(key="user_id", value=str(user.id)) # Упрощенный пример
    return response

# 2. Регистрация (POST)
@router.post("/register")
async def register(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Проверяем, не занят ли логин
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Этот логин уже занят"
        })

    # Создаем нового пользователя
    hashed_pass = get_password_hash(password)
    new_user = models.User(username=username, password=hashed_pass)
    db.add(new_user)
    db.commit()

    # После успешной регистрации отправляем на логин с пометкой об успехе (по желанию)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Регистрация успешна! Теперь войдите." # Используем то же поле для сообщения
    })
    
