import asyncio
import logging
from typing import Dict, List

import aiohttp
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.models import Coin
from database.request import CoinReq, UserReq
from signature import Settings

logger = logging.getLogger(__name__)


class CoinGeckoService:
    def __init__(self, settings: Settings):
        self.db_session_maker = settings.db_manager.async_session
        self.coin_req = CoinReq(settings.db_manager.async_session)
        self.user_req = UserReq(settings.db_manager.async_session)
        self.base_url = "https://api.coingecko.com/api/v3"
        # Расширенный маппинг всех монет, поддерживаемых ботом
        self.coin_mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "DOGE": "dogecoin",
            "LTC": "litecoin",
            "KAS": "kaspa",
            "BCH": "bitcoin-cash",
            "BSV": "bitcoin-sv",
            "ETC": "ethereum-classic",
            "KDA": "kadena",
            "ETHW": "ethereum-pow-iou",
        }
        self.bot = settings.bot

    async def fetch_prices(self) -> Dict[str, Dict]:
        """Получение цен всех монет из CoinGecko API"""
        try:
            coin_ids = ",".join(self.coin_mapping.values())
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/simple/price",
                    params={
                        "ids": coin_ids,
                        "vs_currencies": "usd,rub",
                        "include_24hr_change": "true",
                    },
                    timeout=30,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    logger.info(f"Получены цены для {len(data)} монет из CoinGecko")
                    return data
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при получении цен с CoinGecko: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка при получении цен с CoinGecko: {e}")
            return {}

    async def update_coin_prices_and_notify(self):
        try:
            prices = await self.fetch_prices()
            if not prices:
                logger.warning("Не удалось получить цены с CoinGecko")
                return

            update_data = {}
            for symbol, coin_gecko_id in self.coin_mapping.items():
                if coin_gecko_id in prices:
                    coin_data = prices[coin_gecko_id]
                    update_data[symbol] = {
                        "price_usd": coin_data.get("usd", 0.0),
                        "price_rub": coin_data.get("rub", 0.0),
                        "price_change": coin_data.get("usd_24h_change", 0.0),
                    }

            await self.coin_req.update_coin_prices(update_data)
            logger.info(f"Цены обновлены для {len(update_data)} монет")
            await self.send_price_notification(update_data)
        except Exception as e:
            logger.error(f"Ошибка при обновлении цен: {e}")

    async def send_price_notification(self, prices_data: Dict[str, Dict]):
        try:
            coins = await self.coin_req.get_all_coins()

            target_symbols = ["BTC", "ETH", "LTC", "DOGE", "KAS"]

            # Жёстко сохраняем порядок
            filtered_coins = [
                coin
                for symbol in target_symbols
                for coin in coins
                if coin.symbol == symbol
            ]

            message = ""

            for coin in filtered_coins:
                if coin.symbol in prices_data:
                    data = prices_data[coin.symbol]
                    change_icon = "📈" if data["price_change"] >= 0 else "📉"
                    message += (
                        f"🔸 *{coin.symbol}* ({coin.name})\n"
                        f"   💵 ${data['price_usd']:,.2f} | ₽{data['price_rub']:,.0f}\n"
                        f"   {change_icon} {data['price_change']:+.1f}%\n\n"
                    )

            # users = await self.user_req.get_all_users()
            # for user in users:
            #     if user.notifications:
            #         try:
            #             await self.bot.send_message(
            #                 user.uid, message, parse_mode="Markdown"
            #             )
            #             await asyncio.sleep(0.1)
            #         except Exception as e:
            #             logger.error(
            #                 f"Не удалось отправить уведомление пользователю {user.uid}: {e}"
            #             )

            # # Отправка в канал
            # await self.bot.send_message(-1001546174824, message, parse_mode="Markdown")
            # logger.info(f"Уведомления отправлены {len(users)} пользователям")

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")

    async def get_usd_rub_rate(self) -> float:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/simple/price",
                    params={"ids": "tether", "vs_currencies": "rub"},
                    timeout=10,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("tether", {}).get("rub", 80.0)
        except Exception as e:
            logger.error(f"Ошибка при получении курса USD/RUB: {e}")
            return 80.0

    async def initialize_coins(self):
        """Инициализация монет с получением актуальных цен из API"""
        async with self.db_session_maker() as session:
            from sqlalchemy import select
            from database.models import Algorithm

            existing_coins = await session.execute(select(Coin))
            if not existing_coins.scalars().first():
                # Список монет для инициализации
                coins_to_add = [
                    {"symbol": "BTC", "name": "Bitcoin", "coin_gecko_id": "bitcoin", "algorithm": Algorithm.SHA256},
                    {"symbol": "ETH", "name": "Ethereum", "coin_gecko_id": "ethereum", "algorithm": Algorithm.ETCHASH},
                    {"symbol": "LTC", "name": "Litecoin", "coin_gecko_id": "litecoin", "algorithm": Algorithm.SCRYPT},
                    {"symbol": "DOGE", "name": "Dogecoin", "coin_gecko_id": "dogecoin", "algorithm": Algorithm.SCRYPT},
                    {"symbol": "KAS", "name": "Kaspa", "coin_gecko_id": "kaspa", "algorithm": Algorithm.KHEAVYHASH},
                    {"symbol": "BCH", "name": "Bitcoin Cash", "coin_gecko_id": "bitcoin-cash", "algorithm": Algorithm.SHA256},
                    {"symbol": "BSV", "name": "Bitcoin SV", "coin_gecko_id": "bitcoin-sv", "algorithm": Algorithm.SHA256},
                    {"symbol": "ETC", "name": "Ethereum Classic", "coin_gecko_id": "ethereum-classic", "algorithm": Algorithm.ETCHASH},
                    {"symbol": "KDA", "name": "Kadena", "coin_gecko_id": "kadena", "algorithm": Algorithm.BLAKE2S},
                    {"symbol": "ETHW", "name": "Ethereum PoW", "coin_gecko_id": "ethereum-pow-iou", "algorithm": Algorithm.ETCHASH},
                ]
                
                # Получаем актуальные цены из API
                logger.info("Получение актуальных цен монет из CoinGecko API...")
                prices = await self.fetch_prices()
                
                # Создаем монеты с актуальными ценами или значениями по умолчанию
                for coin_data in coins_to_add:
                    symbol = coin_data["symbol"]
                    coin_gecko_id = coin_data["coin_gecko_id"]
                    
                    # Получаем цену из API, если доступна
                    if prices and coin_gecko_id in prices:
                        price_data = prices[coin_gecko_id]
                        coin_data["current_price_usd"] = price_data.get("usd", 0.0)
                        coin_data["current_price_rub"] = price_data.get("rub", 0.0)
                        coin_data["price_change_24h"] = price_data.get("usd_24h_change", 0.0)
                        logger.info(f"Получена цена для {symbol}: ${coin_data['current_price_usd']:,.2f}")
                    else:
                        # Значения по умолчанию, если API недоступен
                        coin_data["current_price_usd"] = 0.0
                        coin_data["current_price_rub"] = 0.0
                        coin_data["price_change_24h"] = 0.0
                        logger.warning(f"Не удалось получить цену для {symbol}, используются значения по умолчанию")
                    
                    coin = Coin(**coin_data)
                    session.add(coin)
                
                await session.commit()
                logger.info(f"Монеты инициализированы с актуальными ценами из API")
                
                # Обновляем цены сразу после инициализации
                await self.update_coin_prices_and_notify()
            else:
                logger.info("Монеты уже существуют, обновляем цены...")
                # Обновляем цены для существующих монет
                await self.update_coin_prices_and_notify()
