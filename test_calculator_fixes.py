#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки исправлений калькулятора
"""
from utils.calculator import MiningCalculator

def test_normalization():
    """Тест нормализации единиц измерения"""
    print("="*60)
    print("ТЕСТ 1: Нормализация единиц измерения")
    print("="*60)
    
    # Тест для SHA-256 (BTC)
    print("\nТест для SHA-256 (Bitcoin):")
    print("-" * 60)
    
    # Данные: майнер 100 TH/s, сеть 650 PH/s = 650_000 TH/s
    miner_hash = 100  # TH/s
    network_hash = 650_000  # TH/s (650 PH/s)
    
    coin_data = {
        "BTC": {
            "price": 110000.0,  # USD
            "network_hashrate": network_hash,  # TH/s
            "block_reward": 3.125,
            "algorithm": "sha256"
        }
    }
    
    result = MiningCalculator.calculate_profitability(
        hash_rate=miner_hash,
        power_consumption=3250.0,  # W
        electricity_price_rub=5.0,  # руб/кВт·ч
        coin_data=coin_data,
        usd_to_rub=80.0,
        algorithm="sha256"
    )
    
    # Проверяем долю майнера
    miner_hash_hs = miner_hash * MiningCalculator.UNIT_MULTIPLIERS["th/s"]
    network_hash_hs = network_hash * MiningCalculator.UNIT_MULTIPLIERS["th/s"]
    expected_share = miner_hash_hs / network_hash_hs
    
    print(f"Майнер: {miner_hash} TH/s = {miner_hash_hs:,.0f} H/s")
    print(f"Сеть: {network_hash} TH/s = {network_hash_hs:,.0f} H/s")
    print(f"Ожидаемая доля: {expected_share:.8f}")
    
    # Получаем daily_coins из periods
    daily_coins = result['periods']['day']['coins_per_coin'].get('BTC', 0)
    print(f"Доход в день: {daily_coins:.8f} BTC")
    print(f"Доход в USD: ${result['daily_income_usd']:.2f}")
    
    # Проверяем, что доля разумная (не слишком малая)
    blocks_per_day = 86400 / 600  # 144 блока в день для BTC
    calculated_share = daily_coins / (blocks_per_day * coin_data["BTC"]["block_reward"])
    print(f"Рассчитанная доля из результата: {calculated_share:.8f}")
    
    if abs(calculated_share - expected_share) < 0.0001:
        print("[OK] ТЕСТ ПРОЙДЕН: Нормализация работает корректно")
    else:
        print("[ОШИБКА] ТЕСТ НЕ ПРОЙДЕН: Доли не совпадают")
    
    return result


def test_coins_calculation():
    """Тест расчета количества монет"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Расчет количества монет")
    print("="*60)
    
    coin_data = {
        "BTC": {
            "price": 110000.0,
            "network_hashrate": 650_000,  # TH/s
            "block_reward": 3.125,
            "algorithm": "sha256"
        },
        "BCH": {
            "price": 350.0,
            "network_hashrate": 3_000,  # TH/s
            "block_reward": 6.25,
            "algorithm": "sha256"
        }
    }
    
    result = MiningCalculator.calculate_profitability(
        hash_rate=100,  # TH/s
        power_consumption=3250.0,
        electricity_price_rub=5.0,
        coin_data=coin_data,
        usd_to_rub=80.0,
        algorithm="sha256"
    )
    
    print("\nПроверка количества монет для разных криптовалют:")
    print("-" * 60)
    
    coins_per_coin = result['periods']['day']['coins_per_coin']
    # Берем первое значение как базовое
    daily_coins = list(coins_per_coin.values())[0] if coins_per_coin else 0
    
    print(f"daily_coins (базовое количество): {daily_coins:.8f}")
    print(f"\nКоличество монет за день:")
    for symbol, coins in coins_per_coin.items():
        print(f"  {symbol}: {coins:.8f}")
        # Проверяем, что для всех монет одинаковое количество
        if abs(coins - daily_coins) < 0.00000001:
            print(f"    [OK] Правильно: совпадает с daily_coins")
        else:
            print(f"    [ОШИБКА] ОШИБКА: не совпадает с daily_coins (разница: {abs(coins - daily_coins)})")
    
    # Проверяем, что доход в USD правильный для каждой монеты
    print(f"\nПроверка дохода в USD:")
    for symbol, coin_info in coin_data.items():
        coins_for_symbol = coins_per_coin.get(symbol, 0)
        expected_income = coins_for_symbol * coin_info["price"]
        actual_income = result['daily_income_usd']  # Это для первой монеты
        print(f"  {symbol}: {coins_for_symbol:.8f} * ${coin_info['price']:,.2f} = ${expected_income:,.2f}")
    
    return result


