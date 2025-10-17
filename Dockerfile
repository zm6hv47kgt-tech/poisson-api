FROM python:3.11-slim

# optimizări de bază
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# instalăm dependențele
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copiem codul
COPY main.py .

# variabile implicite (le suprascrii în Render)
ENV API_KEYS="" \
    CORS_ALLOW_ORIGINS="*" \
    MU_DEFAULT=1.35 \
    HOME_ADV=1.10

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
