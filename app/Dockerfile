# Lightweight Python runtime
FROM python:3.12-slim

# Application root inside the container
WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Expose FastAPI port
EXPOSE 7000

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000"]
