FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

WORKDIR /app/app

ENTRYPOINT ["functions-framework", "--target", "translate_pages_event", "--port", "8080", "--host", "0.0.0.0"]
