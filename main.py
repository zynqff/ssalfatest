from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal, get_db
from routers import poems, auth
import models

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Poetry AI Project")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(poems.router)
app.include_router(auth.router)

@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    if not db.query(models.Poem).first():
        p1 = models.Poem(title="Анчар", author="А.С. Пушкин", text="В пустыне чахлой и скупой...")
        p2 = models.Poem(title="Ночь, улица, фонарь...", author="А. Блок", text="Ночь, улица, фонарь, аптека...")
        db.add_all([p1, p2])
        db.commit()
    db.close()

@app.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    items = db.query(models.Poem).all()
    user = db.query(models.User).first() # Заглушка текущего юзера
    read_list = json.loads(user.read_poems_json) if user else []
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "poems": items,
        "read_list": read_list,
        "pinned": user.pinned_poem_title if user else None
    })
                    
