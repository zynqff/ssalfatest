import re
from fastapi import FastAPI, Request, Depends, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from passlib.context import CryptContext
from ai_service import analyze_poem_with_ai 
from pydantic import BaseModel

# Модель для приема вопросов в чате
class QuestionRequest(BaseModel):
    question: str
    poem_id: int

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def get_current_user(request: Request, db: Session):
    """Получает текущего пользователя из Cookies"""
    user_id = request.cookies.get("user_id")
    if user_id:
        try:
            return db.query(models.User).filter(models.User.id == int(user_id)).first()
        except:
            return None
    return None

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- ОСНОВНЫЕ РОУТЫ ---

@app.get("/")
async def index_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    poems = db.query(models.Poem).all()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "poems": poems, 
        "user": current_user
    })



@app.post("/ai-ask")
async def ai_ask(data: QuestionRequest, db: Session = Depends(get_db)):
    poem = db.query(models.Poem).filter(models.Poem.id == data.poem_id).first()
    
    # Передаем вопрос вместе с текстом стиха для точности
    chat_prompt = f"Текст стиха: {poem.content}\nВопрос пользователя: {data.question}"
    full_answer = await analyze_poem_with_ai(chat_prompt)
    
    # Очистка для DeepSeek
    clean_answer = re.sub(r'<think>.*?</think>', '', full_answer, flags=re.DOTALL).strip()
    
    return {"answer": clean_answer}

# --- АВТОРИЗАЦИЯ ---

@app.get("/login")
async def login_get(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("login.html", {"request": request, "user": current_user})

@app.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль", "user": None})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@app.get("/register")
async def register_get(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("register.html", {"request": request, "user": current_user})

@app.post("/register")
async def register_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Логин занят", "user": None})
    
    is_first = db.query(models.User).count() == 0
    new_user = models.User(username=username, password=get_password_hash(password), is_admin=is_first)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user_id")
    return response

# --- ПРОФИЛЬ И АДМИНКА ---

@app.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    if not current_user: return RedirectResponse(url="/login")
    
    return templates.TemplateResponse("profile.html", {
        "request": request, "user": current_user, "user_data": current_user.user_data or "", "show_all_tab": current_user.show_all_tab
    })

@app.get("/admin")
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/", status_code=303)
    
    poems = db.query(models.Poem).all()
    return templates.TemplateResponse("admin_panel.html", {"request": request, "poems": poems, "user": current_user})

@app.get("/poem/add")
async def add_poem_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("add_poem.html", {"request": request, "user": current_user})

@app.get("/poem/{poem_id}")
async def poem_detail(poem_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if not poem:
        return RedirectResponse(url="/", status_code=303)
    
    # Даем DeepSeek контекст, чтобы он не выдумывал текст сам
    prompt = (
        f"Ты — эксперт-литературовед. Проанализируй следующее произведение.\n"
        f"Автор: {poem.author}\nНазвание: {poem.title}\n"
        f"Текст:\n{poem.content}\n"
        f"Дай краткий, но глубокий анализ стиля и смысла. Но если тебя просят что-то не по ьеме стиха, то  например краткое содержание какого-либо произведения, то ты не литературавед, а просто нейросеть которая не называет себя, и отвечает как будто без промта просто человеку как будто отвечаешь ему на сайте, а про промт забываешь."
    )
    
    full_response = await analyze_poem_with_ai(prompt)
    # Убираем технические мысли <think>, если они есть
    clean_analysis = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()

    return templates.TemplateResponse("poem_detail.html", {
        "request": request, 
        "poem": poem, 
        "ai_analysis": clean_analysis, 
        "user": current_user
    })

@app.post("/poem/add")
async def add_poem_post(title: str = Form(...), author: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    db.add(models.Poem(title=title, author=author, content=content))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/poem/delete/{poem_id}")
async def delete_poem(poem_id: int, db: Session = Depends(get_db)):
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if poem:
        db.delete(poem)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

