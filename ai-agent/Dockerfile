FROM kagentic-base:latest

# Copy requirements first
COPY ai-agent/requirements.txt .

# Force reinstall psycopg2-binary
RUN pip uninstall -y psycopg2-binary && \
    pip install --no-cache-dir -r requirements.txt

# Set up shared module
RUN mkdir -p /app/shared
COPY shared/ /app/shared/

# Copy service code
COPY ai-agent/ /app/ai-agent/

WORKDIR /app/ai-agent

# Debug: Check versions
RUN python -c "import psycopg2; print('psycopg2 version:', psycopg2.__version__)"

ENV PYTHONPATH=/app
CMD ["python", "app.py"] 