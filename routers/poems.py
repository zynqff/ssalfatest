from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from ai_service import analyze_poem_with_chat
import models, schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def get_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    return db.query(models.User).filter(models.User.id == int(user_id)).first() if user_id else None

@router.get("/{poem_id}")
async def poem_detail(poem_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = await get_user(request, db)
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    
    # Загружаем историю сообщений для конкретного стиха и пользователя
    history = []
    if current_user:
        history = db.query(models.ChatMessage).filter(
            models.ChatMessage.poem_id == poem_id,
            models.ChatMessage.user_id == current_user.id
        ).order_by(models.ChatMessage.created_at.asc()).all()

    return templates.TemplateResponse("poem_detail.html", {
        "request": request, "poem": poem, "user": current_user, "chat_history": history
    })

@router.post("/ai-ask")
async def ask_ai(data: schemas.ChatQuestion, request: Request, db: Session = Depends(get_db)):
    current_user = await get_user(request, db)
    if not current_user:
        return {"answer": "Пожалуйста, войдите в систему."}

    poem = db.query(models.Poem).filter(models.Poem.id == data.poem_id).first()
    
    # Получаем историю для Gemini
    history = db.query(models.ChatMessage).filter(
        models.ChatMessage.poem_id == data.poem_id,
        models.ChatMessage.user_id == current_user.id
    ).all()

    # Сохраняем вопрос пользователя
    db.add(models.ChatMessage(user_id=current_user.id, poem_id=data.poem_id, role="user", content=data.question))
    
    # Запрос к Gemini
    answer = await analyze_poem_with_chat(poem.content, data.question, history)

    # Сохраняем ответ ИИ
    db.add(models.ChatMessage(user_id=current_user.id, poem_id=data.poem_id, role="model", content=answer))
    db.commit()

    return {"answer": answer}

@router.post("/add")
async def add_poem(title: str = Form(...), author: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    db.add(models.Poem(title=title, author=author, content=content))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)
    
