import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

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
        self.token = os.getenv("BOT_TOKEN")
        if not self.token:
            raise ValueError("BOT_TOKEN not set in .env")
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
