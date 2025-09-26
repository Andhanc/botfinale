from datetime import datetime
from typing import Any, Dict, List


class MiningCalculator:
    @staticmethod
    def calculate_profitability(
        hash_rate: float,
        power_consumption: float,
        electricity_price_rub: float,
        coin_data: Dict[str, Dict],
        usd_to_rub: float,
    ) -> Dict[str, Any]:

        first_coin = list(coin_data.keys())[0]
        info = coin_data[first_coin]

        algorithm = info.get("algorithm", "sha256")
        block_time = 150 if algorithm == "scrypt" else 600
        blocks_per_day = 86400 / block_time
        share = hash_rate / info["network_hashrate"]
        daily_coins_first = share * blocks_per_day * info["block_reward"]
        daily_income_usd = daily_coins_first * info["price"]

        daily_income_rub = daily_income_usd * usd_to_rub
        daily_electricity_cost_rub = (
            (power_consumption / 1000) * 24 * electricity_price_rub
        )
        daily_electricity_cost_usd = daily_electricity_cost_rub / usd_to_rub
        daily_profit_usd = daily_income_usd - daily_electricity_cost_usd
        daily_profit_rub = daily_income_rub - daily_electricity_cost_rub

        def make_period(multiplier: int) -> Dict[str, Any]:
            coins_per_coin = {}
            for symbol, coin in coin_data.items():
                coins_per_coin[symbol] = (daily_income_usd / coin["price"]) * multiplier
            return {
                "coins_per_coin": coins_per_coin,
                "income_usd": daily_income_usd * multiplier,
                "income_rub": daily_income_rub * multiplier,
                "electricity_cost_usd": daily_electricity_cost_usd * multiplier,
                "electricity_cost_rub": daily_electricity_cost_rub * multiplier,
                "profit_usd": daily_profit_usd * multiplier,
                "profit_rub": daily_profit_rub * multiplier,
            }

        return {
            "daily_income_usd": daily_income_usd,
            "daily_income_rub": daily_income_rub,
            "daily_electricity_cost_usd": daily_electricity_cost_usd,
            "daily_electricity_cost_rub": daily_electricity_cost_rub,
            "daily_profit_usd": daily_profit_usd,
            "daily_profit_rub": daily_profit_rub,
            "periods": {
                "day": make_period(1),
                "week": make_period(7),
                "month": make_period(30),
                "year": make_period(365),
            },
            "coin_data": coin_data,
        }

    @staticmethod
    def format_result(
        result: Dict[str, Any],
        coin_symbols: List[str],
        usd_to_rub: float,
    ) -> str:
        text = f"\n"

        text += f"💰 **Результаты расчета**\n\n"
        text += f"📊 **Доход в монетах:**\n"
        for period_name, period_display in [
            ("day", "день"),
            ("week", "неделю"),
            ("month", "месяц"),
            ("year", "год"),
        ]:
            coin_strings = []
            for symbol in coin_symbols:
                coins = result["periods"][period_name]["coins_per_coin"][symbol]
                coin_strings.append(
                    f"{coins:.6f} {symbol}"
                    if symbol == "BTC"
                    else f"{coins:.4f} {symbol}"
                )
            text += f"— За {period_display}: {' | '.join(coin_strings)}\n"

        text += f"\n💵 **Доход в долларах:**\n"
        for period, name in [
            ("day", "день"),
            ("week", "неделю"),
            ("month", "месяц"),
            ("year", "год"),
        ]:
            val = result["periods"][period]["income_usd"]
            text += f"— За {name}: ${val:.2f}\n"

        text += f"\n⚡ **Затраты на электроэнергию:**\n"
        for period, name in [
            ("day", "день"),
            ("week", "неделю"),
            ("month", "месяц"),
            ("year", "год"),
        ]:
            val = result["periods"][period]["electricity_cost_usd"]
            text += f"— За {name}: ${val:.2f}\n"

        text += f"\n📈 **Чистая доходность:**\n"
        for period, name in [
            ("day", "день"),
            ("week", "неделю"),
            ("month", "месяц"),
            ("year", "год"),
        ]:
            val = result["periods"][period]["profit_usd"]
            text += f"— За {name}: ${val:.2f}\n"

        text += f"\n🔄 Курс доллара: {usd_to_rub:.2f} руб.\n"
        for symbol in coin_symbols:
            price = result["coin_data"][symbol]["price"]
            text += f"💰 Курс {symbol}: ${price:.4f}\n"

        text += (
            f"\n📅 Доходность актуальна на {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        return text

    @staticmethod
    def format_result_rub(
        result: Dict[str, Any], coin_symbols: List[str], usd_to_rub: float
    ) -> str:
        text = f"💰 **Результаты расчета в рублях**\n\n"
        text += f"💵 **Доход в рублях:**\n"
        for period, name in [
            ("day", "день"),
            ("week", "неделю"),
            ("month", "месяц"),
            ("year", "год"),
        ]:
            val = result["periods"][period]["income_rub"]
            text += f"— За {name}: {val:.2f} руб.\n"

        text += f"\n⚡ **Затраты на электроэнергию:**\n"
        for period, name in [
            ("day", "день"),
            ("week", "неделю"),
            ("month", "месяц"),
            ("year", "год"),
        ]:
            val = result["periods"][period]["electricity_cost_rub"]
            text += f"— За {name}: {val:.2f} руб.\n"

        text += f"\n📈 **Чистая доходность:**\n"
        for period, name in [
            ("day", "день"),
            ("week", "неделю"),
            ("month", "месяц"),
            ("year", "год"),
        ]:
            val = result["periods"][period]["profit_rub"]
            text += f"— За {name}: {val:.2f} руб.\n"

        text += (
            f"\n📅 Доходность актуальна на {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        return text
