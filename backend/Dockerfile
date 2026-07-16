FROM python:3.11-slim

# Prevent python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Prevent python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /backend

# Install system dependencies required for building Python extensions
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend codebase files
COPY . .

EXPOSE 8000

# Start ASGI application server in production mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
