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

class QuestionRequest(BaseModel):
    question: str
    poem_id: int

# Инициализация базы данных
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def get_current_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    if user_id:
        return db.query(models.User).filter(models.User.id == int(user_id)).first()
    return None

# --- РОУТЫ ---

@app.get("/")
async def index_page(request: Request, db: Session = Depends(get_db)):
    poems = db.query(models.Poem).all()
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "poems": poems, 
        "user": current_user 
    })

@app.get("/login")
async def login_get(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("login.html", {"request": request, "user": current_user})

@app.post("/login")
async def login_post(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Неверный логин или пароль",
            "user": None
        })
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@app.get("/register")
async def register_get(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("register.html", {"request": request, "user": current_user})

@app.post("/register")
async def register_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user_count = db.query(models.User).count()
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Этот логин уже занят", "user": None})

    new_user = models.User(
        username=username, 
        password=get_password_hash(password),
        is_admin=(user_count == 0)
    )
    db.add(new_user)
    db.commit()
    return templates.TemplateResponse("login.html", {"request": request, "error": "Регистрация успешна!", "msg_type": "success", "user": None})

@app.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login")
        
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": current_user,
        "user_data": current_user.user_data or "",
        "show_all_tab": current_user.show_all_tab
    })

@app.post("/profile/update")
async def update_profile(
    request: Request, 
    user_data: str = Form(""), 
    new_password: str = Form(""), 
    show_all_tab: bool = Form(False), 
    db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    current_user.user_data = user_data
    current_user.show_all_tab = show_all_tab
    if new_password.strip():
        current_user.password = get_password_hash(new_password)
    db.commit()

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "user_data": current_user.user_data,
        "show_all_tab": current_user.show_all_tab,
        "error": "Изменения сохранены!"
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

@app.post("/poem/add")
async def add_poem_post(title: str = Form(...), author: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    new_poem = models.Poem(title=title, author=author, content=content)
    db.add(new_poem)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/poem/edit/{poem_id}")
async def edit_poem_page(poem_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    return templates.TemplateResponse("add_poem.html", {"request": request, "user": current_user, "poem": poem, "edit_mode": True})

@app.get("/poem/delete/{poem_id}")
async def delete_poem(poem_id: int, db: Session = Depends(get_db)):
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if poem:
        db.delete(poem)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/poem/{poem_id}")
async def poem_detail(poem_id: int, request: Request, db: Session = Depends(get_db)):
    poem = db.query(models.Poem).filter(models.Poem.id == poem_id).first()
    if not poem: return "Стих не найден", 404
    
    current_user = await get_current_user(request, db)
    ai_response = await analyze_poem_with_ai(f"Проанализируй: {poem.content}")

    return templates.TemplateResponse("poem_detail.html", {
        "request": request, "poem": poem, "ai_analysis": ai_response, "user": current_user
    })

@app.post("/ai-ask")
async def ai_ask(data: QuestionRequest, db: Session = Depends(get_db)):
    poem = db.query(models.Poem).filter(models.Poem.id == data.poem_id).first()
    answer = await analyze_poem_with_ai(f"Стих: {poem.content}\nВопрос: {data.question}") 
    return {"answer": answer}

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user_id")
    return response
                     
