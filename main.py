import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from chatbot_logic import generate_bot_reply, check_interesting_application
from email_utils import send_application_email, send_incomplete_application_email
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import requests
import threading
import asyncio

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

# Хранилище сессий пользователей (ключ: IP, значение: данные сессии)
user_sessions = {}

# ====== ФУНКЦИИ ДЛЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ ======

async def keep_alive_ping():
    """Периодически пингуем сам себя, чтобы сервер не засыпал на Render."""
    while True:
        try:
            # Ждем 10 минут (меньше чем 15 минут таймаут Render)
            await asyncio.sleep(600)  # 600 секунд = 10 минут
            
            # Пингуем наш же сервер
            base_url = os.getenv("RENDER_EXTERNAL_URL", "https://fortis-steel-bot.onrender.com")
            
            # Пробуем разные endpoint'ы
            endpoints_to_ping = ["/health", "/", "/ping"]
            
            for endpoint in endpoints_to_ping:
                try:
                    url = f"{base_url}{endpoint}"
                    response = requests.get(url, timeout=5)
                    print(f"🔔 Keep-alive ping to {endpoint}: {response.status_code}")
                    
                except Exception as e:
                    print(f"⚠️ Keep-alive ping failed for {endpoint}: {e}")
                    
        except Exception as e:
            print(f"❌ Keep-alive loop error: {e}")
            await asyncio.sleep(60)  # Ждем минуту при ошибке

