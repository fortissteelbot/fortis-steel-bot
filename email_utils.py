import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# === НАСТРОЙКИ SENDGRID ===
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "bot@fortis-steel.ru")
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")

def send_application_email(text: str, amount: int, phone: str = None, email: str = None):
    """Отправка заявки через SendGrid API с контактами."""
    try:
        print(f"\n📨 ОТПРАВКА EMAIL С КОНТАКТАМИ")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone}")
        print(f"   Email: {email}")
        print(f"   Текст: '{text[:100]}...'")
        
        # Проверяем API ключ
        if not SENDGRID_API_KEY:
            print("⚠️ SENDGRID_API_KEY не настроен. Письмо не будет отправлено.")
            return False
        
        # Формируем текст письма
        email_text = f"""🎯 ПОЛНАЯ ЗАЯВКА С КОНТАКТАМИ

Сумма заказа: {amount} руб.

📞 КОНТАКТНЫЕ ДАННЫЕ:
- Телефон: {phone if phone else 'Не указан'}
- Email: {email if email else 'Не указан'}

📋 Текст заявки:
{text}

📊 Детали:
- Сумма: {amount} руб.
- Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Источник: Чат-бот сайта Fortis Steel

✅ Заявка собрана полностью

---
Отправлено автоматически чат-ботом сайта Fortis Steel
"""
        
        # Создаем письмо через SendGrid
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=f"🎯 ПОЛНАЯ ЗАЯВКА Fortis: {amount} руб.",
            plain_text_content=email_text
        )
        
        # Отправляем через SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Проверяем ответ
        if response.status_code == 202:
            print(f"✅ Email успешно отправлен на {EMAIL_TO}")
            print(f"   Status Code: {response.status_code}")
            return True
        else:
            print(f"⚠️ SendGrid API вернул ошибку {response.status_code}")
            print(f"   Body: {response.body[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки email: {str(e)}")
        return False


# === ТЕСТОВАЯ ФУНКЦИЯ ===
def test_sendgrid_connection():
    """Тестируем подключение к SendGrid."""
    print("\n🔍 Тестируем подключение к SendGrid...")
    
    if not SENDGRID_API_KEY:
        print("❌ SENDGRID_API_KEY не найден в переменных окружения")
        return False
    
    try:
        # Простой запрос для проверки API ключа
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Получаем информацию об аккаунте
        response = sg.client.user.account.get()
        
        if response.status_code == 200:
            print("✅ Подключение к SendGrid успешно!")
            return True
        else:
            print(f"❌ Ошибка доступа к SendGrid: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


# === АЛЬТЕРНАТИВНАЯ ФУНКЦИЯ ===
def send_email_simple(subject: str, text: str):
    """Простая функция отправки email через SendGrid."""
    try:
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=subject,
            plain_text_content=text
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False
