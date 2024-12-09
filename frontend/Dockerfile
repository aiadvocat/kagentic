FROM kagentic-base:latest

# Copy requirements first
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY frontend/ /app/frontend/

WORKDIR /app/frontend
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"] 