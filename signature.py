import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

from config import get_db_url
from database.models import CreateDatabase
from database.request import (
    CalculatorReq,
    CoinReq,
    SellRequestReq,
    UsedDeviceGuideReq,
    UserReq,
)


class Settings:
    def __init__(self):
        # Проверяем, загружен ли .env файл
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if not os.path.exists(env_path):
            raise FileNotFoundError(
                f"Файл .env не найден в {os.path.dirname(__file__)}. "
                f"Создайте файл .env с переменной BOT_TOKEN=ваш_токен"
            )
        
        self.token = os.getenv("BOT_TOKEN")
        if not self.token:
            raise ValueError(
                "BOT_TOKEN не установлен в .env файле. "
                "Добавьте строку: BOT_TOKEN=ваш_токен_бота"
            )
        
        # Проверяем, что токен не является placeholder
        if self.token == "your_bot_token_here" or len(self.token) < 10:
            raise ValueError(
                "BOT_TOKEN в .env файле не настроен. "
                "Замените 'your_bot_token_here' на реальный токен от @BotFather"
            )
        
        self.bot = Bot(
            token=self.token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        )
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db_manager = CreateDatabase(database_url=get_db_url())
        self.user_req = UserReq(self.db_manager.async_session)
        self.calculator_req = CalculatorReq(self.db_manager.async_session)
        self.coin_req = CoinReq(self.db_manager.async_session)
        self.sell_req = SellRequestReq(self.db_manager.async_session)
        self.guide_req = UsedDeviceGuideReq(self.db_manager.async_session)
