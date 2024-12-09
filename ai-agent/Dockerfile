FROM kagentic-base:latest

# Copy requirements first
COPY ai-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY ai-agent/ /app/ai-agent/

WORKDIR /app/ai-agent
ENV PYTHONPATH=/app
CMD ["python", "app.py"] 