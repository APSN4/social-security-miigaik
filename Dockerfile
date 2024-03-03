# Используем базовый образ Python 3.12.1
FROM python:3.12.1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем все файлы из текущей директории внутрь контейнера
COPY . .

RUN pip install --no-cache-dir -r requrements.txt

CMD ["python", "main.py"]
