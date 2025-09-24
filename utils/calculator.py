from datetime import datetime
from typing import Any, Dict, List


class MiningCalculator:
    @staticmethod
    def calculate_profitability(
        hash_rate: float,  # в TH/s
        power_consumption: float,  # в ваттах
        electricity_price_rub: float,
        coin_data: Dict[
            str, Dict
        ],  # {symbol: {price, network_hashrate, block_reward, algorithm}}
        usd_to_rub: float,
    ) -> Dict[str, Any]:

        coin_results = {}
        total_daily_income_usd = 0

        for coin_symbol, coin_info in coin_data.items():
            coin_price = coin_info["price"]
            network_hashrate = coin_info["network_hashrate"]
            block_reward = coin_info["block_reward"]
            algorithm = coin_info.get("algorithm", "sha256")

            block_time = 150 if algorithm == "scrypt" else 600
            blocks_per_day = 86400 / block_time

            share = hash_rate / network_hashrate
            daily_coins = share * blocks_per_day * block_reward
            daily_income_usd = daily_coins * coin_price

            coin_results[coin_symbol] = {
                "daily_coins": daily_coins,
                "daily_income_usd": daily_income_usd,
            }

            total_daily_income_usd += daily_income_usd

        daily_income_rub = total_daily_income_usd * usd_to_rub
        daily_electricity_cost_rub = (
            (power_consumption / 1000) * 24 * electricity_price_rub
        )
        daily_electricity_cost_usd = daily_electricity_cost_rub / usd_to_rub
        daily_profit_usd = total_daily_income_usd - daily_electricity_cost_usd
        daily_profit_rub = daily_income_rub - daily_electricity_cost_rub

        def make_period(multiplier: int) -> Dict[str, Any]:
            return {
                "coins_per_coin": {
                    symbol: info["daily_coins"] * multiplier
                    for symbol, info in coin_results.items()
                },
                "income_usd": total_daily_income_usd * multiplier,
                "income_rub": daily_income_rub * multiplier,
                "electricity_cost_usd": daily_electricity_cost_usd * multiplier,
                "electricity_cost_rub": daily_electricity_cost_rub * multiplier,
                "profit_usd": daily_profit_usd * multiplier,
                "profit_rub": daily_profit_rub * multiplier,
            }

        return {
            "coin_results": coin_results,
            "daily_income_usd": total_daily_income_usd,
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
        equipment_name: str = "",
        hash_rate: float = 0,
        power_consumption: float = 0,
        hash_unit: str = "TH/s",  # ← новый параметр
    ) -> str:
        text = f"🔧 Оборудование: {equipment_name}\n" if equipment_name else ""
        text += f"⚡ Хэшрейт: {hash_rate} {hash_unit}\n" if hash_rate else ""
        text += f"🔌 Потребление: {power_consumption}W\n\n"

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
                if symbol == "BTC":
                    coin_strings.append(f"{coins:.6f} {symbol}")
                elif symbol in ["LTC", "ETH"]:
                    coin_strings.append(f"{coins:.4f} {symbol}")
                else:
                    coin_strings.append(f"{coins:.2f} {symbol}")
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
            if symbol in result.get("coin_data", {}):
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
