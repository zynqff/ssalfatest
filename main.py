from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from routers import auth, poems, users, admin
from dependencies import get_current_user

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Poetry AI Portal")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключаем модули из папки routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(poems.router, prefix="/poem", tags=["Poems"])
app.include_router(users.router, tags=["Users"]) # Профиль пользователя
app.include_router(admin.router) # Панель администратора

@app.get("/")
async def index_page(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    all_poems = db.query(models.Poem).all()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "poems": all_poems, 
        "user": current_user
    })
        
