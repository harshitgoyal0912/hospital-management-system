FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml uv.lock* ./

# Install UV for faster dependency management
RUN pip install uv

# Install dependencies
# Install from uv.lock so the image matches the tested resolution. The previous
# `uv pip install --system -e .` re-resolved from pyproject and ignored the lock,
# which is how an upstream major release could reach the image untested.
RUN if [ -f uv.lock ]; then \
        uv export --frozen --no-dev --no-emit-project -o /tmp/requirements.txt && \
        uv pip install --system -r /tmp/requirements.txt; \
    fi
RUN uv pip install --system --no-deps -e .

# Copy application code
COPY . .

# Create uploads directory for PDF files
RUN mkdir -p uploads && chmod 755 uploads

# Create medical knowledge database directory
RUN mkdir -p medical_knowledge_db && chmod 755 medical_knowledge_db

# Make startup script executable
RUN chmod +x start.sh

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m appuser
# Create and set permissions for appuser home directory
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser && chmod 755 /home/appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the server
CMD ["./start.sh"]
