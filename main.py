from fastapi import FastAPI, Request, Depends, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from passlib.context import CryptContext

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

# --- РОУТЫ ---

@app.get("/")
async def index_page(request: Request, db: Session = Depends(get_db)):
    poems = db.query(models.Poem).all()
    return templates.TemplateResponse("index.html", {"request": request, "poems": poems})

@app.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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
            "error": "Неверный логин или пароль"
        })
    
    # Успешный вход (ставим временную куку для примера)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@app.get("/register")
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_post(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        # Проверка на существование пользователя
        existing_user = db.query(models.User).filter(models.User.username == username).first()
        if existing_user:
            return templates.TemplateResponse("register.html", {
                "request": request, 
                "error": "Этот логин уже занят"
            })

        # Создание нового пользователя с хешированием
        new_user = models.User(
            username=username, 
            password=get_password_hash(password)
        )
        db.add(new_user)
        db.commit()
        
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Регистрация успешна! Теперь войдите."
        })
        
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Ошибка базы данных. Попробуйте другой логин."
        })

@app.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db)):
    # Простейшая проверка авторизации через куку
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")
        
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user_data": user.user_data if user else "",
        "show_all_tab": user.show_all_tab if user else True
    })

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user_id")
    return response
                                                        
