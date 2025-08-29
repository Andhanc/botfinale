import asyncio
from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from signature import Settings
from utils.coin_service import CoinGeckoService
from utils.logger import setup_logger


class BotRunner:
    def __init__(self):
        self.bot_instance = Settings()
        self.scheduler = AsyncIOScheduler()
        self.coin_service = CoinGeckoService(self.bot_instance)

    async def setup(self):
        await self.bot_instance.db_manager.async_main()
        await self.coin_service.initialize_coins()
        from handlers.admin import Admin
        from handlers.client import Client

        await setup_logger(level="DEBUG")
        user_client = Client(bot=self.bot_instance)
        admin_client = Admin(bot=self.bot_instance)
        await user_client.register_handlers()
        await admin_client.register_handler()
        self.setup_scheduler()

    def setup_scheduler(self):
        moscow_tz = pytz.timezone("Europe/Moscow")
        trigger = CronTrigger(hour=10, minute=0, timezone=moscow_tz)
        self.scheduler.add_job(
            self.coin_service.update_coin_prices_and_notify,
            trigger,
            id="daily_price_update",
        )
        self.scheduler.add_job(
            self.coin_service.update_coin_prices_and_notify,
            "date",
            run_date=datetime.now() + timedelta(seconds=5),
        )

    async def run(self):
        await self.setup()
        self.scheduler.start()
        print("Планировщик запущен. Цены будут обновляться ежедневно в 10:00 по Москве")
        try:
            await self.bot_instance.dp.start_polling(self.bot_instance.bot)
        finally:
            self.scheduler.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(BotRunner().run())
    except KeyboardInterrupt:
        print("Bot stopped")
