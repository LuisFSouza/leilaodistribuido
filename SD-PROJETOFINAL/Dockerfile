# syntax=docker/dockerfile:1
FROM python:3.12.7-slim

WORKDIR /server

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "server.py"]
