import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

    # 1. Проверяем заявку
    is_interesting, amount = check_interesting_application(user_message)
    print(f"Результат проверки заявки: интересная={is_interesting}, сумма={amount}")

    # 2. Если большая заявка (>50,000 руб)
    if is_interesting:
        print(f"🚨 БОЛЬШАЯ ЗАЯВКА! Сумма: {amount} руб.")
        
        # ПРОВЕРЯЕМ НАЛИЧИЕ КОНТАКТОВ (ТОЛЬКО ЭТО!)
        # Телефонные номера
        has_phone = any(word in user_message.lower() for word in 
                       ['тел', 'телефон', 'звоните', '+7', '8-9', '89', 'моб', 'сотов', 'номер'])
        
        # Email
        has_email = '@' in user_message or any(domain in user_message.lower() for domain in ['.ru', '.com', '.рф', '.net'])
        
        # Имя/обращение
        has_name = any(word in user_message.lower() for word in 
                      ['зовут', 'имя', 'фамилия', 'меня', 'это', 'я -', 'меня зовут'])
        
        # ЕСТЬ ЛИ ХОТЬ ОДИН КОНТАКТ?
        has_contacts = has_phone or has_email or has_name
        
        print(f"📞 Проверка контактов:")
        print(f"   Телефон: {'✅' if has_phone else '❌'}")
        print(f"   Email: {'✅' if has_email else '❌'}")
        print(f"   Имя: {'✅' if has_name else '❌'}")
        print(f"   ИТОГО контактов: {'✅ ЕСТЬ' if has_contacts else '❌ НЕТ'}")
        
        # ОТПРАВЛЯЕМ EMAIL ТОЛЬКО ЕСЛИ ЕСТЬ КОНТАКТЫ!
        if has_contacts:
            print(f"📨 ОТПРАВЛЯЕМ EMAIL (есть контакты)")
            send_application_email(user_message, amount)
        else:
            print(f"📝 НЕТ КОНТАКТОВ, email НЕ отправляем")
        
        # Фиксированный ответ
        bot_reply = f"Это уже серьёзный заказ ({amount} руб.) — давайте я передам его секретарю, чтобы она назначила ответственного менеджера для лучших условий. Назовите, пожалуйста, ваше имя, телефон и email?"
    
    # 3. Если обычный запрос
    else:
        print(f"✓ Обычный запрос, сумма меньше 50,000 руб или не указана")
        bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)

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
