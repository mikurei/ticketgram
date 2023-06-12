FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY ./src /app/
CMD ["python","bot.py"]