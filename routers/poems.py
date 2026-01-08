from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from database import get_db
from ai_service import analyze_poem_with_chat_stream
import models, schemas
from dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/poem/{poem_id}")
async def poem_detail(
    request: Request,
    poem_id: int, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    new_chat_requested = request.query_params.get('new_chat') == 'true'

    if not user:
        poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
        if not poem:
            raise HTTPException(status_code=404, detail="Poem not found")
        return templates.TemplateResponse("poem_detail.html", {"request": request, "poem": poem, "user": None})

    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")

    # Ищем сессию для этого чата
    current_session = None
    if not new_chat_requested:
        current_session = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == user.id,
            models.ChatSession.poem_id == poem.id
        ).order_by(models.ChatSession.created_at.desc()).first()

    # Если сессия не найдена или запрошена новая, создаем ее
    if not current_session:
        current_session = models.ChatSession(user_id=user.id, poem_id=poem.id)
        db.add(current_session)
        db.commit()
        db.refresh(current_session)

    # Загружаем сообщения для текущей сессии
    chat_history = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == current_session.id
    ).order_by(models.ChatMessage.created_at.asc()).all()

    # Получаем ВСЕ сессии пользователя для истории
    all_user_sessions = db.query(models.ChatSession).options(
        joinedload(models.ChatSession.poem)
    ).filter(
        models.ChatSession.user_id == user.id
    ).order_by(models.ChatSession.created_at.desc()).all()

    return templates.TemplateResponse("poem_detail.html", {
        "request": request, 
        "poem": poem, 
        "user": user, 
        "session_id": current_session.id,
        "all_user_sessions": all_user_sessions,
        "current_chat_history": chat_history
    })

@router.post("/ai-ask")
async def ask_ai(
    data: schemas.ChatQuestion, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Сначала войдите в систему.")

    session = db.query(models.ChatSession).options(
        joinedload(models.ChatSession.poem)
    ).filter(
        models.ChatSession.id == data.session_id,
        models.ChatSession.user_id == user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    history = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == data.session_id
    ).order_by(models.ChatMessage.created_at.asc()).all()

    db.add(models.ChatMessage(session_id=data.session_id, role="user", content=data.question))
    db.commit()

    def save_and_stream():
        full_response = ""
        answer_stream = analyze_poem_with_chat_stream(session.poem.content, data.question, history)
        
        for chunk in answer_stream:
            full_response += chunk
            yield chunk
        
        db.add(models.ChatMessage(session_id=data.session_id, role="model", content=full_response))
        db.commit()

    return StreamingResponse(save_and_stream(), media_type="text/event-stream")

@router.get("/chat/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)

    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session_id
    ).join(models.ChatSession).filter(
        models.ChatSession.user_id == user.id
    ).order_by(models.ChatMessage.created_at.asc()).all()

    if not messages:
        # Проверяем, существует ли сессия, даже если в ней нет сообщений
        session_exists = db.query(models.ChatSession).filter_by(id=session_id, user_id=user.id).first()
        if not session_exists:
            raise HTTPException(status_code=404, detail="Chat history not found")
        return JSONResponse(content=[])

    return [{"role": msg.role, "content": msg.content} for msg in messages]

    
