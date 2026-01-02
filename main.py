import json
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import models
from database import engine, Base, SessionLocal, get_db
from routers import poems, auth

# ВАЖНО: Эта строка создает таблицы при каждом запуске, если их нет
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Poetry AI Project")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(poems.router)
app.include_router(auth.router)

@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    # Проверка наличия стихов
    if not db.query(models.Poem).first():
        p1 = models.Poem(title="Анчар", author="А.С. Пушкин", text="В пустыне чахлой и скупой...")
        db.add(p1)
        db.commit()
    db.close()

@app.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    items = db.query(models.Poem).all()
    user = db.query(models.User).first() 
    read_list = json.loads(user.read_poems_json) if user and user.read_poems_json else []
    pinned = user.pinned_poem_title if user else None
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "poems": items,
        "read_list": read_list,
        "pinned": pinned
    })

@app.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user_data": user.user_data,
        "show_all_tab": user.show_all_tab
    })

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

