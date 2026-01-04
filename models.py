from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)

    # Связь с сообщениями: один пользователь может иметь много сообщений
    messages = relationship("ChatMessage", back_populates="user")

class Poem(Base):
    __tablename__ = "poems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    content = Column(Text)
    
    # Связь с сообщениями: к одному стиху может быть много сообщений
    messages = relationship("ChatMessage", back_populates="poem")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poem_id = Column(Integer, ForeignKey("poems.id"))
    role = Column(String)  # 'user' или 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Обратные связи, чтобы было удобно доставать данные
    user = relationship("User", back_populates="messages")
    poem = relationship("Poem", back_populates="messages")
    
