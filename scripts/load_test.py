import aiohttp
import asyncio
import time
from datetime import datetime

async def make_request(session, request_id):
    url = "http://78.47.98.169:80/api/request"
    payload = {
        "query": "В каком рейтинге (по состоянию на 2021 год) ИТМО впервые вошёл в топ-400 мировых университетов?\n1. ARWU (Shanghai Ranking)\n2. Times Higher Education (THE) World University Rankings\n3. QS World University Rankings\n4. U.S. News & World Report Best Global Universities",
        "id": 15
    }

    
    try:
        timeout = aiohttp.ClientTimeout(total=3600)  # таймаут 1 час
        async with session.post(url, json=payload, timeout=timeout) as response:
            await response.text()  # дожидаемся получения тела ответа
            status = response.status
            return request_id, status
    except asyncio.TimeoutError:
        return request_id, "Ошибка: Таймаут"
    except Exception as e:
        return request_id, f"Ошибка: {str(e)}"

async def main():
    start_time = time.time()
    print(f"Начало тестирования: {datetime.now().strftime('%H:%M:%S')}")
    
    # Настраиваем сессию с увеличенными таймаутами
    conn = aiohttp.TCPConnector(limit=20)  # ограничиваем количество одновременных соединений
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = []
        for i in range(100):
            task = asyncio.create_task(make_request(session, i + 1))
            tasks.append(task)
            await asyncio.sleep(0.1)  # добавляем задержку 100мс между запросами
        
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Анализ результатов
    success_count = sum(1 for _, status in results if status == 200)
    
    print(f"\nЗавершено тестирование: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Общее время выполнения: {duration:.2f} секунд ({duration/60:.2f} минут)")
    print(f"Успешных запросов (код 200): {success_count} из 100")
    
    # Вывод неуспешных запросов
    if success_count < 100:
        print("\nНеуспешные запросы:")
        for req_id, status in results:
            if status != 200:
                print(f"Запрос {req_id}: статус {status}")

if __name__ == "__main__":
    asyncio.run(main())