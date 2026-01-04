from sqlalchemy import Column, Integer, String, Text, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    # Поле для данных профиля "О себе"
    user_data = Column(Text, default="")
    # Настройка отображения вкладок
    show_all_tab = Column(Boolean, default=False)
    # Роль администратора (первый зарегистрированный получит True)
    is_admin = Column(Boolean, default=False)

class Poem(Base):
    __tablename__ = "poems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True) # Поле автора
    content = Column(Text)              # Поле текста (теперь без ошибок)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poem_id = Column(Integer, ForeignKey("poems.id"))
    role = Column(String)  # "user" или "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
