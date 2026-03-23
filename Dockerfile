FROM python:3.12-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Flask будет слушать на 8080
EXPOSE 8080

# Запуск через gunicorn (production-режим)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
