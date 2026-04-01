FROM python:3.11-slim

WORKDIR /app

# Copy requirements first so pip install is cached independently of source changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV MODEL_NAME=mistralai/mamba-codestral-7b-v0.1
ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
