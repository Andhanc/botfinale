from datetime import datetime
from typing import Any, Dict


class MiningCalculator:
    @staticmethod
    def calculate_profitability(
        hash_rate_ths: float,
        power_consumption: float,
        electricity_price_rub: float,
        coin_price_usd: float,
        network_hashrate_ths: float,
        block_reward: float,
        usd_to_rub: float,
    ) -> Dict[str, Any]:
        hash_rate_hs = hash_rate_ths * 1e12
        network_hashrate_hs = network_hashrate_ths * 1e12

        blocks_per_day = 86400 / 600

        daily_coins = (
            (hash_rate_hs / network_hashrate_hs) * blocks_per_day * block_reward
        )
        daily_income_usd = daily_coins * coin_price_usd
        daily_income_rub = daily_income_usd * usd_to_rub
        daily_electricity_cost_rub = (
            (power_consumption / 1000) * 24 * electricity_price_rub
        )
        daily_electricity_cost_usd = daily_electricity_cost_rub / usd_to_rub
        daily_profit_usd = daily_income_usd - daily_electricity_cost_usd
        daily_profit_rub = daily_income_rub - daily_electricity_cost_rub

        def make_period(multiplier: int) -> Dict[str, float]:
            return {
                "coins": daily_coins * multiplier,
                "income_usd": daily_income_usd * multiplier,
                "income_rub": daily_income_rub * multiplier,
                "electricity_cost_usd": daily_electricity_cost_usd * multiplier,
                "electricity_cost_rub": daily_electricity_cost_rub * multiplier,
                "profit_usd": daily_profit_usd * multiplier,
                "profit_rub": daily_profit_rub * multiplier,
            }

        periods = {
            "day": make_period(1),
            "week": make_period(7),
            "month": make_period(30),
            "year": make_period(365),
        }

        return {
            "daily_coins": daily_coins,
            "daily_income_usd": daily_income_usd,
            "daily_income_rub": daily_income_rub,
            "daily_electricity_cost_usd": daily_electricity_cost_usd,
            "daily_electricity_cost_rub": daily_electricity_cost_rub,
            "daily_profit_usd": daily_profit_usd,
            "daily_profit_rub": daily_profit_rub,
            "periods": periods,
        }

    @staticmethod
    def format_result(
        result: Dict[str, Any], coin_symbol: str, usd_to_rub: float
    ) -> str:
        text = f"💰 **Результаты расчета**\n\n"

        text += f"📊 **Доход в монетах {coin_symbol}:**\n"
        text += f"— За день: {result['daily_coins']:.8f} {coin_symbol}\n"
        text += f"— За неделю: {result['periods']['week']['coins']:.8f} {coin_symbol}\n"
        text += f"— За месяц: {result['periods']['month']['coins']:.8f} {coin_symbol}\n"
        text += f"— За год: {result['periods']['year']['coins']:.8f} {coin_symbol}\n\n"

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

        text += f"🔄 **Курс доллара:** {usd_to_rub:.2f} руб.\n"
        text += (
            f"📅 *Доходность актуальна на {datetime.now().strftime('%d.%m.%Y %H:%M')}*"
        )

        return text

    @staticmethod
    def format_result_rub(
        result: Dict[str, Any], coin_symbol: str, usd_to_rub: float
    ) -> str:
        text = f"💰 **Результаты расчета в рублях**\n\n"

        text += f"💵 **Доход в рублях:**\n"
        text += f"— За день: {result['daily_income_rub']:.2f} руб.\n"
        text += f"— За неделю: {result['periods']['week']['income_rub']:.2f} руб.\n"
        text += f"— За месяц: {result['periods']['month']['income_rub']:.2f} руб.\n"
        text += f"— За год: {result['periods']['year']['income_rub']:.2f} руб.\n\n"

        text += f"⚡ **Затраты на электроэнергию:**\n"
        text += f"— За день: {result['daily_electricity_cost_rub']:.2f} руб.\n"
        text += f"— За неделю: {result['periods']['week']['electricity_cost_rub']:.2f} руб.\n"
        text += f"— За месяц: {result['periods']['month']['electricity_cost_rub']:.2f} руб.\n"
        text += f"— За год: {result['periods']['year']['electricity_cost_rub']:.2f} руб.\n\n"

        text += f"📈 **Чистая доходность:**\n"
        text += f"— За день: {result['daily_profit_rub']:.2f} руб.\n"
        text += f"— За неделю: {result['periods']['week']['profit_rub']:.2f} руб.\n"
        text += f"— За месяц: {result['periods']['month']['profit_rub']:.2f} руб.\n"
        text += f"— За год: {result['periods']['year']['profit_rub']:.2f} руб.\n\n"

        text += (
            f"📅 *Доходность актуальна на {datetime.now().strftime('%d.%m.%Y %H:%M')}*"
        )

        return text
