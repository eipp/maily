FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ghostscript \
    libreoffice \
    poppler-utils \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install document generation dependencies
RUN pip install --no-cache-dir \
    reportlab==3.6.12 \
    PyPDF2==3.0.1 \
    python-docx==0.8.11 \
    WeasyPrint==59.0 \
    markdown==3.4.3 \
    pdfkit==1.0.0 \
    xhtml2pdf==0.2.11 \
    python-pptx==0.6.21 \
    openpyxl==3.1.2

# Create necessary directories
RUN mkdir -p /data/documents /data/documents/previews /tmp/mailydocs

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DOCUMENT_STORAGE_PATH=/data/documents
ENV DOCUMENT_BASE_URL=/api/documents
ENV TEMP_DIRECTORY=/tmp/mailydocs

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
