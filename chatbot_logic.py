import requests
import replicate

SYSTEM_PROMPT = """
Ты — опытный менеджер по продажам компании Фортис металл и дизайн, специализирующейся на оптовых и розничных поставках металлопроката. Ты вежливый, компетентный, ориентированный на клиента и умеешь вести деловой диалог. Твоя задача — помочь посетителю сайта подобрать нужный вид металлопроката, ответить на вопросы, предложить выгодные решения и, при наличии интересной заявки (от 50 000 рублей), корректно собрать контактные данные и отправить заявку на почту отдела продаж.

Твоя роль:
Выдавай себя за живого менеджера по имени Аркадий. Отвечай с задержкой, как если бы ты печатал текст вживую.
Представляйся кратко: «Здравствуйте, менеджер Аркадий. Готов помочь с подбором металлопроката и оформлением заказа.»

Веди себя профессионально, но дружелюбно. Не используй сленг, но и не будь слишком формальным.

Говори кратко, по делу, избегай длинных абзацев. Отвечай понятно, особенно если клиент может не разбираться в терминах.

Что ты должен уметь:

Задавать уточняющие вопросы, если запрос клиента неполный:

Какой вид металлопроката вас интересует? (листовой прокат, арматура, трубы, профиль, уголок, швеллер, балка и т.д.)

Какие параметры? (марка стали, толщина, длина, диаметр, вес, тип покрытия — оцинковка, окраска и пр.)

На какую сферу применения? (строительство, производство, ремонт, монтаж и т.п.)

Нужна доставка? (уточни регион или город)

Предпочтительный объём заказа?

Подсказывать и предлагать альтернативы, если нужно:

Например: «У нас в наличии есть аналог по ГОСТ 535-2005, он на 15% дешевле и подходит для ваших задач.»

Предлагай популярные позиции или акции, если они есть (можно оставить место для динамического обновления: «Сейчас действует специальное предложение на стальной лист Ст3сп»).

Работать с заявками от 50 000 руб.:

Если клиент указал объём заказа или сумма по расчёту превышает 50 000 руб., мягко переходи к сбору данных:
«Это уже серьёзный заказ — давайте я передам его секретарю, чтобы она назначила ответственного менеджеа, чтобы вам перезвонили и предложили лучшие условия. Назовите, пожалуйста, ваше имя, телефон и email?»

Подтверди: «Спасибо Ваши данные отправлены. С вами свяжутся в течение 30 минут.»

Отправляй заявку на почту:

Все заявки (с указанием: ФИО, телефон, email, описание запроса, сумма, дата и время) автоматически отправляются на 229@fortis-steel.ru (или другую указанную почту).

Отвечай на частые вопросы:

«Работаете ли вы с НДС?» — Да, все цены указаны с НДС.

«Есть ли самовывоз?» — Да, все данные и контакты вам даст назначенный ответственный.

«Минимальный заказ?» — От 50 000 руб.

Завершай диалог вежливо:

Если клиент уходит: «Буду рад помочь в следующий раз. Удачи вам»

Важно:

Не выдумывай информацию, которой нет. Если не знаешь — скажи: «Уточню у коллег и вернусь с ответом» 
Не предлагай скидки без подтверждения. Лучше: «По таким объёмам менеджер может предложить индивидуальные условия.»
"""

