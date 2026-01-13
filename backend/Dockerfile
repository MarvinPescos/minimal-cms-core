FROM python:3.11-slim

# 1. Environment Variables for Python optimization (No more pycache)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2. Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# 4. Install system dependencies if needed (e.g., for Postgres/Pillow)
# RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 5. Install dependencies (Cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 6. Copy code
COPY . .

# 7. Switch to non-root user
USER appuser

# 8. Use the Exec form CMD
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]