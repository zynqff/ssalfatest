import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Настройка Gemini
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

async def analyze_poem_with_chat(poem_content: str, user_query: str, chat_history: list = None):
    try:
        # Инструкция для ИИ
        system_instruction = (
            f"Ты — эрудированный и дружелюбный литературный критик. Твоя задача — помочь пользователю глубже понять произведение. "
            f"Мы обсуждаем стихотворение:\n\n---\n{poem_content}\n---\n\n"
            "Всегда отвечай по существу, основываясь на тексте произведения и контексте диалога. Будь вежлив и поддерживай беседу."
        )

        model = genai.GenerativeModel(
            'gemini-3-flash-preview',
            system_instruction=system_instruction
        )
        
        # Превращаем историю из БД в формат, который понимает Gemini
        history_for_gemini = []
        if chat_history:
            for msg in chat_history:
                # Роли в Gemini: 'user' и 'model'
                role = "user" if msg.role == "user" else "model"
                history_for_gemini.append({"role": role, "parts": [msg.content]})
        
        # Запускаем чат с историей
        chat = model.start_chat(history=history_for_gemini)
        
        # Отправляем сообщение
        response = chat.send_message(user_query)
        
        return response.text
    except Exception as e:
        # Улучшаем обработку ошибок
        print(f"AI Service Error: {e}")
        return "К сожалению, произошла ошибка при обращении к нейросети. Попробуйте еще раз позже."
                
