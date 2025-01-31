# ИТМО агентский бот API

API-сервис для ответов на вопросы об Университете ИТМО с использованием LLM и поиска по различным источникам.

## Описание

Сервис обрабатывает вопросы об Университете ИТМО, используя:
- Поиск по интернету
- Поиск по новостному порталу news.itmo.ru
- LLM для анализа и генерации ответов

## Тестирование

### Публичный доступ
Сервис доступен по адресу: `78.47.98.169:80/api/request`

### Пример запроса

```bash
curl --location --request POST '78.47.98.169:80/api/request' \
--header 'Content-Type: application/json' \
--data-raw '{
  "query": "В каком городе находится главный кампус Университета ИТМО?\n1. Москва\n2. Санкт-Петербург\n3. Екатеринбург\n4. Нижний Новгород",
  "id": 1
}'
```

### Формат ответа

```json
{
  "id": 1,
  "answer": 2,
  "reasoning": "Согласно информации с официального сайта, главный кампус Университета ИТМО находится в Санкт-Петербурге...",
  "sources": [
    "https://itmo.ru/ru/page/159/kontakty.htm",
    "https://news.itmo.ru/ru/news/123"
  ]
}
```

- `id`: ID запроса
- `answer`: номер правильного варианта (или null для вопросов без вариантов)
- `reasoning`: подробное объяснение ответа
- `sources`: использованные источники информации

## Локальный запуск

### Предварительные требования

- Docker
- Docker Compose
- Файл `.env` с необходимыми переменными окружения:
  ```
  OPENAI_API_KEY=your_key
  GOOGLE_API_KEY=your_key
  GOOGLE_CSE_ID=your_cse_id
  ```

### Запуск

```bash
docker-compose up -d
```

После запуска сервис будет доступен по адресу: `http://localhost:80/api/request`

### Остановка

```bash
docker-compose down
```

