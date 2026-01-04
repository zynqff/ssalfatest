import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Настройка Gemini
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

async def analyze_poem_with_chat(poem_content: str, user_query: str, chat_history: list = None):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Превращаем историю из БД в формат, который понимает Gemini
        # Роли в Gemini: 'user' и 'model' (вместо 'assistant')
        history_for_gemini = []
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.role == "user" else "model"
                history_for_gemini.append({"role": role, "parts": [msg.content]})
        
        # Инструкция для ИИ
        system_instruction = (
            f"Ты — литературный помощник. Мы обсуждаем стихотворение:\n{poem_content}\n"
            "Отвечай на основе текста и предыдущего диалога."
        )

        # Запускаем чат с историей
        chat = model.start_chat(history=history_for_gemini)
        
        # Отправляем сообщение
        response = chat.send_message(user_query)
        
        return response.text
    except Exception as e:
        return f"Ошибка ИИ: {str(e)}"
                