def test_efficiency_factor():
    """Тест efficiency factor"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Efficiency Factor")
    print("="*60)
    
    coin_data = {
        "BTC": {
            "price": 110000.0,
            "network_hashrate": 650_000,
            "block_reward": 3.125,
            "algorithm": "sha256"
        }
    }
    
    result = MiningCalculator.calculate_profitability(
        hash_rate=100,
        power_consumption=3250.0,
        electricity_price_rub=5.0,
        coin_data=coin_data,
        usd_to_rub=80.0,
        algorithm="sha256"
    )
    
    algo_params = MiningCalculator.get_algorithm_params("sha256")
    efficiency = algo_params["efficiency_factor"]
    
    print(f"Efficiency factor: {efficiency}")
    daily_coins = result['periods']['day']['coins_per_coin'].get('BTC', 0)
    print(f"Доход в день: {daily_coins:.8f} BTC")
    
    if efficiency == 0.98:
        print("[OK] ТЕСТ ПРОЙДЕН: Efficiency factor установлен в 0.98")
    else:
        print(f"[ОШИБКА] ТЕСТ НЕ ПРОЙДЕН: Efficiency factor = {efficiency}, ожидалось 0.98")
    
    return result


def test_scrypt_algorithm():
    """Тест для алгоритма Scrypt"""
    print("\n" + "="*60)
    print("ТЕСТ 4: Алгоритм Scrypt (Litecoin)")
    print("="*60)
    
    # Для Scrypt единицы в MH/s
    miner_hash = 1000  # MH/s
    network_hash = 600_000  # MH/s = 0.6 TH/s
    
    coin_data = {
        "LTC": {
            "price": 94.23,
            "network_hashrate": network_hash,  # MH/s
            "block_reward": 6.25,
            "algorithm": "scrypt"
        }
    }
    
    result = MiningCalculator.calculate_profitability(
        hash_rate=miner_hash,
        power_consumption=1500.0,
        electricity_price_rub=5.0,
        coin_data=coin_data,
        usd_to_rub=80.0,
        algorithm="scrypt"
    )
    
    # Нормализация
    miner_hash_hs = miner_hash * MiningCalculator.UNIT_MULTIPLIERS["mh/s"]
    network_hash_hs = network_hash * MiningCalculator.UNIT_MULTIPLIERS["mh/s"]
    expected_share = miner_hash_hs / network_hash_hs
    
    print(f"Майнер: {miner_hash} MH/s = {miner_hash_hs:,.0f} H/s")
    print(f"Сеть: {network_hash} MH/s = {network_hash_hs:,.0f} H/s")
    print(f"Ожидаемая доля: {expected_share:.8f}")
    daily_coins = result['periods']['day']['coins_per_coin'].get('LTC', 0)
    print(f"Доход в день: {daily_coins:.6f} LTC")
    print(f"Доход в USD: ${result['daily_income_usd']:.2f}")
    
    blocks_per_day = 86400 / 150  # Для Scrypt
    calculated_share = daily_coins / (blocks_per_day * coin_data["LTC"]["block_reward"])
    print(f"Рассчитанная доля: {calculated_share:.8f}")
    
    if abs(calculated_share - expected_share) < 0.0001:
        print("[OK] ТЕСТ ПРОЙДЕН: Scrypt работает корректно")
    else:
        print("[ОШИБКА] ТЕСТ НЕ ПРОЙДЕН")
    
    return result


def main():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ КАЛЬКУЛЯТОРА")
    print("="*60)
    
    try:
        test_normalization()
        test_coins_calculation()
        test_efficiency_factor()
        test_scrypt_algorithm()
        
        print("\n" + "="*60)
        print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ОШИБКА] Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

