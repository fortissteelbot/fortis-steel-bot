import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# === НАСТРОЙКИ SENDGRID ===
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "youremail@fortissteelbot.com>")
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")

def send_application_email(full_text: str, amount: int, phone: str, email: str):
    """
    Отправка ПОЛНОЙ заявки через SendGrid API.
    Вызывается, когда у клиента есть И телефон, И email.
    """
    try:
        print(f"\n📨 ОТПРАВКА ПОЛНОЙ ЗАЯВКИ ЧЕРЕЗ SENDGRID")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone}")
        print(f"   Email: {email}")
        
        # Проверяем API ключ
        if not SENDGRID_API_KEY:
            print("⚠️ КРИТИЧЕСКАЯ ОШИБКА: SENDGRID_API_KEY не настроен.")
            return False
        
        if not EMAIL_FROM or not EMAIL_TO:
            print("⚠️ EMAIL_FROM или EMAIL_TO не настроены.")
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
        
        # Отправляем через SendGrid API
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=f"🎯 ПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб.",
            plain_text_content=email_text
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"✅ ПОЛНАЯ заявка успешно отправлена на {EMAIL_TO}")
        print(f"   Статус код: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при отправке полной заявки через SendGrid: {str(e)}")
        return False


def send_incomplete_application_email(full_text: str, amount: int, phone: str = None, email: str = None):
    """
    Отправка НЕПОЛНОЙ заявки через SendGrid API.
    Вызывается при таймауте (10 минут) или если клиент дал только один контакт.
    """
    try:
        print(f"\n📨 ОТПРАВКА НЕПОЛНОЙ ЗАЯВКИ ЧЕРЕЗ SENDGRID (ТАЙМАУТ)")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone if phone else 'Нет'}")
        print(f"   Email: {email if email else 'Нет'}")
        
        if not SENDGRID_API_KEY:
            print("⚠️ SENDGRID_API_KEY не настроен.")
            return False
        
        if not EMAIL_FROM or not EMAIL_TO:
            print("⚠️ EMAIL_FROM или EMAIL_TO не настроены.")
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
        
        # Отправляем через SendGrid
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=f"⚠️ НЕПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб. (нет {missing_text})",
            plain_text_content=email_text
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"✅ НЕПОЛНАЯ заявка отправлена на {EMAIL_TO}")
        print(f"   Статус код: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при отправке неполной заявки через SendGrid: {str(e)}")
        return False


def test_sendgrid_connection():
    """
    Тестируем подключение к SendGrid.
    Проверяет, работает ли API ключ.
    """
    print("\n🔍 ТЕСТИРУЕМ ПОДКЛЮЧЕНИЕ К SENDGRID...")
    
    if not SENDGRID_API_KEY:
        print("❌ SENDGRID_API_KEY не найден в переменных окружения")
        return False
    
    try:
        # Пытаемся отправить тестовое письмо
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject="✅ Тест подключения SendGrid",
            plain_text_content=f"Тестовое письмо от чат-бота Fortis Steel\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"✅ Подключение к SendGrid успешно!")
        print(f"   Тестовое письмо отправлено, статус: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к SendGrid: {e}")
        return False


def send_email_simple(subject: str, text: str):
    """
    Простая функция отправки email через SendGrid.
    Используется для тестовых целей или простых уведомлений.
    """
    try:
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=subject,
            plain_text_content=text
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        success = response.status_code in [200, 201, 202]
        if success:
            print(f"✅ Простое письмо отправлено: {subject}")
            print(f"   Статус: {response.status_code}")
        else:
            print(f"⚠️ Ошибка отправки простого письма: {response.status_code}")
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка отправки простого письма: {e}")
        return False


# === ТЕСТОВЫЙ ВЫЗОВ ПРИ ЗАПУСКЕ МОДУЛЯ ===
if __name__ == "__main__":
    print("🧪 Тестируем модуль email_utils.py с SendGrid")
    test_result = test_sendgrid_connection()
    print(f"Результат теста: {'✅ УСПЕХ' if test_result else '❌ ПРОВАЛ'}")
