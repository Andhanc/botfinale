from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import (
    Algorithm,
    AlgorithmData,
    AsicModel,
    AsicModelLine,
    Coin,
    Manufacturer,
)


class AdminKB:
    @staticmethod
    async def admin_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Рассылка", callback_data="broadcast_start")
        builder.button(text="⚙️ ASIC", callback_data="manage_asic")
        builder.button(text="💰 Монеты", callback_data="manage_coins")
        builder.button(text="⚙️ Алгоритмы", callback_data="manage_algorithms")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()

    # ---------- ASIC ----------
    @staticmethod
    async def list_asic_lines(lines: list[AsicModelLine]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for line in lines:
            builder.button(
                text=f"{line.manufacturer.value} {line.name}",
                callback_data=f"view_line:{line.id}",
            )
        builder.button(text="➕ Добавить ASIC", callback_data="add_asic")
        builder.button(text="🔙 Назад", callback_data="admin_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def list_asic_models(
        models: list[AsicModel], line_id: int
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for model in models:
            builder.button(
                text=f"{model.name}", callback_data=f"delete_asic:{model.id}"
            )
        builder.button(text="🔙 Назад к линейкам", callback_data="manage_asic")
        builder.button(text="🗑️ Удалить линейку", callback_data=f"delete_line:{line_id}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def choose_manufacturer_add() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for m in Manufacturer:
            builder.button(text=m.value, callback_data=f"add_manufacturer:{m.name}")
        builder.button(text="🔙 Назад", callback_data="manage_asic")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    async def choose_algorithm_add() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for a in Algorithm:
            builder.button(text=a.value, callback_data=f"add_algorithm:{a.name}")
        builder.button(text="🔙 Назад", callback_data="add_asic")
        builder.adjust(2)
        return builder.as_markup()

    # ---------- Coins ----------
    @staticmethod
    async def list_coins(coins: list[Coin]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for c in coins:
            builder.button(
                text=f"{c.symbol}: ${c.current_price_usd}",
                callback_data=f"edit_coin:{c.symbol}",
            )
        builder.button(text="🔙 Назад", callback_data="admin_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def broadcast_back() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="admin_menu")
        return builder.as_markup()

    # ---------- Algorithms ----------
    @staticmethod
    async def list_algorithms(algorithms: list[AlgorithmData]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for a in algorithms:
            builder.button(
                text=f"{a.algorithm.value} ({a.default_coin})",
                callback_data=f"edit_algo:{a.algorithm.name}",
            )
        builder.button(text="🔙 Назад", callback_data="admin_menu")
        builder.adjust(1)
        return builder.as_markup()

    # ---------- Reply ----------
    @staticmethod
    async def reply_to_user(user_id: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="💬 Ответить", callback_data=f"reply_user:{user_id}")
        return builder.as_markup()
