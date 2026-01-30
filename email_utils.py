import os
from datetime import datetime
import resend
import re

# === НАСТРОЙКИ RESEND ===
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Fortis Bot <bot@fortis-steel.ru>")
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")

# Инициализируем Resend
resend.api_key = RESEND_API_KEY

def send_application_email(full_text: str, amount: int, phone: str, email: str):
    """
    Отправка ПОЛНОЙ заявки через Resend API.
    Вызывается, когда у клиента есть И телефон, И email.
    """
    try:
        print(f"\n📨 ОТПРАВКА ПОЛНОЙ ЗАЯВКИ ЧЕРЕЗ RESEND")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone}")
        print(f"   Email: {email}")
        
        # Проверяем API ключ
        if not RESEND_API_KEY:
            print("⚠️ КРИТИЧЕСКАЯ ОШИБКА: RESEND_API_KEY не настроен.")
            return False
        
        # Формируем текст письма
        email_text = f"""🎯 ПОЛНАЯ ЗАЯВКА С КОНТАКТАМИ

💰 СУММА ЗАКАЗА: {amount:,} руб.

📞 КОНТАКТНЫЕ ДАННЫЕ КЛИЕНТА:
• Телефон: {phone}
• Email: {email}

📋 ПОЛНЫЙ ТЕКСТ ДИАЛОГА С КЛИЕНТОМ:
{full_text}

📊 ДЕТАЛИ ЗАЯВКИ:
• Сумма заказа: {amount:,} руб.
• Дата получения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Статус: Полная заявка (есть телефон и email)
• Источник: Чат-бот сайта Fortis Steel

✅ ГОТОВО К ОБРАБОТКЕ:
Клиент предоставил все необходимые контакты. 
Можно связываться для уточнения деталей заказа.

---
Автоматически отправлено чат-ботом сайта Fortis Steel
"""
        
        # Отправляем через Resend API
        params = {
            "from": EMAIL_FROM,
            "to": [EMAIL_TO],
            "subject": f"🎯 ПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб.",
            "text": email_text
        }
        
        response = resend.Emails.send(params)
        
        if 'id' in response:
            print(f"✅ ПОЛНАЯ заявка успешно отправлена на {EMAIL_TO}")
            print(f"   ID письма: {response['id']}")
            return True
        else:
            print(f"⚠️ ОШИБКА Resend при отправке полной заявки")
            print(f"   Ответ: {response}")
            return False
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при отправке полной заявки через Resend: {str(e)}")
        return False


def send_incomplete_application_email(full_text: str, amount: int, phone: str = None, email: str = None):
    """
    Отправка НЕПОЛНОЙ заявки через Resend API.
    Вызывается при таймауте (10 минут) или если клиент дал только один контакт.
    """
    try:
        print(f"\n📨 ОТПРАВКА НЕПОЛНОЙ ЗАЯВКИ ЧЕРЕЗ RESEND (ТАЙМАУТ)")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone if phone else 'Нет'}")
        print(f"   Email: {email if email else 'Нет'}")
        
        if not RESEND_API_KEY:
            print("⚠️ RESEND_API_KEY не настроен.")
            return False
        
        # Определяем, чего не хватает
        missing_parts = []
        if not phone:
            missing_parts.append("телефона")
        if not email:
            missing_parts.append("email")
        
        missing_text = ", ".join(missing_parts)
        
        # Формируем текст письма с предупреждением
        email_text = f"""⚠️ ВНИМАНИЕ: НЕПОЛНАЯ ЗАЯВКА

💰 СУММА ЗАКАЗА: {amount:,} руб.

📞 ИМЕЮЩИЕСЯ КОНТАКТЫ:
• Телефон: {phone if phone else '❌ ОТСУТСТВУЕТ'}
• Email: {email if email else '❌ ОТСУТСТВУЕТ'}

❌ НЕДОСТАЮЩИЕ ДАННЫЕ: {missing_text.upper()}

📋 ТЕКСТ ДИАЛОГА С КЛИЕНТОМ:
{full_text}

📊 ДЕТАЛИ И СТАТУС:
• Сумма заказа: {amount:,} руб.
• Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Статус: Неполная заявка (клиент не предоставил все контакты)
• Причина: Таймаут 10 минут или клиент прекратил диалог
• Источник: Чат-бот сайта Fortis Steel

💡 РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ:
1. Свяжитесь с клиентом по ИМЕЮЩЕМУСЯ контакту
2. Запросите недостающий контакт ({missing_text})
3. Заявка перспективная ({amount:,} руб.) - стоит потратить время

🔍 КЛИЕНТ ПРОЯВИЛ ИНТЕРЕС К ЗАКАЗУ НА {amount:,} руб., 
НО НЕ ДАЛ ВСЕ КОНТАКТЫ. НУЖНО ДОЗВОНИТЬСЯ/НАПИСАТЬ!

---
Автоматически отправлено чат-ботом сайта Fortis Steel
"""
        
        # Отправляем через Resend
        params = {
            "from": EMAIL_FROM,
            "to": [EMAIL_TO],
            "subject": f"⚠️ НЕПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб. (нет {missing_text})",
            "text": email_text
        }
        
        response = resend.Emails.send(params)
        
        if 'id' in response:
            print(f"✅ НЕПОЛНАЯ заявка отправлена на {EMAIL_TO}")
            print(f"   ID письма: {response['id']}")
            return True
        else:
            print(f"⚠️ Ошибка Resend при отправке неполной заявки: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке неполной заявки через Resend: {str(e)}")
        return False


def test_resend_connection():
    """
    Тестируем подключение к Resend.
    Проверяет, работает ли API ключ.
    """
    print("\n🔍 ТЕСТИРУЕМ ПОДКЛЮЧЕНИЕ К RESEND...")
    
    if not RESEND_API_KEY:
        print("❌ RESEND_API_KEY не найден в переменных окружения")
        return False
    
    try:
        # Пытаемся отправить тестовое письмо
        test_params = {
            "from": EMAIL_FROM,
            "to": [EMAIL_TO],
            "subject": "✅ Тест подключения Resend",
            "text": f"Тестовое письмо от чат-бота Fortis Steel\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        response = resend.Emails.send(test_params)
        
        if 'id' in response:
            print("✅ Подключение к Resend успешно!")
            print(f"   Тестовое письмо отправлено, ID: {response['id']}")
            return True
        else:
            print(f"❌ Ошибка подключения к Resend: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Resend: {e}")
        return False


def send_email_simple(subject: str, text: str):
    """
    Простая функция отправки email через Resend.
    Используется для тестовых целей или простых уведомлений.
    """
    try:
        params = {
            "from": EMAIL_FROM,
            "to": [EMAIL_TO],
            "subject": subject,
            "text": text
        }
        
        response = resend.Emails.send(params)
        
        success = 'id' in response
        if success:
            print(f"✅ Простое письмо отправлено: {subject}")
            print(f"   ID: {response['id']}")
        else:
            print(f"⚠️ Ошибка отправки простого письма: {response}")
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка отправки простого письма: {e}")
        return False


# === ТЕСТОВЫЙ ВЫЗОВ ПРИ ЗАПУСКЕ МОДУЛЯ ===
if __name__ == "__main__":
    print("🧪 Тестируем модуль email_utils.py с Resend")
    test_result = test_resend_connection()
    print(f"Результат теста: {'✅ УСПЕХ' if test_result else '❌ ПРОВАЛ'}")
