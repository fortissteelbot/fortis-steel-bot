import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === НАСТРОЙКИ MAILGUN ===
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")  # Ваш Private API Key
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "sandboxXXXXXX.mailgun.org")  # Ваш домен Mailgun
EMAIL_FROM = f"Fortis Chatbot <bot@{MAILGUN_DOMAIN}>"  # Отправитель
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")  # Получатель

def send_application_email(text: str, amount: int):
    """Отправка заявки через Mailgun API ТОЛЬКО при наличии контактов."""
    try:
        # ДВОЙНАЯ ПРОВЕРКА КОНТАКТОВ (на всякий случай)
        print(f"\n📧 ПРОВЕРКА КОНТАКТОВ ДЛЯ EMAIL:")
        print(f"   Исходный текст: '{text[:100]}...'")
        
        # Проверяем наличие телефона
        phone_keywords = ['тел', 'телефон', 'звоните', '+7', '8-9', '89', 'моб', 'сотов', 'номер', 'позвонить']
        has_phone = any(keyword in text.lower() for keyword in phone_keywords)
        
        # Дополнительно ищем цифровые номера телефонов
        import re
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
        if not MAILGUN_API_KEY:
            print("⚠️ MAILGUN_API_KEY не настроен. Письмо не будет отправлено.")
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
        
        # Данные для письма
        email_data = {
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": f"🚀 Новая заявка с сайта Fortis: {amount} руб.",
            "text": email_text
        }
        
        # URL для Mailgun API
        mailgun_url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        
        # Отправляем через Mailgun API (Basic Auth)
        response = requests.post(
            mailgun_url,
            auth=("api", MAILGUN_API_KEY),  # Mailgun использует Basic Auth
            data=email_data,
            timeout=10
        )
        
        # Проверяем ответ
        if response.status_code == 200:
            print(f"✅ Email успешно отправлен на {EMAIL_TO}")
            print(f"   ID сообщения: {response.json().get('id', 'unknown')}")
        else:
            print(f"⚠️ Mailgun API вернул ошибку {response.status_code}")
            print(f"   Ответ: {response.text[:150]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {str(e)}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")


# === ТЕСТОВАЯ ФУНКЦИЯ ===
def test_mailgun_connection():
    """Тестируем подключение к Mailgun."""
    print("\n🔍 Тестируем подключение к Mailgun...")
    
    if not MAILGUN_API_KEY:
        print("❌ MAILGUN_API_KEY не найден в переменных окружения")
        return False
    
    try:
        # Простой запрос для проверки домена
        response = requests.get(
            f"https://api.mailgun.net/v3/domains/{MAILGUN_DOMAIN}",
            auth=("api", MAILGUN_API_KEY),
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Подключение к Mailgun успешно!")
            print(f"   Домен: {MAILGUN_DOMAIN}")
            return True
        else:
            print(f"❌ Ошибка доступа к домену: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
