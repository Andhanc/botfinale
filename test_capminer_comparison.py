#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Сравнение нашего калькулятора с capminer.ru
Данные из скриншота
"""
from utils.calculator import MiningCalculator

def test_capminer_comparison():
    """Тест сравнения с capminer.ru"""
    print("="*60)
    print("СРАВНЕНИЕ С CALCULATOR CAPMINER.RU")
    print("="*60)
    
    # Данные из скриншота
    hashrate = 100  # TH/s
    power = 3000  # Вт
    electricity_price_usd = 0.12  # $/кВт-ч
    pool_fee = 0.015  # 1.5%
    algorithm = "sha256"
    
    # Результаты с capminer.ru
    capminer_daily_btc = 0.00004147
    capminer_daily_usd = 3.83
    capminer_electricity_btc = 0.00005318
    capminer_electricity_usd = 4.91
    capminer_profit_btc = -0.00001171
    capminer_profit_usd = -1.08
    
    # Вычисляем цену BTC из их данных
    btc_price_1 = capminer_daily_usd / capminer_daily_btc
    btc_price_2 = capminer_electricity_usd / capminer_electricity_btc
    btc_price = (btc_price_1 + btc_price_2) / 2
    
    print(f"\nВходные данные:")
    print(f"  Хэшрейт: {hashrate} TH/s")
    print(f"  Потребление: {power} Вт")
    print(f"  Цена энергии: {electricity_price_usd} $/кВт-ч")
    print(f"  Комиссия пула: {pool_fee * 100}%")
    print(f"  Цена BTC (вычислена): ${btc_price:,.2f}")
    
    # Данные сети BTC (примерные, нужно уточнить)
    # Для BTC: ~650 PH/s = 650,000 TH/s
    network_hashrate_btc = 650_000  # TH/s
    block_reward_btc = 3.125
    block_time_btc = 600  # секунд
    
    coin_data = {
        "BTC": {
            "price": btc_price,
            "network_hashrate": network_hashrate_btc,
            "block_reward": block_reward_btc,
            "algorithm": "sha256"
        }
    }
    
    # Наш расчет БЕЗ комиссии пула
    print("\n" + "="*60)
    print("НАШ РАСЧЕТ БЕЗ КОМИССИИ ПУЛА")
    print("="*60)
    
    result_no_fee = MiningCalculator.calculate_profitability(
        hash_rate=hashrate,
        power_consumption=power,
        electricity_price_rub=electricity_price_usd * 80,  # Конвертируем в рубли
        coin_data=coin_data,
        usd_to_rub=80.0,
        algorithm="sha256",
        pool_fee=0.0,
        electricity_price_usd=electricity_price_usd
    )
    
    our_daily_coins_no_fee = result_no_fee['periods']['day']['coins_per_coin'].get('BTC', 0)
    our_daily_usd_no_fee = result_no_fee['periods']['day']['income_usd']
    our_electricity_usd_no_fee = result_no_fee['periods']['day']['electricity_cost_usd']
    our_profit_usd_no_fee = result_no_fee['periods']['day']['profit_usd']
    
    print(f"Доход: {our_daily_coins_no_fee:.8f} BTC (${our_daily_usd_no_fee:.2f})")
    print(f"Электроэнергия: ${our_electricity_usd_no_fee:.2f}")
    print(f"Прибыль: ${our_profit_usd_no_fee:.2f}")
    
    # Наш расчет С комиссией пула
    print("\n" + "="*60)
    print("НАШ РАСЧЕТ С КОМИССИЕЙ ПУЛА (1.5%)")
    print("="*60)
    
    result_with_fee = MiningCalculator.calculate_profitability(
        hash_rate=hashrate,
        power_consumption=power,
        electricity_price_rub=electricity_price_usd * 80,
        coin_data=coin_data,
        usd_to_rub=80.0,
        algorithm="sha256",
        pool_fee=pool_fee,
        electricity_price_usd=electricity_price_usd
    )
    
    our_daily_coins = result_with_fee['periods']['day']['coins_per_coin'].get('BTC', 0)
    our_daily_usd = result_with_fee['periods']['day']['income_usd']
    our_electricity_usd = result_with_fee['periods']['day']['electricity_cost_usd']
    our_profit_usd = result_with_fee['periods']['day']['profit_usd']
    
    print(f"Доход: {our_daily_coins:.8f} BTC (${our_daily_usd:.2f})")
    print(f"Электроэнергия: ${our_electricity_usd:.2f}")
    print(f"Прибыль: ${our_profit_usd:.2f}")
    
    # Сравнение
    print("\n" + "="*60)
    print("СРАВНЕНИЕ С CAPMINER.RU")
    print("="*60)
    
    print(f"\nДоход:")
    print(f"  Capminer: {capminer_daily_btc:.8f} BTC (${capminer_daily_usd:.2f})")
    print(f"  Наш:      {our_daily_coins:.8f} BTC (${our_daily_usd:.2f})")
    diff_income_pct = abs(our_daily_coins - capminer_daily_btc) / capminer_daily_btc * 100
    print(f"  Разница:  {diff_income_pct:.2f}%")
    
    print(f"\nЭлектроэнергия:")
    print(f"  Capminer: ${capminer_electricity_usd:.2f}")
    print(f"  Наш:      ${our_electricity_usd:.2f}")
    diff_electricity_pct = abs(our_electricity_usd - capminer_electricity_usd) / capminer_electricity_usd * 100
    print(f"  Разница:  {diff_electricity_pct:.2f}%")
    
    print(f"\nПрибыль:")
    print(f"  Capminer: ${capminer_profit_usd:.2f}")
    print(f"  Наш:      ${our_profit_usd:.2f}")
    diff_profit_pct = abs(our_profit_usd - capminer_profit_usd) / abs(capminer_profit_usd) * 100 if capminer_profit_usd != 0 else 0
    print(f"  Разница:  {diff_profit_pct:.2f}%")
    
    # Анализ
    print("\n" + "="*60)
    print("АНАЛИЗ")
    print("="*60)
    
    if diff_income_pct < 5:
        print("[OK] Доход совпадает с capminer.ru (разница < 5%)")
    else:
        print(f"[ВНИМАНИЕ] Доход отличается на {diff_income_pct:.2f}%")
        print("  Возможные причины:")
        print("  - Разные данные о network_hashrate")
        print("  - Разные значения block_reward")
        print("  - Разные efficiency factors")
    
    if diff_electricity_pct < 1:
        print("[OK] Электроэнергия совпадает с capminer.ru")
    else:
        print(f"[ВНИМАНИЕ] Электроэнергия отличается на {diff_electricity_pct:.2f}%")
    
    # Проверяем расчет электроэнергии вручную
    manual_electricity = (power / 1000) * 24 * electricity_price_usd
    print(f"\nПроверка электроэнергии (вручную):")
    print(f"  (3000 Вт / 1000) * 24 ч * $0.12 = ${manual_electricity:.2f}")
    print(f"  Capminer: ${capminer_electricity_usd:.2f}")
    print(f"  Наш:      ${our_electricity_usd:.2f}")

if __name__ == "__main__":
    test_capminer_comparison()


