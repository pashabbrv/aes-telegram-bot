FROM python:3.9

RUN apt-get update && apt-get install -y poppler-utils

WORKDIR /app

# Копируем зависимости первыми для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всю структуру проекта
COPY . .

CMD ["python", "-m", "bot.bot"]