from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from routers import auth, poems

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Poetry AI Portal")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

async def get_current_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    if user_id:
        return db.query(models.User).filter(models.User.id == int(user_id)).first()
    return None

# Подключаем модули из папки routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(poems.router, prefix="/poem", tags=["Poems"])

@app.get("/")
async def index_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    all_poems = db.query(models.Poem).all()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "poems": all_poems, 
        "user": current_user
    })
        
