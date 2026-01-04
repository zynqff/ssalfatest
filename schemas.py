from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Добавь это для чата:
class ChatQuestion(BaseModel):
    question: str
    poem_id: int
    
