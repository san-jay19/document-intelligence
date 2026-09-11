FROM python:3.12-slim

# ---------------------------------------------------------
# System dependencies for OCR
# ---------------------------------------------------------

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Application directory
# ---------------------------------------------------------

WORKDIR /app

# ---------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------
# Copy application
# ---------------------------------------------------------

COPY . .

# ---------------------------------------------------------
# Start FastAPI
# ---------------------------------------------------------

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]