def generate_bot_reply(api_key: str, message: str) -> str:
    """Генерация ответа бота через Replicate API."""
    try:
        print(f"\n=== ДЕБАГ: Начинаем генерацию ===")
        print(f"Сообщение: '{message}'")
        
        client = replicate.Client(api_token=api_key)
        
        # 1. Создаем ПРАВИЛЬНЫЙ промпт для GPT-5
        full_prompt = f"""{SYSTEM_PROMPT}

Теперь отвечай как менеджер Аркадий.

Вопрос клиента: {message}

Ответ Аркадия:"""
        
        print(f"Длина полного промпта: {len(full_prompt)} символов")
        print(f"Первые 500 символов: {full_prompt[:500]}...")
        
        # 2. Отправляем запрос как в документации Replicate
        # Важно: возможно нужен streaming как в примере
        output = replicate.run(
            "meta/meta-llama-3-70b-instruct",
            input={
                "prompt": full_prompt,
                "max_tokens": 1000,
                "temperature": 0.8,
                "top_p": 0.9
            }
        )
        
        print(f"Тип ответа: {type(output)}")
        print(f"Ответ сырой: {output}")
        
        # 3. Обрабатываем ответ (GPT-5 может вернуть генератор)
        result = ""
        if hasattr(output, '__iter__') and not isinstance(output, str):
            # Если это генератор/stream (как в документации)
            for chunk in output:
                if isinstance(chunk, str):
                    result += chunk
                else:
                    result += str(chunk)
        elif isinstance(output, str):
            result = output
        else:
            result = str(output)
        
        print(f"Итоговый ответ: {result[:200]}...")
        print(f"=== ДЕБАГ: Конец генерации ===\n")
        
        return result.strip() if result.strip() else "Извините, не получилось сгенерировать ответ."
            
    except Exception as e:
        print(f"ДЕБАГ: Ошибка: {str(e)}")
        return f"Ошибка: {str(e)}"

# --- ЛОГИКА ОПРЕДЕЛЕНИЯ "ИНТЕРЕСНОЙ ЗАЯВКИ" ---

KEYWORDS = [
    "купить", "заказать", "арматура", "труба", "лист", "швеллер", "профнастил", "оцинкованный", 
    "оцинковка", "профлист", "перфорированный", "балка", "уголок", "металл", "металлопрокат", 
    "стоимость", "цена", "штрипс", "рулон", "опт", "оптовый", "крупный", "партия", "поставк",
    "заявк", "оформ", "договор", "заказ"
]

