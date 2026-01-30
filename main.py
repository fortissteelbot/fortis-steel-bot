import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from chatbot_logic import generate_bot_reply, check_interesting_application
from email_utils import send_application_email
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta

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

# Хранилище сессий (в продакшене используй Redis)
user_sessions = {}

def cleanup_old_sessions():
    """Очистка старых сессий (старше 2 часов)"""
    now = datetime.now()
    to_delete = []
    for session_id, session_data in user_sessions.items():
        if now - session_data['created_at'] > timedelta(hours=2):
            to_delete.append(session_id)
    
    for session_id in to_delete:
        del user_sessions[session_id]
        print(f"🧹 Очищена старая сессия: {session_id}")

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    user_ip = request.client.host  # Идентификатор сессии
    
    print(f"\n=== /chat endpoint вызван ===")
    print(f"Пользователь IP: {user_ip}")
    print(f"Сообщение: '{user_message}'")

    # Очищаем старые сессии
    cleanup_old_sessions()

    # 1. Проверяем заявку
    is_interesting, amount = check_interesting_application(user_message)
    print(f"Результат проверки заявки: интересная={is_interesting}, сумма={amount}")

    # 2. Если большая заявка (>50,000 руб)
    if is_interesting:
        print(f"🚨 БОЛЬШАЯ ЗАЯВКА! Сумма: {amount} руб.")
        
        # Создаем или обновляем сессию
        if user_ip not in user_sessions:
            user_sessions[user_ip] = {
                'created_at': datetime.now(),
                'amount': amount,
                'phone': None,
                'email': None,
                'text_parts': [],
                'email_sent': False,
                'last_message': None
            }
        
        session = user_sessions[user_ip]
        session['text_parts'].append(user_message)
        session['last_message'] = user_message
        full_text = "\n".join(session['text_parts'])
        
        # Ищем контакты в текущем сообщении
        # Телефон
        phone_pattern = r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        phone_matches = re.findall(phone_pattern, user_message)
        if phone_matches:
            session['phone'] = phone_matches[0]
            print(f"📞 Найден телефон: {session['phone']}")
        
        # Email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, user_message)
        if email_matches:
            session['email'] = email_matches[0]
            print(f"📧 Найден email: {session['email']}")
        
        # Если есть ключевые слова, но не нашли паттерном
        if not session['phone'] and any(word in user_message.lower() for word in ['тел', 'телефон', '+7', '8-9', '89']):
            session['phone'] = "Указан в тексте (не распознан автоматически)"
        
        if not session['email'] and '@' in user_message:
            session['email'] = "Указан в тексте (не распознан автоматически)"
        
        print(f"📊 Состояние сессии:")
        print(f"   Телефон: {'✅ ' + str(session['phone']) if session['phone'] else '❌'}")
        print(f"   Email: {'✅ ' + str(session['email']) if session['email'] else '❌'}")
        print(f"   Email отправлен: {'✅' if session['email_sent'] else '❌'}")
        
        # Логика ответа
        if session['email_sent']:
            # Письмо уже отправлено
            bot_reply = "Спасибо! Ваши данные уже переданы менеджеру. С вами свяжутся в течение 30 минут."
        
        elif session['phone'] and session['email']:
            # Есть оба контакта - отправляем письмо
            print(f"📨 ОТПРАВЛЯЕМ EMAIL: есть и телефон, и email")
            success = send_application_email(full_text, amount, session['phone'], session['email'])
            if success:
                session['email_sent'] = True
                bot_reply = "Спасибо! Ваши контактные данные получены. Я передал заявку менеджеру, с вами свяжутся в течение 30 минут."
            else:
                bot_reply = "Произошла ошибка при отправке заявки. Пожалуйста, попробуйте еще раз или свяжитесь с нами напрямую."
        
        elif session['phone'] and not session['email']:
            # Только телефон
            bot_reply = f"Спасибо за телефон! Для оформления заказа на {amount} руб. мне также нужен ваш email. Напишите его, пожалуйста."
        
        elif session['email'] and not session['phone']:
            # Только email
            bot_reply = f"Спасибо за email! Для оформления заказа на {amount} руб. мне также нужен ваш телефон для связи. Напишите его, пожалуйста."
        
        else:
            # Нет контактов
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
