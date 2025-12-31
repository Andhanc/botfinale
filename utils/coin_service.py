import asyncio
import logging
from typing import Dict, List, Optional

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
        # Binance P2P API для получения курсов монет
        self.binance_p2p_url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        # ExchangeRate API для получения курсов валют
        self.exchange_rate_url = "https://api.exchangerate-api.com/v4/latest/USD"
        # CoinGecko API (используется как fallback и для получения изменения за 24ч)
        self.coin_gecko_url = "https://api.coingecko.com/api/v3"
        # Маппинг монет для Binance P2P (asset код)
        self.binance_coin_mapping = {
            "BTC": "BTC",
            "ETH": "ETH",
            "USDT": "USDT",
            "DOGE": "DOGE",
            "LTC": "LTC",
            "BCH": "BCH",
            "ETC": "ETC",
            # Монеты, которые могут быть недоступны на Binance P2P
            "KAS": "KAS",
            "BSV": "BSV",
            "KDA": "KDA",
            "ETHW": "ETHW",
        }
        # Маппинг для CoinGecko (используется для fallback и изменения за 24ч)
        self.coin_gecko_mapping = {
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

    async def get_binance_p2p_price(self, asset: str, fiat: str = "RUB") -> Optional[float]:
        """Получение цены P2P с Binance. Возвращает среднюю цену из топ-5 объявлений"""
        logger.info(f"🔍 Запрос к Binance P2P API для получения цены {asset}/{fiat}")
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                # Получаем объявления на продажу (SELL) - когда продавец продает монету за фиат
                # Это цена, по которой можно купить монету (цена для покупателя)
                payload = {
                    "asset": asset,
                    "fiat": fiat,
                    "merchantCheck": False,
                    "page": 1,
                    "payTypes": [],
                    "publisherType": None,
                    "rows": 10,  # Получаем больше объявлений для более точной средней цены
                    "tradeType": "SELL",
                    "transAmount": "",
                }
                
                logger.debug(f"📤 Отправка POST запроса к Binance P2P: {self.binance_p2p_url} с payload: {payload}")
                async with session.post(
                    self.binance_p2p_url,
                    json=payload,
                    headers=headers,
                    timeout=15,
                ) as response:
                    logger.debug(f"📥 Получен ответ от Binance P2P для {asset}/{fiat}, статус: {response.status}")
                    if response.status != 200:
                        logger.warning(
                            f"Binance P2P вернул статус {response.status} для {asset}/{fiat}"
                        )
                        return None
                    
                    data = await response.json()
                    
                    # Логируем структуру ответа при первой ошибке для отладки
                    if not data.get("success"):
                        error_msg = data.get("message", "Unknown error")
                        logger.debug(
                            f"Binance P2P API error для {asset}/{fiat}: {error_msg}. "
                            f"Response: {data}"
                        )
                    
                    if data.get("success") and data.get("data"):
                        ads = data["data"]
                        if ads and len(ads) > 0:
                            logger.debug(
                                f"Получено {len(ads)} объявлений для {asset}/{fiat} с Binance P2P"
                            )
                            # Берем среднюю цену из топ-5 объявлений для более точной оценки
                            prices = []
                            for idx, ad in enumerate(ads[:5]):
                                adv = ad.get("adv", {})
                                price = adv.get("price")
                                if price:
                                    try:
                                        price_float = float(price)
                                        if price_float > 0:
                                            prices.append(price_float)
                                            logger.debug(
                                                f"Объявление {idx+1} для {asset}/{fiat}: {price_float}"
                                            )
                                    except (ValueError, TypeError) as e:
                                        logger.debug(
                                            f"Не удалось преобразовать цену в float: {price}, ошибка: {e}"
                                        )
                                        continue
                            
                            if prices:
                                # Берем минимальную цену (низ рынка) - самую низкую цену из объявлений
                                prices.sort()
                                min_price = prices[0]  # Первая цена после сортировки - минимальная
                                
                                logger.info(
                                    f"Получена цена {asset}/{fiat} с Binance P2P (низ рынка): "
                                    f"{min_price:.2f} (минимальная из {len(prices)} объявлений, "
                                    f"диапазон: {min_price:.2f} - {prices[-1]:.2f})"
                                )
                                return min_price
                            else:
                                logger.warning(
                                    f"Не найдено валидных цен в объявлениях для {asset}/{fiat}. "
                                    f"Структура первого объявления: {ads[0] if ads else 'нет данных'}"
                                )
                    else:
                        # Детальное логирование при отсутствии данных
                        logger.warning(
                            f"Binance P2P не вернул данные для {asset}/{fiat}. "
                            f"Success: {data.get('success')}, "
                            f"Message: {data.get('message', 'нет сообщения')}, "
                            f"Response keys: {list(data.keys())}"
                        )
                        # Логируем первые 200 символов ответа для отладки
                        response_str = str(data)[:200]
                        logger.debug(f"Фрагмент ответа API: {response_str}")
                    
                    return None
        except aiohttp.ClientTimeout:
            logger.warning(f"Таймаут при получении цены {asset}/{fiat} с Binance P2P")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при получении цены {asset}/{fiat} с Binance P2P: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Ошибка при получении цены {asset}/{fiat} с Binance P2P: {e}",
                exc_info=True
            )
            return None

    async def get_coin_gecko_prices_batch(
        self, coin_ids: List[str], max_retries: int = 3
    ) -> Dict[str, Dict[str, float]]:
        """Получение цен нескольких монет из CoinGecko одним запросом (batch)"""
        if not coin_ids:
            return {}
        
        logger.info(f"🔍 Запрос к CoinGecko API для получения цен {len(coin_ids)} монет")
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # Объединяем все coin_id в один запрос
                    ids_param = ",".join(coin_ids)
                    
                    url = f"{self.coin_gecko_url}/simple/price"
                    params = {
                        "ids": ids_param,
                        "vs_currencies": "usd,rub",
                        "include_24hr_change": "true",
                    }
                    logger.debug(f"📤 Отправка GET запроса к CoinGecko: {url} с params: {params}")
                    async with session.get(
                        url,
                        params=params,
                        timeout=15,
                    ) as response:
                        logger.debug(f"📥 Получен ответ от CoinGecko, статус: {response.status}")
                        # Обработка 429 (Too Many Requests)
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            wait_time = retry_after + (attempt * 10)  # Увеличиваем задержку с каждой попыткой
                            logger.warning(
                                f"CoinGecko rate limit (429). Ожидание {wait_time} секунд перед повтором {attempt + 1}/{max_retries}"
                            )
                            if attempt < max_retries - 1:
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.error("Превышено количество попыток для CoinGecko")
                                return {}
                        
                        response.raise_for_status()
                        data = await response.json()
                        
                        result = {}
                        for coin_id in coin_ids:
                            if coin_id in data:
                                result[coin_id] = {
                                    "usd": data[coin_id].get("usd", 0.0),
                                    "rub": data[coin_id].get("rub", 0.0),
                                    "usd_24h_change": data[coin_id].get("usd_24h_change", 0.0),
                                }
                        return result
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка сети при получении цен с CoinGecko (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))  # Экспоненциальная задержка
                    continue
            except Exception as e:
                logger.error(f"Ошибка при получении цен с CoinGecko (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
        
        return {}

    async def get_coin_gecko_price(self, coin_id: str) -> Optional[Dict[str, float]]:
        """Получение цены одной монеты из CoinGecko (fallback для обратной совместимости)"""
        result = await self.get_coin_gecko_prices_batch([coin_id])
        return result.get(coin_id)

    async def fetch_prices(self) -> Dict[str, Dict]:
        """Получение цен всех монет из Binance P2P API (верхняя граница стакана)"""
        from datetime import datetime
        logger.info(f"⏰ Время начала получения цен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        prices = {}
        
        # Получаем сохраненные цены из БД на случай, если API недоступен (только для fallback)
        existing_coins = await self.coin_req.get_all_coins()
        saved_prices = {
            coin.symbol: {
                "usd": coin.current_price_usd or 0.0,
                "rub": coin.current_price_rub or 0.0,
                "usd_24h_change": coin.price_change_24h or 0.0,
            }
            for coin in existing_coins
        }
        logger.info(f"📦 Загружены сохраненные цены из БД для {len(saved_prices)} монет (используются только как fallback)")
        
        # Получаем курс USD/RUB для конвертации
        usd_to_rub = await self.get_usd_rub_rate()
        if not usd_to_rub or usd_to_rub <= 0:
            logger.warning("Не удалось получить курс USD/RUB, используем значение по умолчанию 80")
            usd_to_rub = 80.0
        
        # Получаем все изменения за 24ч из CoinGecko одним batch запросом
        coin_ids_for_24h = [
            self.coin_gecko_mapping[symbol]
            for symbol in self.binance_coin_mapping.keys()
            if symbol in self.coin_gecko_mapping
        ]
        
        logger.info(f"📈 Получение изменений за 24ч из CoinGecko для {len(coin_ids_for_24h)} монет...")
        gecko_24h_changes = await self.get_coin_gecko_prices_batch(coin_ids_for_24h)
        logger.info(f"✅ Получены изменения за 24ч для {len(gecko_24h_changes)} монет из CoinGecko")
        
        # Создаем маппинг symbol -> 24h change
        symbol_to_24h_change = {}
        for symbol, gecko_id in self.coin_gecko_mapping.items():
            if gecko_id in gecko_24h_changes:
                symbol_to_24h_change[symbol] = gecko_24h_changes[gecko_id].get("usd_24h_change", 0.0)
        
        # Получаем цены для каждой монеты с Binance P2P
        logger.info(f"🔄 Начинаем получение цен с Binance P2P для {len(self.binance_coin_mapping)} монет")
        for symbol, asset in self.binance_coin_mapping.items():
            try:
                logger.info(f"📊 Получение цены для {symbol} ({asset}) с Binance P2P...")
                # Сначала пытаемся получить цену в RUB с Binance P2P
                p2p_price_rub = await self.get_binance_p2p_price(asset, "RUB")
                
                # Добавляем задержку между запросами к Binance P2P, чтобы не перегружать API
                await asyncio.sleep(0.6)
                
                if p2p_price_rub and p2p_price_rub > 0:
                    # Конвертируем в USD
                    price_usd = p2p_price_rub / usd_to_rub
                    
                    # Используем изменение за 24ч из batch запроса к CoinGecko
                    price_change = symbol_to_24h_change.get(symbol, saved_prices.get(symbol, {}).get("usd_24h_change", 0.0))
                    
                    prices[symbol] = {
                        "usd": price_usd,
                        "rub": p2p_price_rub,
                        "usd_24h_change": price_change,
                    }
                    logger.info(f"✅ {symbol}: Цена получена С BINANCE P2P (RUB) - ${price_usd:.2f} / ₽{p2p_price_rub:.2f} (24h: {price_change:+.1f}%)")
                else:
                    # Попробуем получить цену в USD, если RUB недоступна
                    logger.debug(f"Пробуем получить цену {symbol} в USD с Binance P2P...")
                    p2p_price_usd_str = await self.get_binance_p2p_price(asset, "USD")
                    await asyncio.sleep(0.6)
                    
                    if p2p_price_usd_str and p2p_price_usd_str > 0:
                        # Цена уже в USD, конвертируем в RUB
                        price_usd = float(p2p_price_usd_str)
                        price_rub = price_usd * usd_to_rub
                        price_change = symbol_to_24h_change.get(symbol, saved_prices.get(symbol, {}).get("usd_24h_change", 0.0))
                        
                        prices[symbol] = {
                            "usd": price_usd,
                            "rub": price_rub,
                            "usd_24h_change": price_change,
                        }
                        logger.info(f"✅ {symbol}: Цена получена С BINANCE P2P (USD) - ${price_usd:.2f} / ₽{price_rub:.2f} (24h: {price_change:+.1f}%)")
                    else:
                        # Fallback на CoinGecko, если нет на Binance P2P
                        logger.warning(f"⚠️ {symbol}: Монета недоступна на Binance P2P (RUB/USD), используем CoinGecko")
                        if symbol in self.coin_gecko_mapping:
                            gecko_id = self.coin_gecko_mapping[symbol]
                            if gecko_id in gecko_24h_changes:
                                gecko_data = gecko_24h_changes[gecko_id]
                                prices[symbol] = gecko_data
                                logger.info(f"✅ {symbol}: Цена получена С COINGECKO (fallback) - ${gecko_data.get('usd', 0):,.2f} / ₽{gecko_data.get('rub', 0):,.0f}")
                            else:
                                # Если CoinGecko тоже недоступен, используем сохраненные значения
                                if symbol in saved_prices and saved_prices[symbol]["usd"] > 0:
                                    prices[symbol] = saved_prices[symbol]
                                    logger.warning(f"⚠️ {symbol}: Используем сохраненные значения из БД (последний fallback)")
                                else:
                                    logger.error(f"❌ {symbol}: Не удалось получить цену ни из одного источника")
                
            except Exception as e:
                logger.error(f"❌ Ошибка при получении цены для {symbol}: {e}", exc_info=True)
                # Используем сохраненные значения при ошибке
                if symbol in saved_prices and saved_prices[symbol]["usd"] > 0:
                    prices[symbol] = saved_prices[symbol]
                    logger.warning(f"⚠️ {symbol}: Используем сохраненные значения из БД из-за ошибки")
                continue
        
        from datetime import datetime
        logger.info(f"⏰ Время завершения получения цен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📊 ИТОГО: Получены цены для {len(prices)} монет")
        
        return prices

    async def update_coin_prices_and_notify(self):
        from datetime import datetime
        try:
            logger.info("=" * 60)
            logger.info(f"🚀 НАЧАЛО ОБНОВЛЕНИЯ ЦЕН МОНЕТ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            prices = await self.fetch_prices()
            
            if not prices:
                logger.warning("Не удалось получить цены, проверяем сохраненные значения в БД")
                # Если не удалось получить цены, не обновляем БД - оставляем старые значения
                existing_coins = await self.coin_req.get_all_coins()
                if existing_coins:
                    logger.info(f"Используем сохраненные цены для {len(existing_coins)} монет")
                    return
                else:
                    logger.error("Нет сохраненных цен и не удалось получить новые")
                    return

            update_data = {}
            for symbol in self.binance_coin_mapping.keys():
                if symbol in prices:
                    coin_data = prices[symbol]
                    # Обновляем только если цена больше 0
                    if coin_data.get("usd", 0.0) > 0 or coin_data.get("rub", 0.0) > 0:
                        update_data[symbol] = {
                            "price_usd": coin_data.get("usd", 0.0),
                            "price_rub": coin_data.get("rub", 0.0),
                            "price_change": coin_data.get("usd_24h_change", 0.0),
                        }
                        logger.debug(f"✅ {symbol}: Данные подготовлены для обновления БД (USD: ${coin_data.get('usd', 0):.2f}, RUB: ₽{coin_data.get('rub', 0):.2f})")
                    else:
                        logger.warning(f"⚠️ Цена для {symbol} равна 0, пропускаем обновление")

            if update_data:
                await self.coin_req.update_coin_prices(update_data)
                logger.info(f"💾 Цены обновлены в БД для {len(update_data)} монет")
                logger.info(f"⏰ Время обновления БД: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await self.send_price_notification(update_data)
            else:
                logger.warning("⚠️ Нет данных для обновления цен")
            logger.info("=" * 60)
            logger.info(f"✅ ЗАВЕРШЕНО ОБНОВЛЕНИЕ ЦЕН МОНЕТ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении цен: {e}", exc_info=True)

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

            # Курс доллара (USDT/RUB)
            usd_to_rub = await self.get_usd_rub_rate()

            # Сообщение в том же формате, что и в меню "Цены монет"
            message = "💎 Текущие цены монет:\n\n"
            message += f"🔄 Курс доллара: 1 USDT ≈ {usd_to_rub:.2f} RUB\n\n"

            for coin in filtered_coins:
                if coin.symbol in prices_data:
                    data = prices_data[coin.symbol]
                    change_icon = "📈" if data["price_change"] >= 0 else "📉"
                    message += (
                        f"🔸 {coin.symbol} ({coin.name})\n"
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

            # Отправка в канал временно отключена
            # Делаем пост с курсом валют и монет в канал Asic Store (https://t.me/asic_mining_store)
            # await self.bot.send_message(-1001546174824, message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")

    async def get_usd_rub_rate(self) -> float:
        """Получение курса USD/RUB через exchangerate-api.com"""
        logger.info(f"💱 Запрос курса USD/RUB через exchangerate-api.com")
        try:
            async with aiohttp.ClientSession() as session:
                logger.debug(f"📤 Отправка GET запроса к {self.exchange_rate_url}")
                async with session.get(
                    self.exchange_rate_url,
                    timeout=10,
                ) as response:
                    logger.debug(f"📥 Получен ответ от exchangerate-api, статус: {response.status}")
                    response.raise_for_status()
                    data = await response.json()
                    rub_rate = data.get("rates", {}).get("RUB")
                    if rub_rate and rub_rate > 0:
                        logger.info(f"Получен курс USD/RUB: {rub_rate:.2f}")
                        return float(rub_rate)
                    else:
                        logger.warning("Не удалось получить курс RUB из exchangerate-api")
                        return 80.0
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при получении курса USD/RUB: {e}")
            # Fallback на Binance P2P для USDT/RUB
            logger.info("💱 Fallback: получение курса USDT/RUB с Binance P2P...")
            try:
                usdt_rub = await self.get_binance_p2p_price("USDT", "RUB")
                if usdt_rub and usdt_rub > 0:
                    logger.info(f"✅ Получен курс USDT/RUB с Binance P2P (fallback): {usdt_rub:.2f}")
                    return float(usdt_rub)
            except Exception as fallback_error:
                logger.error(f"Ошибка при fallback на Binance P2P: {fallback_error}")
            return 80.0
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
                logger.info("Получение актуальных цен монет из Binance P2P API...")
                prices = await self.fetch_prices()
                
                # Создаем монеты с актуальными ценами или значениями по умолчанию
                for coin_data in coins_to_add:
                    symbol = coin_data["symbol"]
                    
                    # Получаем цену из API, если доступна
                    if prices and symbol in prices:
                        price_data = prices[symbol]
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
            else:
                logger.info("Монеты уже существуют")
