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
    
    conn = aiohttp.TCPConnector(limit=20)  # ограничиваем количество одновременных соединений
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        all_results = []
        active_tasks = set()
        request_id = 1
        total_requests = 100  # общее количество запросов для отправки
        
        # Продолжаем, пока не обработаем все запросы
        while len(all_results) < total_requests:
            # Добавляем новые задачи, пока их меньше 20
            while len(active_tasks) < 20 and request_id <= total_requests:
                task = asyncio.create_task(make_request(session, request_id))
                active_tasks.add(task)
                request_id += 1
            
            # Ждем завершения любой задачи
            done, pending = await asyncio.wait(
                active_tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Обрабатываем завершенные задачи
            for completed_task in done:
                result = await completed_task
                all_results.append(result)
                active_tasks.remove(completed_task)
            
            # Выводим прогресс
            print(f"\rОбработано запросов: {len(all_results)}/100, "
                  f"Активных запросов: {len(active_tasks)}", end="")
    
    print("\n")  # Новая строка после прогресс-бара
    end_time = time.time()
    duration = end_time - start_time
    
    # Анализ результатов
    success_count = sum(1 for _, status in all_results if status == 200)
    
    print(f"\nЗавершено тестирование: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Общее время выполнения: {duration:.2f} секунд ({duration/60:.2f} минут)")
    print(f"Успешных запросов (код 200): {success_count} из 100")
    
    # Вывод неуспешных запросов
    if success_count < 100:
        print("\nНеуспешные запросы:")
        for req_id, status in all_results:
            if status != 200:
                print(f"Запрос {req_id}: статус {status}")

if __name__ == "__main__":
    asyncio.run(main())