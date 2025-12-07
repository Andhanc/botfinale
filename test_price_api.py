#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест получения цен из CoinGecko API
"""
import asyncio
from utils.coin_service import CoinGeckoService
from signature import Settings

async def test_price_fetching():
    """Тест получения цен из API"""
    print("="*60)
    print("ТЕСТ: Получение цен из CoinGecko API")
    print("="*60)
    
    settings = Settings()
    coin_service = CoinGeckoService(settings)
    
    # Тест получения цен
    print("\n1. Получение цен из API...")
    prices = await coin_service.fetch_prices()
    
    if prices:
        print(f"[OK] Получены цены для {len(prices)} монет")
        print("\nПримеры цен:")
        print("-" * 60)
        
        # Показываем несколько примеров
        examples = ["bitcoin", "ethereum", "litecoin", "kaspa"]
        for coin_id in examples:
            if coin_id in prices:
                data = prices[coin_id]
                print(f"{coin_id.upper()}:")
                print(f"  USD: ${data.get('usd', 0):,.2f}")
                print(f"  RUB: {data.get('rub', 0):,.0f} руб")
                print(f"  24h change: {data.get('usd_24h_change', 0):+.2f}%")
                print()
    else:
        print("[ОШИБКА] Не удалось получить цены из API")
        return False
    
    # Тест обновления цен в БД
    print("\n2. Обновление цен в базе данных...")
    try:
        await coin_service.update_coin_prices_and_notify()
        print("[OK] Цены обновлены в базе данных")
    except Exception as e:
        print(f"[ОШИБКА] Ошибка при обновлении: {e}")
        return False
    
    # Проверяем цены в БД
    print("\n3. Проверка цен в базе данных...")
    coins = await coin_service.coin_req.get_all_coins()
    
    if coins:
        print(f"[OK] Найдено {len(coins)} монет в базе")
        print("\nЦены в базе данных:")
        print("-" * 60)
        for coin in coins[:5]:  # Показываем первые 5
            print(f"{coin.symbol}: ${coin.current_price_usd:,.2f} | {coin.current_price_rub:,.0f} руб")
    else:
        print("[ВНИМАНИЕ] Монеты не найдены в базе данных")
    
    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_price_fetching())
        if result:
            print("\n[OK] Все тесты пройдены успешно")
        else:
            print("\n[ОШИБКА] Некоторые тесты не прошли")
    except Exception as e:
        print(f"\n[ОШИБКА] Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()


