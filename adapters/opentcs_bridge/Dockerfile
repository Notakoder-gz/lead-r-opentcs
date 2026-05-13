# Используем легкий Python
FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем библиотеки для связи
RUN pip install --no-cache-dir \
    eclipse-zenoh \
    requests \
    pyyaml

# Создаем рабочую папку
WORKDIR /app

# Копируем код и конфигурации в образ
COPY . /app/

# Команда запуска
CMD ["python3", "adapter.py"]