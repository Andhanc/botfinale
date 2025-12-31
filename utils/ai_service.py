import asyncio
import json
import os
from typing import Any, Dict

import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AI_API_KEY")
if not API_KEY:
    raise ValueError("AI_API_KEY not set in .env file. Get your API key from https://ai.io.net/ai/api-keys")

# Используем OpenAI-совместимый API endpoint, как в примере
AI_API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
# Используем поддерживаемую модель из списка API
AI_MODEL = "deepseek-ai/DeepSeek-V3.2"  # Можно изменить на другую модель из списка при необходимости


async def ask_ishushka(
    conversation_id: str, prompt: str, context: Dict[str, Any]
) -> str:
    """
    Отправляет запрос к AI API и получает ответ
    Использует OpenAI-совместимый API формат, как в примере tarot бота
    """
    asic_info = "\n".join(
        [
            f"- {device.get('manufacturer', 'N/A')} {device.get('name', 'N/A')}: "
            f"{device.get('hash_rate', 0)} {'TH/s' if device.get('hash_rate', 0) > 1 else 'GH/s'}, "
            f"{device.get('power', 0)}W"
            for device in context.get("asic_models", [])
        ]
    )

    coin_info = "\n".join(
        [
            f"- {coin.get('symbol', 'N/A')}: ${coin.get('price', 0):.4f} (₽{coin.get('price_rub', 0):.2f})"
            for coin in context.get("coins", [])
        ]
    )

    system_prompt = (
        "Ты — ведущий инженер-аналитик компании ASIC Store. Твой экспертность покрывает два ключевых направления: "
        "майнинг на ASIC-фермах и энергообеспечение на базе газопоршневых установок (ГПУ) но мы пока это не продаём имей ввиду. "
        "Все финансовые расчеты производи строго в долларах.\n\n"
        f"Доступное оборудование ASIC:\n{asic_info if asic_info else 'Информация отсутствует'}\n\n"
        f"**АКТУАЛЬНЫЕ ЦЕНЫ МОНЕТ (используй ТОЛЬКО эти данные для расчетов):**\n{coin_info if coin_info else 'Информация отсутствует'}\n\n"
        f"**АКТУАЛЬНЫЙ КУРС ДОЛЛАРА:** 1$ = ₽{context.get('usd_rub_rate', 80)}\n\n"
        "**ВАЖНО:** Все цены монет и курс доллара предоставлены из актуальных источников данных. "
        "Используй ТОЛЬКО эти значения для всех расчетов и ответов. НЕ используй устаревшие или примерные значения.\n\n"
        "**КОНТАКТЫ ДЛЯ УТОЧНЕНИЯ ИНФОРМАЦИИ:**\n"
        "- Менеджер: @snooby37\n"
        "- Канал: @asic_mining_store\n"
        "При необходимости уточнения информации о доступности оборудования, актуальных ценах или условиях покупки, "
        "всегда направляй пользователей к менеджеру @snooby37 или в канал @asic_mining_store.\n\n"
        "**Логика ответа:**\n"
        "1. **Анализ уровня знаний:** Определи уровень экспертизы пользователя по его запросу.\n"
        "   - *Новичок:* Используй простые аналогии, объясняй базовые понятия (хешрейт, потребление, окупаемость), избегай сложного жаргона. Сфокусируйся на общей концепции.\n"
        "   - *Опытный:* Говори на профессиональном языке, используй термины (J/TH, ROI, волатильность), предоставляй детальные расчеты и сравнительный анализ.\n"
        "2. **Предмет запроса:**\n"
        "   - **ASIC/Майнинг:** При упоминании конкретной модели или расчетов доходности, после основного ответа ОБЯЗАТЕЛЬНО добавь фразу: 'Для проверки текущей доступности и актуальных условий покупки [название модели], пожалуйста, уточните у менеджера @snooby37 или посмотрите в нашем канале @asic_mining_store'\n"
        "   - **Цены монет/валют:** Всегда используй актуальные цены из предоставленных данных. Если пользователь спрашивает о ценах, используй точные значения из списка выше.\n"
        "   - **ГПУ (Газопоршневые установки):** Ты компетентен в этом вопросе. Объясняй их роль как источника энергообеспечения для майнинг-ферм, считай стоимость кВт*ч в долларах, говори о надежности и окупаемости.\n"
        "   - **Вне темы:** Если вопрос не связан с майнингом, криптовалютами, ASIC, энергоснабжением (вкл. ГПУ) или оборудованием, вежливо ответь: 'Я специализируюсь исключительно на вопросах, связанных с майнингом и энергообеспечением ферм. К сожалению, не могу помочь с этим вопросом. Для других вопросов обратитесь к менеджеру @snooby37 или в канал @asic_mining_store.'\n"
        "3. **Формат:** Всегда отвечай чистым, сплошным текстом без разметки (markdown, bullet points, HTML) просто чистый без стилизации ответ, но сделай красиво и читаемо. Длина ответа — до 2000 символов. Не представляйся повторно. ЭТО СТРОГО НАСТРОГО"
    )

    user_prompt = prompt

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        payload = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        async with aiohttp.ClientSession() as session:
            # Увеличиваем таймаут для сложных запросов (3 минуты)
            timeout = aiohttp.ClientTimeout(total=180, connect=10, sock_read=180)
            async with session.post(
                AI_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"API Error {resp.status}: {error_text}")
                    try:
                        error_data = await resp.json()
                        error_msg_obj = error_data.get("error", {})
                        if isinstance(error_msg_obj, dict):
                            error_msg = error_msg_obj.get("message", error_text)
                        else:
                            error_msg = error_text
                        if "401" in str(resp.status) or "unauthorized" in error_text.lower():
                            return "Ошибка: неверный API ключ. Проверьте настройки AI_API_KEY в файле .env\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"
                    except Exception as parse_error:
                        print(f"Error parsing API error response: {parse_error}")
                        pass
                    return "Ошибка подключения к AI-сервису. Попробуйте позже.\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"

                data = await resp.json()
                
                # Обработка ответа в формате OpenAI Chat Completions
                if "choices" in data and len(data["choices"]) > 0:
                    message_content = data["choices"][0]["message"]["content"] or ""
                    
                    # Удаляем возможные служебные метки (могут быть вложенные)
                    while "</think>" in message_content:
                        message_content = message_content.split("</think>")[-1].strip()
                    
                    # Очищаем от оставшихся меток
                    message_content = message_content.replace("</think>", "").strip()
                    
                    # Проверяем, что ответ не пустой
                    if not message_content or not message_content.strip():
                        message_content = "К сожалению, не удалось получить ответ от AI-сервиса. Попробуйте переформулировать вопрос."
                    
                    # Добавляем ссылки на менеджера и канал в конец ответа
                    footer = "\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"
                    message_content = message_content + footer
                    
                    return message_content
                else:
                    print(f"Unexpected API response format: {data}")
                    return "Не удалось получить ответ от сервиса.\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"

    except asyncio.TimeoutError as e:
        print(f"Timeout error: {e}")
        return "Запрос занимает слишком много времени. Попробуйте упростить вопрос или обратитесь к менеджеру.\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"
    except aiohttp.ClientError as e:
        import traceback
        error_type = type(e).__name__
        print(f"Network error: {error_type}: {e}")
        if error_type == "TimeoutError":
            return "Запрос превысил время ожидания. Попробуйте упростить вопрос или обратитесь к менеджеру.\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"
        traceback.print_exc()
        return "Ошибка сети. Проверьте подключение к интернету.\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_msg_str = str(e) if str(e).strip() else None
        print(f"Unexpected error: {error_type}")
        if error_msg_str:
            print(f"Error message: {error_msg_str}")
        traceback.print_exc()
        
        # Формируем сообщение об ошибке
        if error_msg_str and error_msg_str.strip():
            error_msg = f"Произошла непредвиденная ошибка: {error_msg_str}\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"
        else:
            error_msg = f"Произошла ошибка при обработке запроса ({error_type}). Попробуйте позже или обратитесь к менеджеру.\n\n💬 Наш менеджер: @snooby37\n📢 Наш канал: @asic_mining_store"
        return error_msg


# Для обратной совместимости, но теперь не используется
async def create_chat() -> str:
    """Больше не нужна для нового API, оставлена для совместимости"""
    return "not_needed"
