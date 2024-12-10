FROM kagentic-base:latest

# Copy requirements first
COPY web-search-tool/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set up shared module
RUN mkdir -p /app/shared
COPY shared/ /app/shared/

# Copy service code
COPY web-search-tool/ /app/web-search-tool/

WORKDIR /app/web-search-tool
ENV PYTHONPATH=/app
CMD ["python", "app.py"] 