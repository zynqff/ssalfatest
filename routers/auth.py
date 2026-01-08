from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from security import hash_password, verify_password # Используем твой security.py

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_handler(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register_handler(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Проверяем уникальность логина
    if db.query(models.User).filter(models.User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Этот логин уже занят"})
    
    # Проверяем, есть ли уже пользователи в базе
    is_first_user = db.query(models.User).first() is None

    # Создаем нового пользователя
    new_user = models.User(
        username=username, 
        hashed_password=hash_password(password),
        is_admin=is_first_user # Если это первый пользователь, он становится админом
    )
    db.add(new_user)
    db.commit()
    
    # Перенаправляем на страницу входа после успешной регистрации
    return RedirectResponse(url="/auth/login?registered=true", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login")
    response.delete_cookie("user_id")
    return response
        
