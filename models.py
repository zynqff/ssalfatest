from sqlalchemy import Column, Integer, String, Text, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password_hash = Column(String)
    user_data = Column(Text, default="Это ваша личная информация.")
    read_poems_json = Column(Text, default='[]') 
    is_admin = Column(Boolean, default=False)
    pinned_poem_title = Column(String, nullable=True)
    show_all_tab = Column(Boolean, default=True)

class Poem(Base):
    __tablename__ = "poems"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    author = Column(String)
    text = Column(Text)
