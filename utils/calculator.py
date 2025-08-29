from datetime import datetime
from typing import Any, Dict


class MiningCalculator:
    @staticmethod
    def calculate_profitability(
        hash_rate: float,
        power_consumption: float,
        electricity_price: float,
        coin_price: float,
        algorithm_data: Dict[str, Any],
        usd_to_rub: float = 80.0,
    ) -> Dict[str, Any]:
        """
        Расчет доходности майнинга
        """
        # Упрощенный расчет (реальная формула зависит от алгоритма)
        daily_coins = (
            (hash_rate / algorithm_data["network_hashrate"])
            * algorithm_data["block_reward"]
            * 144
        )
        daily_income_usd = daily_coins * coin_price

        # Затраты на электроэнергию
        daily_power_kwh = (power_consumption * 24) / 1000
        daily_electricity_cost_usd = daily_power_kwh * electricity_price
        daily_profit_usd = daily_income_usd - daily_electricity_cost_usd

        # Расчет для разных периодов
        periods = {"day": 1, "week": 7, "month": 30, "year": 365}

        result = {
            "daily_coins": daily_coins,
            "daily_income_usd": daily_income_usd,
            "daily_electricity_cost_usd": daily_electricity_cost_usd,
            "daily_profit_usd": daily_profit_usd,
            "periods": {},
        }

        for period_name, days in periods.items():
            result["periods"][period_name] = {
                "coins": daily_coins * days,
                "income_usd": daily_income_usd * days,
                "electricity_cost_usd": daily_electricity_cost_usd * days,
                "profit_usd": daily_profit_usd * days,
                "income_rub": daily_income_usd * days * usd_to_rub,
                "electricity_cost_rub": daily_electricity_cost_usd * days * usd_to_rub,
                "profit_rub": daily_profit_usd * days * usd_to_rub,
            }

        return result

    @staticmethod
    def format_result(
        result: Dict[str, Any], coin_symbol: str, usd_to_rub: float = 80.0
    ) -> str:
        """
        Форматирование результатов расчета
        """
        text = f"💰 **Результаты расчета**\n\n"

        text += f"📊 **Доход в монетах {coin_symbol}:**\n"
        text += f"— За день: {result['daily_coins']:.2f} {coin_symbol}\n"
        text += f"— За неделю: {result['periods']['week']['coins']:.2f} {coin_symbol}\n"
        text += f"— За месяц: {result['periods']['month']['coins']:.2f} {coin_symbol}\n"
        text += f"— За год: {result['periods']['year']['coins']:.2f} {coin_symbol}\n\n"

        text += f"💵 **Доход в долларах:**\n"
        text += f"— За день: ${result['daily_income_usd']:.2f}\n"
        text += f"— За неделю: ${result['periods']['week']['income_usd']:.2f}\n"
        text += f"— За месяц: ${result['periods']['month']['income_usd']:.2f}\n"
        text += f"— За год: ${result['periods']['year']['income_usd']:.2f}\n\n"

        text += f"⚡ **Затраты на электроэнергию:**\n"
        text += f"— За день: ${result['daily_electricity_cost_usd']:.2f}\n"
        text += (
            f"— За неделю: ${result['periods']['week']['electricity_cost_usd']:.2f}\n"
        )
        text += (
            f"— За месяц: ${result['periods']['month']['electricity_cost_usd']:.2f}\n"
        )
        text += (
            f"— За год: ${result['periods']['year']['electricity_cost_usd']:.2f}\n\n"
        )

        text += f"📈 **Чистая доходность:**\n"
        text += f"— За день: ${result['daily_profit_usd']:.2f}\n"
        text += f"— За неделю: ${result['periods']['week']['profit_usd']:.2f}\n"
        text += f"— За месяц: ${result['periods']['month']['profit_usd']:.2f}\n"
        text += f"— За год: ${result['periods']['year']['profit_usd']:.2f}\n\n"

        text += f"🔄 **Курс доллара:** {usd_to_rub} руб.\n"
        text += (
            f"📅 *Доходность актуальна на {datetime.now().strftime('%d.%m.%Y %H:%M')}*"
        )

        return text

    @staticmethod
    def format_result_rub(
        result: Dict[str, Any], coin_symbol: str, usd_to_rub: float = 80.0
    ) -> str:
        """
        Форматирование результатов расчета в рублях
        """
        text = f"💰 **Результаты расчета в рублях**\n\n"

        text += f"💵 **Доход в рублях:**\n"
        text += f"— За день: {result['periods']['day']['income_rub']:.2f} руб.\n"
        text += f"— За неделю: {result['periods']['week']['income_rub']:.2f} руб.\n"
        text += f"— За месяц: {result['periods']['month']['income_rub']:.2f} руб.\n"
        text += f"— За год: {result['periods']['year']['income_rub']:.2f} руб.\n\n"

        text += f"⚡ **Затраты на электроэнергию:**\n"
        text += (
            f"— За день: {result['periods']['day']['electricity_cost_rub']:.2f} руб.\n"
        )
        text += f"— За неделю: {result['periods']['week']['electricity_cost_rub']:.2f} руб.\n"
        text += f"— За месяц: {result['periods']['month']['electricity_cost_rub']:.2f} руб.\n"
        text += f"— За год: {result['periods']['year']['electricity_cost_rub']:.2f} руб.\n\n"

        text += f"📈 **Чистая доходность:**\n"
        text += f"— За день: {result['periods']['day']['profit_rub']:.2f} руб.\n"
        text += f"— За неделю: {result['periods']['week']['profit_rub']:.2f} руб.\n"
        text += f"— За месяц: {result['periods']['month']['profit_rub']:.2f} руб.\n"
        text += f"— За год: {result['periods']['year']['profit_rub']:.2f} руб.\n\n"

        text += (
            f"📅 *Доходность актуальна на {datetime.now().strftime('%d.%m.%Y %H:%M')}*"
        )

        return text