def check_interesting_application(text: str):
    t = text.lower()
    
    print(f"\n🔍 ПРОВЕРКА ЗАЯВКИ: '{text}'")
    print(f"📝 Текст в нижнем регистре: '{t}'")
    
    # Проверка ключевых слов
    if not any(k in t for k in KEYWORDS):
        print(f"❌ Нет ключевых слов в тексте")
        return False, 0
    
    print(f"✅ Есть ключевые слова в тексте")
    
    import re
    
    # ====== ПРЕДВАРИТЕЛЬНО: ищем телефонные номера, чтобы исключить их ======
    phone_patterns = [
        r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # Полные номера
        r'\b\d{10}\b',  # 10 цифр подряд (9161234567)
        r'\b\d{11}\b',  # 11 цифр подряд (89161234567)
    ]
    
    phone_numbers = []
    for pattern in phone_patterns:
        phones = re.findall(pattern, t)
        if phones:
            phone_numbers.extend(phones)
    
    print(f"📞 Найденные телефоны для исключения: {phone_numbers}")
    
    # ШАБЛОН 1A: "50 тыс" → ×1000
    matches_thousand = re.findall(r'(\d+)\s*тыс', t)
    for match in matches_thousand:
        # Проверяем, не телефон ли это
        if any(match in phone or phone in match for phone in phone_numbers):
            print(f"   Пропускаем '{match} тыс' - похоже на часть телефона")
            continue
            
        num = int(match) * 1000
        print(f"🔎 Нашли '{match} тыс' → {num} руб.")
        if num >= 50000:
            print(f"   🎯 НАШЛИ БОЛЬШУЮ СУММУ: {num} руб.")
            return True, num
    
    # ШАБЛОН 1B: "1 млн" → ×1000000
    matches_million = re.findall(r'(\d+)\s*млн', t)
    for match in matches_million:
        # Проверяем, не телефон ли это
        if any(match in phone or phone in match for phone in phone_numbers):
            print(f"   Пропускаем '{match} млн' - похоже на часть телефона")
            continue
            
        num = int(match) * 1000000
        print(f"🔎 Нашли '{match} млн' → {num} руб.")
        if num >= 50000:
            print(f"   🎯 НАШЛИ БОЛЬШУЮ СУММУ: {num} руб.")
            return True, num
    
    # ШАБЛОН 1C: "100000 рублей" → ×1 (только если есть "руб")
    if 'руб' in t or 'р.' in t or 'р ' in t:
        matches_rub = re.findall(r'(\d+)[^\d]*руб', t) + re.findall(r'(\d+)[^\d]*р\.', t) + re.findall(r'(\d+)[^\d]*р\s', t)
        for match in matches_rub:
            # Проверяем, не телефон ли это
            if any(match in phone or phone in match for phone in phone_numbers):
                print(f"   Пропускаем '{match} руб' - похоже на телефон")
                continue
                
            # Дополнительная проверка: если число слишком длинное для суммы
            if len(match) >= 7:  # 1,000,000 = 7 цифр, но это максимум для реальных сумм
                print(f"   Пропускаем '{match} руб' - слишком длинное для суммы ({len(match)} цифр)")
                continue
                
            num = int(match)  # НЕ умножаем!
            print(f"🔎 Нашли '{match} руб' → {num} руб.")
            if num >= 50000:
                print(f"   🎯 НАШЛИ БОЛЬШУЮ СУММУ: {num} руб.")
                return True, num
    
    # ШАБЛОН 2: Контекстные числа
    context_patterns = [
        r'(?:заказ|заявк[ау]|сумм[аой]|итого|на\s+сумму)\s*[вна]?\s*(\d+)',
        r'по\s+(\d+)',
    ]
    
    for pattern in context_patterns:
        matches = re.findall(pattern, t)
        if matches:
            print(f"🔎 Шаблон '{pattern}' → совпадения: {matches}")
            for match in matches:
                # Проверяем, не телефон ли это
                if any(match in phone or phone in match for phone in phone_numbers):
                    print(f"   Пропускаем '{match}' - похоже на телефон")
                    continue
                    
                num = int(match)
                if num >= 50000:
                    print(f"   🎯 НАШЛИ БОЛЬШУЮ СУММУ: {num} руб.")
                    return True, num
    
    # ШАБЛОН 3: Количества и цены
    quantity_price = re.search(r'(\d+)\s*(?:тонн|тн?|шт)[^.]*по\s*(\d+)', t)
    if quantity_price:
        quantity = quantity_price.group(1)
        price = quantity_price.group(2)
        
        # Проверяем, не телефоны ли это
        is_quantity_phone = any(quantity in phone or phone in quantity for phone in phone_numbers)
        is_price_phone = any(price in phone or phone in price for phone in phone_numbers)
        
        if not (is_quantity_phone or is_price_phone):
            quantity_num = int(quantity)
            price_num = int(price)
            total = quantity_num * price_num
            print(f"🔎 Нашли '{quantity} по {price}' = {total} руб.")
            if total >= 50000:
                print(f"   🎯 НАШЛИ БОЛЬШУЮ СУММУ: {total} руб.")
                return True, total
        else:
            print(f"   Пропускаем '{quantity} по {price}' - похоже на телефоны")
    
    # ШАБЛОН 4: Все числа (с интеллектуальной проверкой)
    all_numbers = re.findall(r'\d+', t)
    print(f"🔎 Все числа в тексте: {all_numbers}")
    
    for num_str in all_numbers:
        # Пропускаем если это часть телефонного номера
        if any(num_str in phone or phone in num_str for phone in phone_numbers):
            print(f"   Пропускаем '{num_str}' - часть телефонного номера")
            continue
        
        # Пропускаем слишком длинные числа (вероятно не суммы)
        if len(num_str) >= 7:  # Более 1 млн обычно пишут "1 млн", а не "1000000"
            print(f"   Пропускаем '{num_str}' - слишком длинное ({len(num_str)} цифр)")
            continue
            
        num = int(num_str)
        
        # Пропускаем "подозрительные" числа
        # Например: 12345, 54321 (последовательности) - вероятно не суммы
        digits = [int(d) for d in num_str]
        is_sequence = all(digits[i] == digits[i-1] + 1 for i in range(1, len(digits))) or \
                      all(digits[i] == digits[i-1] - 1 for i in range(1, len(digits)))
        
        if is_sequence and len(num_str) >= 4:
            print(f"   Пропускаем '{num_str}' - последовательность цифр")
            continue
            
        if num >= 50000:
            print(f"   🎯 НАШЛИ БОЛЬШУЮ СУММУ (резервный поиск): {num} руб.")
            return True, num
    
    print(f"❌ Не нашли суммы > 50000")
    return False, 0
