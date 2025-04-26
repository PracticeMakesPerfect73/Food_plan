FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=FoodBot.settings

EXPOSE 8000

CMD ["python", "Bot/run.py"]
