import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content
from dotenv import load_dotenv
import re

load_dotenv()

# === НАСТРОЙКИ SENDGRID ===
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "bot@fortis-steel.ru")  # Должен быть верифицирован в SendGrid
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")

def send_application_email(text: str, amount: int):
    """Отправка заявки через SendGrid API ТОЛЬКО при наличии контактов."""
    try:
        # ДВОЙНАЯ ПРОВЕРКА КОНТАКТОВ (на всякий случай)
        print(f"\n📧 ПРОВЕРКА КОНТАКТОВ ДЛЯ EMAIL:")
        print(f"   Исходный текст: '{text[:100]}...'")
        
        # Проверяем наличие телефона
        phone_keywords = ['тел', 'телефон', 'звоните', '+7', '8-9', '89', 'моб', 'сотов', 'номер', 'позвонить']
        has_phone = any(keyword in text.lower() for keyword in phone_keywords)
        
        # Дополнительно ищем цифровые номера телефонов
        phone_numbers = re.findall(r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}', text)
        has_phone = has_phone or bool(phone_numbers)
        
        # Проверяем наличие email
        has_email = '@' in text
        # Дополнительно проверяем домены
        email_domains = ['.ru', '.com', '.рф', '.net', '.org', '.io']
        has_email = has_email or any(domain in text.lower() for domain in email_domains)
        
        # Проверяем наличие имени
        name_keywords = ['зовут', 'имя', 'фамилия', 'меня', 'это', 'я -', 'меня зовут', 'обращайтесь']
        has_name = any(keyword in text.lower() for keyword in name_keywords)
        
        # ЕСТЬ ЛИ ХОТЬ ОДИН КОНТАКТ?
        has_contacts = has_phone or has_email
        
        print(f"   Телефон: {'✅' if has_phone else '❌'} {phone_numbers if phone_numbers else ''}")
        print(f"   Email: {'✅' if has_email else '❌'}")
        print(f"   Имя: {'✅' if has_name else '❌'}")
        print(f"   ИТОГО контактов: {'✅ ЕСТЬ' if has_contacts else '❌ НЕТ'}")
        
        # ЕСЛИ НЕТ КОНТАКТОВ - НЕ ОТПРАВЛЯЕМ!
        if not has_contacts:
            print(f"🚫 EMAIL НЕ ОТПРАВЛЕН: В заявке нет контактов!")
            print(f"   Телефон: {has_phone}, Email: {has_email}")
            print(f"   Текст заявки: '{text[:150]}...'")
            return
        
        # Проверяем API ключ
        if not SENDGRID_API_KEY:
            print("⚠️ SENDGRID_API_KEY не настроен. Письмо не будет отправлено.")
            return
        
        # Улучшенный текст письма
        email_text = f"""Поступила заявка на сумму {amount} руб.

📋 Текст заявки:
{text}

📊 Детали:
- Сумма: {amount} руб.
- Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Источник: Чат-бот сайта Fortis Steel

📞 Контакты в заявке:
- Телефон: {'✅ Есть' if has_phone else '❌ Нет'} {phone_numbers if phone_numbers else ''}
- Email: {'✅ Есть' if has_email else '❌ Нет'} 
- Имя: {'✅ Есть' if has_name else '❌ Нет'}

{'⚠️ ВНИМАНИЕ: В заявке недостаточно контактных данных!' if not (has_phone or has_email) else '✅ В заявке есть контактные данные'}

---
Отправлено чат-ботом сайта Fortis Steel
"""
        
        # Создаем письмо через SendGrid
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=f"🚀 Новая заявка с сайта Fortis: {amount} руб.",
            plain_text_content=email_text
        )
        
        # Отправляем через SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Проверяем ответ
        if response.status_code == 202:
            print(f"✅ Email успешно отправлен на {EMAIL_TO}")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {response.headers}")
        else:
            print(f"⚠️ SendGrid API вернул ошибку {response.status_code}")
            print(f"   Body: {response.body}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки email: {str(e)}")


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
            print(f"   Ответ: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


# === АЛЬТЕРНАТИВНАЯ ФУНКЦИЯ (если нужна простая версия) ===
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
