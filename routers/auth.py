from fastapi import APIRouter, Depends, HTTPException, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import models
# Исправленный импорт (без core.)
from security import hash_password, verify_password, create_access_token

router = APIRouter(tags=["Auth"])

@router.post("/register")
async def register(
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    new_user = models.User(username=username, password_hash=hash_password(password))
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

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
    res.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return res

@router.get("/logout")
async def logout():
    res = RedirectResponse(url="/login", status_code=302)
    res.delete_cookie("access_token")
    return res

@router.post("/profile/update")
async def update_profile(
    user_data: str = Form(None),
    show_all_tab: bool = Form(False),
    new_password: str = Form(None),
    db: Session = Depends(get_db)
):
    # Временно берем первого юзера
    user = db.query(models.User).first()
    if not user:
        return RedirectResponse(url="/login")

    if new_password and len(new_password) >= 4:
        user.password_hash = hash_password(new_password)
    
    user.user_data = user_data if user_data is not None else user.user_data
    user.show_all_tab = show_all_tab
    
    db.commit()
    return RedirectResponse(url="/profile", status_code=303)
    
