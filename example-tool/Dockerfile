FROM kagentic-base:latest

# Copy requirements first
COPY example-tool/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set up shared module
RUN mkdir -p /app/shared
COPY shared/ /app/shared/

# Copy service code
COPY example-tool/ /app/example-tool/

WORKDIR /app/example-tool
ENV PYTHONPATH=/app
CMD ["python", "app.py"] 