# database/models.py
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)


# --- ENUMS -------------------------------------------------------------


class UserStatus(str, Enum):
    USER = "user"
    ADMIN = "admin"


class Algorithm(str, Enum):
    SHA256 = "SHA-256"
    SCRYPT = "Scrypt"
    ETCHASH = "Etchash/Ethash"
    KHEAVYHASH = "kHeavyHash"
    BLAKE2S = "Blake2S"
    BLAKE2B_SHA3 = "Blake2B+SHA3"


class Manufacturer(str, Enum):
    BITMAIN = "Bitmain"
    WHATSMINER = "Whatsminer"
    ICERIVER = "Ice River"
    GOLDSHELL = "Goldshell"
    IPOLLO = "iPollo"
    OTHER = "Другой"


# --- TABLES ------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    uid = Column(BigInteger, nullable=False, unique=True)
    uname = Column(String(50))
    status = Column(SQLEnum(UserStatus), default=UserStatus.USER)
    notifications = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    sell_requests = relationship("SellRequest", back_populates="user")


class Coin(Base):
    __tablename__ = "coins"

    symbol = Column(String(10), nullable=False, unique=True)
    name = Column(String(50), nullable=False)
    coin_gecko_id = Column(String(50), nullable=False)
    algorithm = Column(SQLEnum(Algorithm), nullable=False)
    current_price_usd = Column(Float, default=0.0)
    current_price_rub = Column(Float, default=0.0)
    price_change_24h = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.now())


class AsicModelLine(Base):
    __tablename__ = "asic_model_lines"

    name = Column(String(100), nullable=False)  # Например: "S19", "M50", "T21"
    manufacturer = Column(SQLEnum(Manufacturer), nullable=False)
    algorithm = Column(SQLEnum(Algorithm), nullable=False)

    # Связь с конкретными модификациями
    models = relationship("AsicModel", back_populates="model_line")


class AsicModel(Base):
    __tablename__ = "asic_models"

    name = Column(String(100), nullable=False)  # Например: "S19 Pro", "S19j Pro 110TH"
    model_line_id = Column(Integer, ForeignKey("asic_model_lines.id"))
    hash_rate = Column(Float, nullable=False)
    power_consumption = Column(Float, nullable=False)
    get_coin = Column(String(), default="")
    is_active = Column(Boolean, default=True)

    # Связи
    model_line = relationship("AsicModelLine", back_populates="models")
    sell_requests = relationship("SellRequest", back_populates="device")


class AlgorithmData(Base):
    __tablename__ = "algorithm_data"

    algorithm = Column(SQLEnum(Algorithm), nullable=False, unique=True)
    default_coin = Column(String(10), nullable=False)
    difficulty = Column(Float, default=0.0)
    network_hashrate = Column(Float, default=0.0)
    block_reward = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.now)


class SellRequest(Base):
    __tablename__ = "sell_requests"

    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(Integer, ForeignKey("asic_models.id"))
    price = Column(Float, nullable=False)
    condition = Column(String(20), nullable=False)
    description = Column(Text)
    contact_info = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="sell_requests")
    device = relationship("AsicModel", back_populates="sell_requests")


class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    message_text = Column(Text, nullable=False)
    photo_url = Column(String(255))
    sent_at = Column(DateTime, default=datetime.now)
    sent_by = Column(Integer, ForeignKey("users.id"))


class UsedDeviceGuide(Base):
    __tablename__ = "used_device_guide"

    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    last_updated = Column(DateTime, default=datetime.now)
    updated_by = Column(Integer, ForeignKey("users.id"))


class Link(Base):
    __tablename__ = "link"

    link = Column(String(), nullable=False)


# --- ENGINE & SESSION --------------------------------------------------


