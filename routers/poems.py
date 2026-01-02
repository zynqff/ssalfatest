from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
import models
import json
from ai_service import analyze_poem_with_ai

router = APIRouter(prefix="/poems", tags=["Стихи"])

@router.post("/ask")
async def ask_ai(payload: dict = Body(...), db: Session = Depends(get_db)):
    poem_id = payload.get("poem_id")
    question = payload.get("question")
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    
    prompt = f"Стихотворение: {poem.title}\nАвтор: {poem.author}\nТекст: {poem.text}\n\nВопрос: {question}"
    answer = await analyze_poem_with_ai(prompt)
    return {"answer": answer}

@router.post("/toggle_read")
async def toggle_read(payload: dict = Body(...), db: Session = Depends(get_db)):
    title = payload.get("title")
    user = db.query(models.User).first() # В будущем заменить на текущего юзера
    reads = json.loads(user.read_poems_json)
    if title in reads: reads.remove(title)
    else: reads.append(title)
    user.read_poems_json = json.dumps(reads)
    db.commit()
    return {"success": True}
