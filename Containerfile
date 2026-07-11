# ---- Dockerfile for the application ----
# Adjust base image and commands as needed for your stack.

FROM python:3.14-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM python:3.14-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Expose port (adjust if your app uses a different port)
EXPOSE 3000

# Command to run the application
# Replace with your actual entrypoint (e.g., uvicorn, gunicorn, node, etc.)
CMD ["python", "-m", "app.main"]