import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Настройка Gemini
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

async def analyze_poem_with_chat(poem_content: str, user_query: str, chat_history: list = None):
    """Возвращает полный ответ от ИИ одним блоком."""
    try:
        model, history_for_gemini = _prepare_model_and_history(poem_content, chat_history)
        chat = model.start_chat(history=history_for_gemini)
        response = chat.send_message(user_query)
        return response.text
    except Exception as e:
        print(f"AI Service Error: {e}")
        return "К сожалению, произошла ошибка при обращении к нейросети. Попробуйте еще раз позже."

def analyze_poem_with_chat_stream(poem_content: str, user_query: str, chat_history: list = None):
    """Возвращает генератор для потоковой передачи ответа от ИИ."""
    try:
        model, history_for_gemini = _prepare_model_and_history(poem_content, chat_history)
        chat = model.start_chat(history=history_for_gemini)
        response_stream = chat.send_message(user_query, stream=True)
        
        for chunk in response_stream:
            # Отдаем только текстовую часть каждого блока
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"AI Service Stream Error: {e}")
        yield "К сожалению, произошла ошибка при обращении к нейросети. Попробуйте еще раз позже."

def _prepare_model_and_history(poem_content: str, chat_history: list = None):
    """Вспомогательная функция для подготовки модели и истории чата."""
    system_instruction = (
        f"Ты — эрудированный и дружелюбный литературный критик. Твоя задача — помочь пользователю глубже понять произведение. "
        f"Мы обсуждаем стихотворение:\n\n---\n{poem_content}\n---\n\n"
        "Всегда отвечай по существу, основываясь на тексте произведения и контексте диалога. Будь вежлив и поддерживай беседу."
    )

    model = genai.GenerativeModel(
        'gemini-3-flash-preview', # Возвращаем flash, т.к. он быстрее для стриминга
        system_instruction=system_instruction
    )
    
    history_for_gemini = []
    if chat_history:
        for msg in chat_history:
            role = "user" if msg.role == "user" else "model"
            history_for_gemini.append({"role": role, "parts": [msg.content]})
            
    return model, history_for_gemini
                
