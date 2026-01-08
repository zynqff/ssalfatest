from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from dependencies import get_current_admin_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin_user)] # Все роуты здесь требуют админа
)

templates = Jinja2Templates(directory="templates")

@router.get("")
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    poems = db.query(models.Poem).all()
    return templates.TemplateResponse("admin_panel.html", {"request": request, "poems": poems})

@router.get("/poem/add")
async def add_poem_form(request: Request):
    return templates.TemplateResponse("add_poem.html", {"request": request, "edit_mode": False})

@router.post("/poem/add")
async def add_poem(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    new_poem = models.Poem(title=title, author=author, content=content)
    db.add(new_poem)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/poem/edit/{poem_id}")
async def edit_poem_form(request: Request, poem_id: int, db: Session = Depends(get_db)):
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")
    return templates.TemplateResponse("add_poem.html", {"request": request, "poem": poem, "edit_mode": True})

@router.post("/poem/edit/{poem_id}")
async def edit_poem(
    request: Request,
    poem_id: int,
    title: str = Form(...),
    author: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")
    
    poem.title = title
    poem.author = author
    poem.content = content
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/poem/delete/{poem_id}")
async def delete_poem(poem_id: int, db: Session = Depends(get_db)):
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if poem:
        db.delete(poem)
        db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
