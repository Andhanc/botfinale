from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Algorithm, Manufacturer


class CalculatorKB:
    @staticmethod
    async def choose_method() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="ASIC-майнер", callback_data="calc_method:asic")
        builder.button(text="По хешрейту", callback_data="calc_method:hashrate")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def choose_manufacturer() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for manufacturer in Manufacturer:
            builder.button(
                text=manufacturer.value,
                callback_data=f"calc_manufacturer:{manufacturer.value}",
            )
        builder.button(text="🔙 Назад", callback_data="back_calc_method")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    async def result_menu_rub() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="💵 Рассчитать в долларах", callback_data="calc_usd")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def choose_asic_models(models: list) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for model in models:
            builder.button(text=model.name, callback_data=f"calc_model:{model.id}")
        builder.button(text="🔙 Назад", callback_data="back_calc_manufacturer")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def choose_algorithm() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for algorithm in Algorithm:
            builder.button(
                text=algorithm.value, callback_data=f"calc_algorithm:{algorithm.value}"
            )
        builder.button(text="🔙 Назад", callback_data="back_calc_method")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    async def back_to_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        return builder.as_markup()

    @staticmethod
    async def electricity_input() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back_calc_model")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def hashrate_input() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back_calc_algorithm")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def power_input() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back_calc_hashrate")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def result_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Рассчитать в рублях", callback_data="calc_rub")
        builder.button(text="🔙 Главное меню", callback_data="back_main")
        builder.adjust(1)
        return builder.as_markup()
