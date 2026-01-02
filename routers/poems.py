from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
import models
import json
from ai_service import analyze_poem_with_ai

router = APIRouter(prefix="/poems", tags=["Стихи"])

@router.get("/all")
async def get_all_poems(db: Session = Depends(get_db)):
    return db.query(models.Poem).all()

@router.post("/ask")
async def ask_ai(payload: dict = Body(...), db: Session = Depends(get_db)):
    poem_id = payload.get("poem_id")
    question = payload.get("question")
    
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if not poem:
        raise HTTPException(status_code=404, detail="Стихотворение не найдено")

    # Формируем расширенный промпт для чата
    prompt = f"""
    Ты — литературный критик. 
    Стихотворение: "{poem.title}" (Автор: {poem.author}).
    Текст: {poem.text}
    
    Вопрос пользователя: {question}
    Отвечай аргументированно и глубоко на русском языке.
    """
    answer = await analyze_poem_with_ai(prompt)
    return {"answer": answer}

@router.post("/toggle_read")
async def toggle_read(payload: dict = Body(...), db: Session = Depends(get_db)):
    title = payload.get("title")
    # В этой версии берем первого пользователя для простоты, 
    # в будущем добавьте current_user через JWT
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    reads = json.loads(user.read_poems_json)
    if title in reads:
        reads.remove(title)
        status = "unmarked"
    else:
        reads.append(title)
        status = "marked"
    
    user.read_poems_json = json.dumps(reads)
    db.commit()
    return {"success": True, "status": status}

@router.post("/toggle_pin")
async def toggle_pin(payload: dict = Body(...), db: Session = Depends(get_db)):
    title = payload.get("title")
    user = db.query(models.User).first()
    
    if user.pinned_poem_title == title:
        user.pinned_poem_title = None
        status = "unpinned"
    else:
        user.pinned_poem_title = title
        status = "pinned"
        
    db.commit()
    return {"success": True, "status": status}
    
