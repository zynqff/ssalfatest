import httpx
from config import settings

async def analyze_poem_with_ai(prompt: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        # Заменилиllama3-8b-8192 на llama-3.1-8b-instant
        "model": "llama-4-scout-17b-16e-instruct", 
        "messages": [
            {"role": "system", "content": "Ты профессиональный литературовед и критик. Отвечай глубоко и на русском языке."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
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
    
