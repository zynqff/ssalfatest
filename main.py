from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from routers import poems, auth
import models

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(poems.router)
app.include_router(auth.router)

@app.get("/")
async def home(request: Request, db: Session = Depends(SessionLocal)):
    all_poems = db.query(models.Poem).all()
    return templates.TemplateResponse("index.html", {"request": request, "poems": all_poems})
