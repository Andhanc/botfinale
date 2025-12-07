#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест формулы capminer.ru
"""
from utils.calculator import MiningCalculator

def test_capminer_formula():
    """Тест формулы на данных из скриншотов"""
    
    print("="*70)
    print("ТЕСТ ФОРМУЛЫ CAPMINER.RU")
    print("="*70)
    
    # Тест 1: BTC
    print("\n1. ТЕСТ BTC | SHA-256:")
    print("-"*70)
    btc_data = {
        "BTC": {
            "price": 92355.92,
            "network_hashrate": 1_068_844_948,  # TH/s (из capminer)
            "block_reward": 3.125,
            "algorithm": "sha256"
        }
    }
    
    result_btc = MiningCalculator.calculate_profitability(
        hash_rate=100,  # TH/s
        power_consumption=3000,
        electricity_price_rub=0.12 * 80,
        coin_data=btc_data,
        usd_to_rub=80.0,
        algorithm="sha256",
        pool_fee=0.015,
        electricity_price_usd=0.12
    )
    
    our_btc = result_btc['periods']['day']['coins_per_coin']['BTC']
    our_btc_usd = result_btc['periods']['day']['income_usd']
    expected_btc = 0.00004147
    expected_btc_usd = 3.83
    
    print(f"Ожидается: {expected_btc:.8f} BTC = ${expected_btc_usd:.2f}")
    print(f"Получено:  {our_btc:.8f} BTC = ${our_btc_usd:.2f}")
    diff = abs(our_btc - expected_btc) / expected_btc * 100
    print(f"Разница:   {diff:.2f}%")
    
    if diff < 1:
        print("[OK] BTC расчет совпадает!")
    else:
        print("[ОШИБКА] BTC расчет не совпадает")
    
    # Тест 2: LTC
    print("\n2. ТЕСТ LTC | Scrypt:")
    print("-"*70)
    ltc_data = {
        "LTC": {
            "price": 83.66,
            "network_hashrate": 3_367_490,  # GH/s (из capminer)
            "block_reward": 6.25,
            "algorithm": "scrypt"
        }
    }
    
    result_ltc = MiningCalculator.calculate_profitability(
        hash_rate=100,  # GH/s
        power_consumption=3000,
        electricity_price_rub=0.12 * 80,
        coin_data=ltc_data,
        usd_to_rub=80.0,
        algorithm="scrypt",
        pool_fee=0.015,
        electricity_price_usd=0.12
    )
    
    our_ltc = result_ltc['periods']['day']['coins_per_coin']['LTC']
    our_ltc_usd = result_ltc['periods']['day']['income_usd']
    expected_ltc = 0.10530097
    expected_ltc_usd = 8.81
    
    print(f"Ожидается: {expected_ltc:.8f} LTC = ${expected_ltc_usd:.2f}")
    print(f"Получено:  {our_ltc:.8f} LTC = ${our_ltc_usd:.2f}")
    diff = abs(our_ltc - expected_ltc) / expected_ltc * 100
    print(f"Разница:   {diff:.2f}%")
    
    if diff < 1:
        print("[OK] LTC расчет совпадает!")
    else:
        print("[ОШИБКА] LTC расчет не совпадает")
    
    # Тест 3: DOGE
    print("\n3. ТЕСТ DOGE | Scrypt:")
    print("-"*70)
    doge_data = {
        "DOGE": {
            "price": 0.15,
            "network_hashrate": 2_958_883,  # GH/s (из capminer)
            "block_reward": 10000,
            "block_time": 60,  # DOGE блок каждую минуту (не 150 как LTC!)
            "algorithm": "scrypt"
        }
    }
    
    result_doge = MiningCalculator.calculate_profitability(
        hash_rate=100,  # GH/s
        power_consumption=3000,
        electricity_price_rub=0.12 * 80,
        coin_data=doge_data,
        usd_to_rub=80.0,
        algorithm="scrypt",
        pool_fee=0.015,
        electricity_price_usd=0.12
    )
    
    our_doge = result_doge['periods']['day']['coins_per_coin']['DOGE']
    our_doge_usd = result_doge['periods']['day']['income_usd']
    expected_doge = 479.37003261
    expected_doge_usd = 71.31
    
    print(f"Ожидается: {expected_doge:.2f} DOGE = ${expected_doge_usd:.2f}")
    print(f"Получено:  {our_doge:.2f} DOGE = ${our_doge_usd:.2f}")
    diff = abs(our_doge - expected_doge) / expected_doge * 100
    print(f"Разница:   {diff:.2f}%")
    
    if diff < 1:
        print("[OK] DOGE расчет совпадает!")
    else:
        print("[ОШИБКА] DOGE расчет не совпадает")

if __name__ == "__main__":
    test_capminer_formula()

