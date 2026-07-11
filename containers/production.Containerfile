# Production Build Stage
FROM python:3.14-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runner Stage
FROM python:3.14-slim as runner

WORKDIR /app

# Create a non-privileged user to run app safely
RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local
COPY . .

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV ENV=production

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
