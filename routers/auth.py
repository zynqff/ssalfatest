from fastapi import APIRouter, Depends, HTTPException, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from security import hash_password, verify_password, create_access_token

router = APIRouter(tags=["Auth"])

@router.post("/register")
async def register(
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # 1. Проверяем, существует ли пользователь
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        # Вместо 500 ошибки выдаем понятную 400
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    try:
        # 2. Создаем нового пользователя с начальными значениями
        new_user = models.User(
            username=username, 
            password_hash=hash_password(password),
            read_poems_json="[]",  # Инициализируем пустым JSON-списком
            user_data="Новый пользователь",
            show_all_tab=True
        )
        db.add(new_user)
        db.commit()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        db.rollback()
        print(f"Ошибка при регистрации: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения в базу данных")

@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    token = create_access_token(data={"sub": user.username})
    
    res = RedirectResponse(url="/", status_code=303)
    # Устанавливаем токен в куки
    res.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return res

@router.get("/logout")
async def logout():
    res = RedirectResponse(url="/login", status_code=302)
    res.delete_cookie("access_token")
    return res
        
