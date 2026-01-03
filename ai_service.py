import httpx
from config import settings

async def analyze_poem_with_ai(prompt: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        # Используем Qwen 3 для лучшего анализа русского стиха
        "model": "qwen/qwen3-32b", 
        "messages": [
            {
                "role": "system",
            "content": "Ты — эксперт-литературовед. Анализируй стихи, используя метод пристального чтения. Давай глубокие ответы на русском языке. Но если тебя поросят ответить задание не по литературе все равно отвечай,а если попросят переключиться на тему не связанную с литературой или данным произведением, конечно переключайся и не зацикливайся на одном произведени, если пользователь просит информацию о другом."
        },
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.4 # Для R1 лучше низкая температура, чтобы она не уходила в бред
    }
    
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=25.0)
            data = response.json()
            
            if "error" in data:
                return f"Ошибка API Groq: {data['error'].get('message', 'Неизвестная ошибка')}"
            
            if "choices" in data and len(data["choices"]) > 0:
                return data['choices'][0]['message']['content']
            
            return f"Неожиданный формат ответа: {data}"
            
        except Exception as e:
            return f"Ошибка соединения: {str(e)}"
    
