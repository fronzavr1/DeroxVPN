FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ДИАГНОСТИКА: показываем, какие файлы есть
RUN echo "=== ФАЙЛЫ В /app ===" && ls -la

# ДИАГНОСТИКА: проверяем, что app.py существует
RUN test -f app.py && echo "✅ app.py найден" || echo "❌ app.py ОТСУТСТВУЕТ!"

# ДИАГНОСТИКА: проверяем синтаксис app.py
RUN python -m py_compile app.py && echo "✅ app.py синтаксически верен" || echo "❌ Ошибка синтаксиса в app.py!"

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "app.py"]
