from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from ai_service import analyze_poem_with_chat # Твой новый ИИ сервис
import models, schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def get_user_from_request(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    return db.query(models.User).filter(models.User.id == int(user_id)).first() if user_id else None

@router.get("/{poem_id}")
async def poem_detail(poem_id: int, request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_request(request, db)
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    
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
async def ask_ai(data: schemas.ChatQuestion, request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_request(request, db)
    if not user:
        return {"answer": "Сначала войдите в систему."}

    poem = db.query(models.Poem).filter(models.Poem.id == data.poem_id).first()
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
    
