import httpx
from config import settings

async def analyze_poem_with_ai(prompt: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Ты профессиональный литературовед и критик. Отвечай глубоко и на русском языке."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"Ошибка ИИ: {str(e)}"
            
