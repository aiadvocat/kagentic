FROM kagentic-base:latest

# Copy requirements first
COPY example-tool/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY example-tool/ /app/example-tool/

WORKDIR /app/example-tool
CMD ["python", "app.py"] 