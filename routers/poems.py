from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from ai_service import analyze_poem_with_chat
import models, schemas
from dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/{poem_id}")
async def poem_detail(
    request: Request,
    poem_id: int, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")
    
    # Загружаем историю из ChatMessage
    history = []
    if user:
        history = db.query(models.ChatMessage).filter(
            models.ChatMessage.poem_id == poem_id,
            models.ChatMessage.user_id == user.id
        ).order_by(models.ChatMessage.created_at.asc()).all()

    return templates.TemplateResponse("poem_detail.html", {
        "request": request, "poem": poem, "user": user, "chat_history": history
    })

@router.post("/ai-ask")
async def ask_ai(
    data: schemas.ChatQuestion, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Сначала войдите в систему.")

    poem = db.query(models.Poem).filter(models.Poem.id == data.poem_id).first()
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    history = db.query(models.ChatMessage).filter(
        models.ChatMessage.poem_id == data.poem_id,
        models.ChatMessage.user_id == user.id
    ).all()

    # 1. Сохраняем вопрос пользователя
    db.add(models.ChatMessage(user_id=user.id, poem_id=data.poem_id, role="user", content=data.question))
    
    # 2. Получаем ответ от Gemini
    answer = await analyze_poem_with_chat(poem.content, data.question, history)

    # 3. Сохраняем ответ ИИ (Gemini использует роль 'model')
    db.add(models.ChatMessage(user_id=user.id, poem_id=data.poem_id, role="model", content=answer))
    db.commit()

    return {"answer": answer}
    