class CreateDatabase:
    def __init__(self, database_url: str, echo: bool = False) -> None:
        self.engine = create_async_engine(url=database_url, echo=echo)
        self.async_session = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
            autoflush=False,
        )

    @asynccontextmanager
    async def get_session(self):
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def async_main(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Таблицы успешно созданы")

            # Начальные данные (при первом запуске)
            async with self.async_session() as session:
                from sqlalchemy import select

                if not await session.scalar(select(AlgorithmData)):
                    session.add_all(
                        [
                            # Bitcoin (SHA256) - ИСПРАВЛЕНО
                            AlgorithmData(
                                algorithm=Algorithm.SHA256,
                                default_coin="BTC",
                                difficulty=85_000_000_000_000_000,  # 85e15 (реалистично)
                                network_hashrate=650_000_000,  # 200 EH/s
                                block_reward=3.125,  # После халвинга 2024
                            ),
                            # Kaspa (KHEAVYHASH) - ОБНОВЛЕНО
                            AlgorithmData(
                                algorithm=Algorithm.KHEAVYHASH,
                                default_coin="KAS",
                                difficulty=150_000_000_000,  # 150e9 (более реалистично)
                                network_hashrate=300_000,  # 300 PH/s
                                block_reward=100,  # Обновленная награда
                            ),
                            # Ethereum Classic (ETCHASH) - ОБНОВЛЕНО
                            AlgorithmData(
                                algorithm=Algorithm.ETCHASH,
                                default_coin="ETH",
                                difficulty=50_000_000_000_000,  # 50e12
                                network_hashrate=50_000_000,  # 50 TH/s
                                block_reward=2.56,
                            ),
                            # Litecoin (SCRYPT) - ОБНОВЛЕНО
                            AlgorithmData(
                                algorithm=Algorithm.SCRYPT,
                                default_coin="LTC",
                                difficulty=15_000_000,  # 15e6
                                network_hashrate=600_000,  # 600 TH/s
                                block_reward=6.25,  # Обновленная награда
                            ),
                            # Blake2S - ОБНОВЛЕНО
                            AlgorithmData(
                                algorithm=Algorithm.BLAKE2S,
                                default_coin="NEOX",
                                difficulty=200_000_000,  # 200e6
                                network_hashrate=3_000,  # 3 TH/s
                                block_reward=3.5,
                            ),
                            # Blake2B+SHA3 - ОБНОВЛЕНО
                            AlgorithmData(
                                algorithm=Algorithm.BLAKE2B_SHA3,
                                default_coin="KLS",
                                difficulty=3_000_000_000,  # 3e9
                                network_hashrate=200,  # 200 GH/s
                                block_reward=12,
                            ),
                        ]
                    )
                    await session.commit()

                coins_exist = await session.execute(select(Coin))
                if not coins_exist.scalars().first():
                    session.add_all(
                        [
                            Coin(
                                symbol="BTC",
                                name="Bitcoin",
                                coin_gecko_id="bitcoin",
                                algorithm=Algorithm.SHA256,
                                current_price_usd=45000.0,
                                current_price_rub=45000.0 * 90,
                            ),
                            Coin(
                                symbol="KAS",
                                name="Kaspa",
                                coin_gecko_id="kaspa",
                                algorithm=Algorithm.KHEAVYHASH,
                                current_price_usd=0.087,
                                current_price_rub=0.087 * 90,
                            ),
                            Coin(
                                symbol="ETH",
                                name="Ethereum",
                                coin_gecko_id="ethereum-classic",
                                algorithm=Algorithm.ETCHASH,
                                current_price_usd=21.67,
                                current_price_rub=21.67 * 90,
                            ),
                            Coin(
                                symbol="DOGE",
                                name="Dogecoin",
                                coin_gecko_id="dogecoin",
                                algorithm=Algorithm.SCRYPT,
                                current_price_usd=0.23,
                                current_price_rub=0.23 * 90,
                            ),
                            Coin(
                                symbol="LTC",
                                name="Litecoin",
                                coin_gecko_id="litecoin",
                                algorithm=Algorithm.SCRYPT,
                                current_price_usd=120.02,
                                current_price_rub=120.02 * 90,
                            ),
                        ]
                    )
                    await session.commit()
