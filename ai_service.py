import httpx
from core.config import settings

async def analyze_poem_with_ai(text: str):
    """
    Используем Groq API для мгновенного анализа.
    Модель: llama3-8b-8192 (очень быстрая и умная).
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-8b-8192", # Самая оптимальная модель на текущий момент
        "messages": [
            {
                "role": "system", 
                "content": "Ты профессиональный литературовед. Давай краткий, глубокий анализ стихотворения на русском языке."
            },
            {
                "role": "user", 
                "content": f"Проанализируй этот стих:\n\n{text}"
            }
        ],
        "temperature": 0.7
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"Ошибка Groq: {str(e)}"
