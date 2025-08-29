# fill_coins.py
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import async_sessionmaker

from database.models import Algorithm, Coin, CreateDatabase


async def fill_coins():
    # Подключаемся к БД
    db_url = f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}/{os.getenv("POSTGRES_NAME")}'
    db_manager = CreateDatabase(database_url=db_url)

    # Создаем таблицы если их нет
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(CreateDatabase.metadata.create_all)

    # Данные для добавления
    coins_data = [
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "coin_gecko_id": "bitcoin",
            "algorithm": Algorithm.SHA256,
            "current_price_usd": 45000.0,
            "current_price_rub": 3600000.0,
            "price_change_24h": 0.0,
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "coin_gecko_id": "ethereum",
            "algorithm": Algorithm.ETCHASH,
            "current_price_usd": 2500.0,
            "current_price_rub": 200000.0,
            "price_change_24h": 0.0,
        },
        {
            "symbol": "KAS",
            "name": "Kaspa",
            "coin_gecko_id": "kaspa",
            "algorithm": Algorithm.KHEAVYHASH,
            "current_price_usd": 0.087,
            "current_price_rub": 7.0,
            "price_change_24h": 0.0,
        },
        {
            "symbol": "LTC",
            "name": "Litecoin",
            "coin_gecko_id": "litecoin",
            "algorithm": Algorithm.SCRYPT,
            "current_price_usd": 75.0,
            "current_price_rub": 6000.0,
            "price_change_24h": 0.0,
        },
        {
            "symbol": "DOGE",
            "name": "Dogecoin",
            "coin_gecko_id": "dogecoin",
            "algorithm": Algorithm.SCRYPT,
            "current_price_usd": 0.15,
            "current_price_rub": 12.0,
            "price_change_24h": 0.0,
        },
        {
            "symbol": "USDT",
            "name": "Tether",
            "coin_gecko_id": "tether",
            "algorithm": Algorithm.SHA256,  # USDT работает на разных блокчейнах
            "current_price_usd": 1.0,
            "current_price_rub": 80.0,
            "price_change_24h": 0.0,
        },
    ]

    async with db_manager.async_session() as session:
        # Проверяем, есть ли уже монеты
        from sqlalchemy import select

        existing_coins = await session.execute(select(Coin))
        if existing_coins.scalars().first():
            print("Монеты уже существуют в базе!")
            return

        # Добавляем монеты
        for coin_data in coins_data:
            coin = Coin(**coin_data)
            session.add(coin)

        await session.commit()
        print("✅ Монеты успешно добавлены в базу!")

        # Показываем добавленные монеты
        result = await session.execute(select(Coin))
        coins = result.scalars().all()
        for coin in coins:
            print(f"{coin.symbol} - {coin.name}")


if __name__ == "__main__":
    asyncio.run(fill_coins())
