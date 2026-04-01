FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 user
USER user

EXPOSE 7860
ENV PORT=7860
ENV MODEL_NAME=mistralai/mamba-codestral-7b-v0.1
ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]