"""Тестовый скрипт — проверить что YooMoney токен работает."""
import asyncio
from yoomoney import AsyncClient
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    token = os.getenv("YOOMONEY_TOKEN")
    if not token:
        print("❌ YOOMONEY_TOKEN не установлен в .env")
        return
    
    print(f"Токен: {token[:10]}...")
    
    async with AsyncClient(token) as client:
        # 1. Проверить аккаунт
        try:
            user = await client.account_info()
            print(f"✅ Аккаунт: {user.account}")
            print(f"   Баланс: {user.balance}")
        except Exception as e:
            print(f"❌ Ошибка account_info: {e}")
            return
        
        # 2. Проверить историю
        try:
            history = await client.operation_history()
            print(f"✅ История: {len(history.operations)} операций")
            for op in history.operations[:5]:
                print(f"   - label={op.label}, status={op.status}, amount={op.amount}")
        except Exception as e:
            print(f"❌ Ошибка operation_history: {e}")
            print("   → Токен не имеет разрешения 'operation-history'!")
            print("   → Пересоздайте токен с scope=['account-info', 'operation-history']")

asyncio.run(main())
