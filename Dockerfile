FROM python:3.11-slim

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Копируем манифест зависимостей
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Копируем код бота
COPY bot/ ./bot/

CMD ["uv", "run", "python", "bot/main.py"]
