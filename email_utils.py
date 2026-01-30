import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# === НАСТРОЙКИ SENDGRID ===
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "bot@fortis-steel.ru")  # Должен быть верифицирован в SendGrid
EMAIL_TO = os.getenv("EMAIL_TO", "229@fortis-steel.ru")  # Получатель заявок

def send_application_email(text: str, amount: int, phone: str, email: str):
    """
    Отправка ПОЛНОЙ заявки через SendGrid API.
    Вызывается, когда у клиента есть И телефон, И email.
    """
    try:
        print(f"\n📨 ОТПРАВКА ПОЛНОЙ ЗАЯВКИ")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone}")
        print(f"   Email: {email}")
        print(f"   Длина текста: {len(text)} символов")
        
        # Проверяем API ключ
        if not SENDGRID_API_KEY:
            print("⚠️ КРИТИЧЕСКАЯ ОШИБКА: SENDGRID_API_KEY не настроен. Письмо не будет отправлено.")
            return False
        
        # Формируем текст письма
        email_text = f"""🎯 ПОЛНАЯ ЗАЯВКА С КОНТАКТАМИ

💰 СУММА ЗАКАЗА: {amount} руб.

📞 КОНТАКТНЫЕ ДАННЫЕ КЛИЕНТА:
• Телефон: {phone}
• Email: {email}

📋 ПОЛНЫЙ ТЕКСТ ДИАЛОГА С КЛИЕНТОМ:
{text}

📊 ДЕТАЛИ ЗАЯВКИ:
• Сумма заказа: {amount} руб.
• Дата получения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Статус: Полная заявка (есть телефон и email)
• Источник: Чат-бот сайта Fortis Steel

✅ ГОТОВО К ОБРАБОТКЕ:
Клиент предоставил все необходимые контакты. 
Можно связываться для уточнения деталей заказа.

---
Автоматически отправлено чат-ботом сайта Fortis Steel
"""
        
        # Создаем письмо через SendGrid
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=f"🎯 ПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб. заменяем запятые на пробелы".replace(",", " "),
            plain_text_content=email_text
        )
        
        # Отправляем через SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Проверяем ответ
        if response.status_code == 202:
            print(f"✅ ПОЛНАЯ заявка успешно отправлена на {EMAIL_TO}")
            print(f"   Статус SendGrid: {response.status_code}")
            return True
        else:
            print(f"⚠️ ОШИБКА SendGrid при отправке полной заявки: {response.status_code}")
            print(f"   Тело ответа: {response.body[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при отправке полной заявки: {str(e)}")
        return False


def send_incomplete_application_email(text: str, amount: int, phone: str = None, email: str = None):
    """
    Отправка НЕПОЛНОЙ заявки через SendGrid API.
    Вызывается при таймауте (10 минут) или если клиент дал только один контакт.
    """
    try:
        print(f"\n📨 ОТПРАВКА НЕПОЛНОЙ ЗАЯВКИ (ТАЙМАУТ)")
        print(f"   Сумма: {amount} руб.")
        print(f"   Телефон: {phone if phone else 'Нет'}")
        print(f"   Email: {email if email else 'Нет'}")
        
        if not SENDGRID_API_KEY:
            print("⚠️ SENDGRID_API_KEY не настроен.")
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

💰 СУММА ЗАКАЗА: {amount} руб.

📞 ИМЕЮЩИЕСЯ КОНТАКТЫ:
• Телефон: {phone if phone else '❌ ОТСУТСТВУЕТ'}
• Email: {email if email else '❌ ОТСУТСТВУЕТ'}

❌ НЕДОСТАЮЩИЕ ДАННЫЕ: {missing_text.upper()}

📋 ТЕКСТ ДИАЛОГА С КЛИЕНТОМ:
{text}

📊 ДЕТАЛИ И СТАТУС:
• Сумма заказа: {amount} руб.
• Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Статус: Неполная заявка (клиент не предоставил все контакты)
• Причина: Таймаут 10 минут или клиент прекратил диалог
• Источник: Чат-бот сайта Fortis Steel

💡 РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ:
1. Свяжитесь с клиентом по ИМЕЮЩЕМУСЯ контакту
2. Запросите недостающий контакт ({missing_text})
3. Заявка перспективная ({amount} руб.) - стоит потратить время

🔍 КЛИЕНТ ПРОЯВИЛ ИНТЕРЕС К ЗАКАЗУ НА {amount} руб., 
НО НЕ ДАЛ ВСЕ КОНТАКТЫ. НУЖНО ДОЗВОНИТЬСЯ/НАПИСАТЬ!

---
Автоматически отправлено чат-ботом сайта Fortis Steel
"""
        
        # Создаем письмо
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=f"⚠️ НЕПОЛНАЯ ЗАЯВКА Fortis: {amount:,} руб. (нет {missing_text})".replace(",", " "),
            plain_text_content=email_text
        )
        
        # Отправляем
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ НЕПОЛНАЯ заявка отправлена на {EMAIL_TO}")
            print(f"   Статус: {response.status_code}")
            return True
        else:
            print(f"⚠️ Ошибка SendGrid при отправке неполной заявки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке неполной заявки: {str(e)}")
        return False


def test_sendgrid_connection():
    """
    Тестируем подключение к SendGrid.
    Проверяет, работает ли API ключ и можно ли отправлять письма.
    """
    print("\n🔍 ТЕСТИРУЕМ ПОДКЛЮЧЕНИЕ К SENDGRID...")
    
    if not SENDGRID_API_KEY:
        print("❌ SENDGRID_API_KEY не найден в переменных окружения")
        return False
    
    try:
        # Простой запрос для проверки API ключа
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Пытаемся получить информацию об аккаунте
        response = sg.client.user.account.get()
        
        if response.status_code == 200:
            print("✅ Подключение к SendGrid успешно!")
            print("   API ключ работает корректно")
            return True
        else:
            print(f"❌ Ошибка доступа к SendGrid: {response.status_code}")
            print(f"   Возможно, неверный API ключ или проблемы с аккаунтом")
            return False
            
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
        
        success = response.status_code == 202
        if success:
            print(f"✅ Простое письмо отправлено: {subject}")
        else:
            print(f"⚠️ Ошибка отправки простого письма: {response.status_code}")
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка отправки простого письма: {e}")
        return False


# === ТЕСТОВЫЙ ВЫЗОВ ПРИ ЗАПУСКЕ МОДУЛЯ ===
if __name__ == "__main__":
    print("🧪 Тестируем модуль email_utils.py")
    test_result = test_sendgrid_connection()
    print(f"Результат теста: {'✅ УСПЕХ' if test_result else '❌ ПРОВАЛ'}")
