from fastapi import APIRouter, Depends, HTTPException, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from security import hash_password, verify_password, create_access_token #

router = APIRouter(tags=["Auth"])

@router.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password_hash): #
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    token = create_access_token(data={"sub": user.username}) #
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token") #
    return response

@router.post("/profile/update")
async def update_profile(
    user_data: str = Form(None), 
    show_all_tab: bool = Form(False), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).first() # Пример
    user.user_data = user_data
    user.show_all_tab = show_all_tab
    db.commit()
    return RedirectResponse(url="/", status_code=303)
