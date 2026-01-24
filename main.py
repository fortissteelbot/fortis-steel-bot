import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
from chatbot_logic import generate_bot_reply, check_interesting_application
from email_utils import send_application_email
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем папку static, чтобы отдавать widget.js
app.mount("/static", StaticFiles(directory="static"), name="static")

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")


@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    print(f"\n=== /chat endpoint вызван ===")
    print(f"Сообщение пользователя: '{user_message}'")

    # 1. СНАЧАЛА проверяем, является ли сообщение интересной заявкой
    is_interesting, amount = check_interesting_application(user_message)
    print(f"Результат проверки заявки: интересная={is_interesting}, сумма={amount}")

    # 2. Если это большая заявка (от 50,000 руб)
    if is_interesting:
        print(f"🚨 БОЛЬШАЯ ЗАЯВКА! Сумма: {amount} руб.")
        
        # Отправляем email уведомление
        send_application_email(user_message, amount)
        
        # Фиксированный ответ для больших заявок
        bot_reply = f"Это уже серьёзный заказ ({amount} руб.) — давайте я передам его секретарю, чтобы она назначила ответственного менеджера для лучших условий. Назовите, пожалуйста, ваше имя, телефон и email?"
        
        print(f"📨 Email отправлен. Ответ бота: {bot_reply[:100]}...")
    
    # 3. Если обычный запрос (меньше 50,000 руб)
    else:
        print(f"✓ Обычный запрос, сумма меньше 50,000 руб или не указана")
        
        # Генерируем ответ через AI
        bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)
        print(f"🤖 AI ответ сгенерирован")

    return {"reply": bot_reply}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    """Эндпоинт для проверки здоровья, поддерживает GET и HEAD."""
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"status": "ok", "service": "chatbot-api"}


@app.get("/")
async def root():
    return {
        "service": "Fortis Chatbot API", 
        "status": "running",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET, HEAD)"
        }
    }
