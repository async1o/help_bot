# help_bot — Telegram бот поддержки

## Запуск через Docker

1. Скопируйте `.env.example` в `.env` и заполните значения:
   ```bash
   cp .env.example .env
   # Отредактируйте .env
   ```

2. Запустите:
   ```bash
   docker compose up -d --build
   ```

3. Проверьте логи:
   ```bash
   docker compose logs -f bot
   ```

4. Остановить:
   ```bash
   docker compose down
   ```

   С удалением данных БД:
   ```bash
   docker compose down -v
   ```

## Локальный запуск (для разработки)

```bash
cd bot
python main.py
```

В `.env` укажите `DB_HOST=localhost` для локального запуска.

## Структура проекта

```
├── bot/                    # Исходный код бота
│   ├── main.py             # Точка входа (запуск бота)
│   ├── test_yoomoney.py    # Тест YooMoney токена
│   └── src/
│       ├── db/             # База данных (подключение, репозитории)
│       ├── filters/        # aiogram фильтры
│       ├── handlers/       # Обработчики сообщений и callback
│       ├── keyboards/      # Клавиатуры
│       ├── models/         # SQLAlchemy модели
│       ├── schemas/        # Pydantic схемы
│       ├── services/       # Бизнес-логика
│       ├── states/         # FSM состояния
│       ├── storage/        # Хранилище диалогов
│       └── utils/          # Утилиты (конфиг, платежи)
├── .env.example            # Пример переменных окружения
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Роли

- **Пользователь** — `/start`, `/sos` для отправки запроса
- **Оператор** — принимает запросы, общается в чате, `/stop_dialog` для завершения
- **Администратор** — `/admin`, `/add_operator`, `/delete_operator`, `/add_admin`, `/delete_admin`