def start_keep_alive():
    """Запускаем keep-alive в фоновом потоке."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(keep_alive_ping())

# Запускаем keep-alive при старте приложения
@app.on_event("startup")
async def startup_event():
    """Запускается при старте приложения."""
    print("🚀 Starting Fortis Chatbot API...")
    print("🔔 Starting keep-alive service...")
    
    # Запускаем keep-alive в фоне
    threading.Thread(target=start_keep_alive, daemon=True).start()
    
    print("✅ Keep-alive service started")
    print(f"📧 Email service: Resend")
    print(f"🤖 AI service: Replicate")

def cleanup_old_sessions():
    """
    Очистка старых сессий:
    - После 10 минут отправляем неполную заявку (если есть хотя бы один контакт)
    - После 2 часов удаляем сессию полностью
    """
    now = datetime.now()
    to_delete = []
    
    for session_id, session_data in user_sessions.items():
        session_age = now - session_data['created_at']
        
        # Если сессии больше 10 минут И есть хотя бы один контакт И письмо еще не отправлено
        if (session_age > timedelta(minutes=10) and 
            not session_data['email_sent'] and 
            (session_data['phone'] or session_data['email'])):
            
            print(f"⏰ ТАЙМАУТ 10 минут: отправляем неполную заявку для сессии {session_id}")
            
            # Отправляем неполную заявку
            full_text = "\n".join(session_data['text_parts'])
            send_incomplete_application_email(
                full_text, 
                session_data['amount'], 
                session_data['phone'], 
                session_data['email']
            )
            session_data['email_sent'] = True
            session_data['incomplete_sent'] = True
            session_data['timeout_reason'] = "10 минут без второго контакта"
        
        # Удаляем очень старые сессии (больше 2 часов)
        if session_age > timedelta(hours=2):
            to_delete.append(session_id)
            print(f"🧹 Удаляем старую сессию {session_id} (больше 2 часов)")
    
    for session_id in to_delete:
        del user_sessions[session_id]

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    user_ip = request.client.host  # Используем IP как идентификатор сессии
    
    print(f"\n=== /chat endpoint вызван ===")
    print(f"Пользователь IP: {user_ip}")
    print(f"Сообщение: '{user_message}'")

    # Очищаем старые сессии перед обработкой нового сообщения
    cleanup_old_sessions()

    # 1. Проверяем, является ли это интересной заявкой (>50,000 руб)
    is_interesting, amount = check_interesting_application(user_message)
    print(f"Результат проверки заявки: интересная={is_interesting}, сумма={amount}")

    # 2. Если это большая заявка (>50,000 руб)
    if is_interesting:
        print(f"🚨 БОЛЬШАЯ ЗАЯВКА! Сумма: {amount} руб.")
        
        # Создаем новую сессию или получаем существующую
        if user_ip not in user_sessions:
            user_sessions[user_ip] = {
                'created_at': datetime.now(),
                'amount': amount,
                'phone': None,           # Найденный телефон
                'email': None,           # Найденный email
                'text_parts': [],        # Все сообщения пользователя в этой сессии
                'email_sent': False,     # Отправлено ли письмо
                'incomplete_sent': False,# Отправлено ли неполное письмо (таймаут)
                'reminder_sent': False,  # Отправлено ли напоминание о втором контакте
                'message_count': 0       # Количество сообщений в сессии
            }
            print(f"🆕 Создана новая сессия для {user_ip}")
        
        session = user_sessions[user_ip]
        session['text_parts'].append(user_message)
        session['message_count'] += 1
        full_text = "\n".join(session['text_parts'])
        
        # Ищем контакты в текущем сообщении
        
        # Телефон: ищем по паттерну (+7, 8, и т.д.)
        phone_pattern = r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        phone_matches = re.findall(phone_pattern, user_message)
        
        # Email: ищем стандартный email паттерн
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, user_message)
        
        # Обновляем найденные контакты
        if phone_matches and not session['phone']:
            session['phone'] = phone_matches[0]
            print(f"📞 Найден телефон в сообщении: {session['phone']}")
        
        if email_matches and not session['email']:
            session['email'] = email_matches[0]
            print(f"📧 Найден email в сообщении: {session['email']}")
        
        # Дополнительная проверка по ключевым словам (если не нашли паттерном)
        if not session['phone'] and any(word in user_message.lower() for word in ['тел', 'телефон', '+7', '8-9', '89', 'моб', 'сотов']):
            session['phone'] = "Указан в тексте (не распознан автоматически)"
            print(f"📞 Телефон указан в тексте")
        
        if not session['email'] and '@' in user_message:
            session['email'] = "Указан в тексте (не распознан автоматически)"
            print(f"📧 Email указан в тексте")
        
        # Логируем текущее состояние сессии
        print(f"📊 СОСТОЯНИЕ СЕССИИ {user_ip}:")
        print(f"   Сообщений: {session['message_count']}")
        print(f"   Телефон: {'✅ ' + str(session['phone']) if session['phone'] else '❌ Нет'}")
        print(f"   Email: {'✅ ' + str(session['email']) if session['email'] else '❌ Нет'}")
        print(f"   Полное письмо отправлено: {'✅' if session['email_sent'] and not session.get('incomplete_sent') else '❌'}")
        print(f"   Неполное письмо отправлено: {'✅' if session.get('incomplete_sent') else '❌'}")
        print(f"   Напоминание отправлено: {'✅' if session['reminder_sent'] else '❌'}")
        
        # ===== ЛОГИКА ОТВЕТА БОТА =====
        
        # Случай 1: Письмо уже отправлено (полное или неполное)
        if session['email_sent']:
            if session.get('incomplete_sent'):
                bot_reply = "Заявка передана менеджеру. Мы свяжемся с вами по имеющимся контактам. Спасибо!"
            else:
                bot_reply = "Спасибо! Полная заявка передана менеджеру. С вами свяжутся в течение 30 минут."
        
        # Случай 2: Есть ОБА контакта - отправляем ПОЛНУЮ заявку
        elif session['phone'] and session['email']:
            print(f"📨 ОТПРАВЛЯЕМ ПОЛНУЮ ЗАЯВКУ (есть и телефон, и email)")
            success = send_application_email(full_text, amount, session['phone'], session['email'])
            if success:
                session['email_sent'] = True
                bot_reply = "Спасибо! Полная заявка передана менеджеру. С вами свяжутся в течение 30 минут."
            else:
                bot_reply = "Произошла ошибка при отправке заявки. Пожалуйста, попробуйте еще раз или свяжитесь с нами напрямую."
        
        # Случай 3: Есть только ОДИН контакт
        elif session['phone'] or session['email']:
            has_phone = bool(session['phone'])
            has_email = bool(session['email'])
            
            # Если это уже не первое сообщение с контактом, отправляем напоминание
            if not session['reminder_sent'] and session['message_count'] >= 2:
                if has_phone and not has_email:
                    bot_reply = f"Спасибо за телефон! Для быстрого оформления заказа на {amount} руб. укажите также email. Это ускорит обработку заявки."
                elif has_email and not has_phone:
                    bot_reply = f"Спасибо за email! Для быстрого оформления заказа на {amount} руб. укажите также телефон для связи. Это ускорит обработку заявки."
                session['reminder_sent'] = True
                print(f"💡 Отправлено напоминание о втором контакте")
            
            else:
                # Просим недостающий контакт
                if has_phone and not has_email:
                    bot_reply = f"Спасибо! Для оформления заказа на {amount} руб. мне также нужен ваш email. Напишите его, пожалуйста."
                elif has_email and not has_phone:
                    bot_reply = f"Спасибо! Для оформления заказа на {amount} руб. мне также нужен ваш телефон для связи. Напишите его, пожалуйста."
                else:
                    bot_reply = f"Это уже серьёзный заказ ({amount} руб.) — назовите, пожалуйста, телефон и email для связи?"
        
        # Случай 4: Нет контактов вообще
        else:
            bot_reply = f"Это уже серьёзный заказ ({amount} руб.) — давайте я передам его менеджеру для лучших условий. Назовите, пожалуйста, телефон и email для связи?"
    
    # 3. Если это обычный запрос (не заявка >50,000 руб)
    else:
        print(f"✓ Обычный запрос, сумма меньше 50,000 руб или не указана")
        bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)

    return {"reply": bot_reply}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    """Эндпоинт для проверки здоровья, поддерживает GET и HEAD."""
    if request.method == "HEAD":
        return Response(status_code=200)
    return {
        "status": "ok", 
        "service": "fortis-chatbot-api",
        "timestamp": datetime.now().isoformat(),
        "sessions_count": len(user_sessions),
        "email_service": "resend"
    }


@app.get("/")
async def root():
    """Корневой endpoint с информацией о сервисе."""
    return {
        "service": "Fortis Chatbot API", 
        "status": "running",
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": {
                "url": "/chat",
                "method": "POST",
                "description": "Основной endpoint для общения с ботом"
            },
            "health": {
                "url": "/health", 
                "method": "GET, HEAD",
                "description": "Проверка работоспособности сервиса"
            },
            "ping": {
                "url": "/ping",
                "method": "GET",
                "description": "Простой пинг для keep-alive"
            }
        },
        "features": {
            "ai_provider": "Replicate (Llama 3 70B)",
            "email_provider": "Resend",
            "session_timeout": "10 minutes for incomplete applications",
            "min_order_amount": "50,000 RUB"
        }
    }


@app.get("/ping")
async def ping():
    """Простой endpoint для пинга сервера (используется для keep-alive)."""
    return {
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "service": "fortis-chatbot",
        "message": "Server is alive and responding"
    }


@app.get("/debug/sessions")
async def debug_sessions():
    """Отладочный эндпоинт для просмотра активных сессий (только для разработки)."""
    now = datetime.now()
    active_sessions = {}
    
    for session_id, session_data in user_sessions.items():
        session_age = now - session_data['created_at']
        active_sessions[session_id] = {
            "age_seconds": session_age.total_seconds(),
            "age_minutes": round(session_age.total_seconds() / 60, 1),
            "amount": session_data['amount'],
            "phone": session_data['phone'],
            "email": session_data['email'],
            "message_count": session_data['message_count'],
            "email_sent": session_data['email_sent'],
            "incomplete_sent": session_data.get('incomplete_sent', False)
        }
    
    return {
        "active_sessions_count": len(user_sessions),
        "current_time": now.isoformat(),
        "sessions": active_sessions
    }


@app.get("/test/email")
async def test_email():
    """Тестовый endpoint для проверки отправки email (только для разработки)."""
    test_amount = 75000
    test_phone = "+79161234567"
    test_email = "test@example.com"
    test_text = "Это тестовое сообщение для проверки отправки email через Resend."
    
    try:
        # Тест полной заявки
        success_full = send_application_email(test_text, test_amount, test_phone, test_email)
        
        # Тест неполной заявки
        success_incomplete = send_incomplete_application_email(test_text, test_amount, test_phone, None)
        
        return {
            "status": "test_completed",
            "full_email_sent": success_full,
            "incomplete_email_sent": success_incomplete,
            "test_data": {
                "amount": test_amount,
                "phone": test_phone,
                "email": test_email
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Обработчик ошибок 404
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return Response(
        status_code=404,
        content=f"Endpoint {request.url.path} not found. Available endpoints: /chat (POST), /health (GET), / (GET)"
    )
