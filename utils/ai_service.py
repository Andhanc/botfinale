import json
from typing import Any, Dict

import aiohttp

API_KEY = "bCRbsa88-Z8rTkDbw-QdJdC90a-NDABdnxJ"
BASE_URL = "https://api.ishushka.com"


# создаём новый чат один раз
async def create_chat() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/chat/new/{API_KEY}") as resp:
            data = await resp.json()
            return data["conversation_id"]  # сохраняем


# общение внутри чата
# ai_service.py - обновить функцию ask_ishushka
async def ask_ishushka(
    conversation_id: str, prompt: str, context: Dict[str, Any]
) -> str:
    # Формируем детальную информацию об устройствах
    asic_info = "\n".join(
        [
            f"- {device['manufacturer']} {device['name']}: "
            f"{device['hash_rate']} {'TH/s' if device['hash_rate'] > 1 else 'GH/s'}, "
            f"{device['power']}W, ${device['price']}"
            for device in context.get("asic_models", [])
        ]
    )

    coin_info = "\n".join(
        [
            f"- {coin['symbol']}: ${coin['price']:.4f}"
            for coin in context.get("coins", [])
        ]
    )

    system_prompt = (
        "Ты — сотрудник ASIC+, профессионал по майнингу. Отдавай ответы до 2000 символов. "
        "Ты должен отвечать только на вопросы по майнингу и распознавать их. "
        "У тебя должно быть строгое отсутствие разметки. Не используй Макрдаун или что-то на подобии. Просто чистый ответ"
        "Если ты уже представлялся пользователю, больше не представляйся.\n\n"
        "Доступное оборудование ASIC:\n"
        f"{asic_info}\n\n"
        "Текущие цены монет:\n"
        f"{coin_info}\n\n"
        "Примеры вопросов, на которые ты можешь отвечать:\n"
        "• «Какой ASIC выгодно купить за 3000$?»\n"
        "• «Какая сейчас прибыль от S19 XP?»\n"
        "• «Сравни Whatsminer M50 и Bitmain S19»\n"
        "• «Какие ASIC есть для майнинга Kaspa?»\n"
        "• «Покажи прайс на оборудование»\n\n"
        "Отвечай только на вопросы, связанные с майнингом и оборудованием. "
        "Если вопрос не по теме, вежливо откажись отвечать.\n\n"
        "Текущий запрос пользователя:"
    )

    payload = {
        "version": "gemini-2-5-flash",
        "message": system_prompt + "\n\n" + prompt,
        "ref": "",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/chat/request/{API_KEY}/{conversation_id}", data=payload
        ) as resp:
            data = await resp.json()
            print(data)
            return data.get("message", "Ошибка")
