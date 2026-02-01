import os
import requests
from datetime import datetime

# === НАСТРОЙКИ FORMSPREE ===
FORMSPREE_URL = os.getenv("FORMSPREE_URL", "https://formspree.io/f/xgozobyn")
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")

def send_application_email(full_text: str, amount: int, phone: str, email: str):
    """
    Отправка ПОЛНОЙ заявки через Formspree API.
    Вызывается, когда у клиента есть И телефон, И email.
    """
    try:
        print(f"\n📨 ОТПРАВКА ПОЛНОЙ ЗАЯВКИ ЧЕРЕЗ FORMSPREE")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone}")
        print(f"   Email: {email}")
        
        if not FORMSPREE_URL:
            print("❌ FORMSPREE_URL не настроен.")
            return False
        
        # Формируем данные для отправки
        form_data = {
            "_replyto": "bot@fortissteelbot.com",
            "_subject": f"🎯 ПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб.",
            "amount": f"{amount:,} руб.",
            "phone": phone,
            "client_email": email,
            "text": full_text,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "type": "full_application"
        }
        
        # Отправляем через Formspree API
        response = requests.post(
            FORMSPREE_URL,
            data=form_data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=10
        )
        
        print(f"   Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ ПОЛНАЯ заявка отправлена на {EMAIL_TO}")
            return True
        else:
            print(f"❌ Ошибка Formspree: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке через Formspree: {str(e)}")
        return False


def send_incomplete_application_email(full_text: str, amount: int, phone: str = None, email: str = None):
    """
    Отправка НЕПОЛНОЙ заявки через Formspree API.
    Вызывается при таймауте (10 минут) или если клиент дал только один контакт.
    """
    try:
        print(f"\n📨 ОТПРАВКА НЕПОЛНОЙ ЗАЯВКИ ЧЕРЕЗ FORMSPREE")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone if phone else 'Нет'}")
        print(f"   Email: {email if email else 'Нет'}")
        
        if not FORMSPREE_URL:
            print("❌ FORMSPREE_URL не настроен.")
            return False
        
        # Определяем, чего не хватает
        missing_parts = []
        if not phone:
            missing_parts.append("телефона")
        if not email:
            missing_parts.append("email")
        missing_text = ", ".join(missing_parts)
        
        # Формируем данные для отправки
        form_data = {
            "_replyto": "bot@fortissteelbot.com",
            "_subject": f"⚠️ НЕПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб. (нет {missing_text})",
            "amount": f"{amount:,} руб.",
            "phone": phone if phone else "ОТСУТСТВУЕТ",
            "client_email": email if email else "ОТСУТСТВУЕТ",
            "text": full_text,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "missing_data": missing_text,
            "type": "incomplete_application",
            "reason": "Таймаут 10 минут"
        }
        
        # Отправляем через Formspree API
        response = requests.post(
            FORMSPREE_URL,
            data=form_data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=10
        )
        
        print(f"   Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ НЕПОЛНАЯ заявка отправлена на {EMAIL_TO}")
            return True
        else:
            print(f"❌ Ошибка Formspree: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке через Formspree: {str(e)}")
        return False


def test_formspree_connection():
    """
    Тестируем подключение к Formspree.
    Проверяет, работает ли API ключ.
    """
    print("\n🔍 ТЕСТИРУЕМ ПОДКЛЮЧЕНИЕ К FORMSPREE...")
    
    if not FORMSPREE_URL:
        print("❌ FORMSPREE_URL не найден в переменных окружения")
        return False
    
    try:
        test_data = {
            "_replyto": "bot@fortissteelbot.com",
            "_subject": "✅ Тест подключения Formspree",
            "amount": "0 руб.",
            "phone": "+79161234567",
            "client_email": "test@example.com",
            "text": "Тестовое сообщение от чат-бота Fortis Steel",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "type": "test"
        }
        
        response = requests.post(
            FORMSPREE_URL,
            data=test_data,
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Подключение к Formspree успешно!")
            print(f"   Тестовое письмо отправлено")
            return True
        else:
            print(f"❌ Ошибка подключения к Formspree: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Formspree: {e}")
        return False


# === ТЕСТОВЫЙ ВЫЗОВ ПРИ ЗАПУСКЕ МОДУЛЯ ===
if __name__ == "__main__":
    print("🧪 Тестируем модуль email_utils.py с Formspree")
    test_result = test_formspree_connection()
    print(f"Результат теста: {'✅ УСПЕХ' if test_result else '❌ ПРОВАЛ'}")
