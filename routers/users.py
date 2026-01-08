from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from security import hash_password
import models
from dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile")
async def profile_page(request: Request, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Модель User не содержит поля user_data, поэтому оно не передается в шаблон
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.post("/profile") # Изменяем URL для соответствия форме
async def update_profile(
    request: Request,
    new_password: str = Form(None),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if new_password:
        # Добавим проверку на минимальную длину пароля
        if len(new_password) < 4:
            return templates.TemplateResponse("profile.html", {
                "request": request, 
                "user": user, 
                "error": "Пароль должен быть не менее 4 символов"
            })
        user.hashed_password = hash_password(new_password)
        db.add(user)
        db.commit()
    
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

