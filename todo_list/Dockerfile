# Используем минималистичный образ Python 3.10 на основе Debian Buster
FROM python:3.10-slim-buster

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./config ./config/
COPY ./todo/ ./todo/
COPY ./manage.py ./

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]