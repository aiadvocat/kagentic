# Contributing to Kagentic

We love your input! We want to make contributing to Kagentic as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Adding New Tools

1. Create a new directory for your tool:
```
my-new-tool/
├── app.py
├── Dockerfile
└── requirements.txt
```

2. Required dependencies in requirements.txt:
```
flask==2.0.1
requests==2.26.0
python-dotenv==0.19.0
werkzeug==2.0.3  # Required for Flask compatibility
psycopg2-binary==2.9.9  # Required for database connection
sqlalchemy==1.4.23  # Required for shared database module
```

3. Implement the required endpoints in app.py:
```python
import threading
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        logger.info("Health check called")
        # Verify your tool's core functionality
        # Example: check configuration, test basic operation, etc.
        if your_tool_is_healthy():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.error("Health check failed")
            return jsonify({
                "status": "unhealthy",
                "error": "Specific error message",
                "timestamp": datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/<your-endpoint>', methods=['POST'])
def your_tool_endpoint():
    # Implement your tool's functionality
    pass

def register_with_agent():
    while True:
        try:
            logger.info("Attempting to register with AI Agent...")
            response = requests.post(
                'http://ai-agent:5000/api/tools/register',
                json={
                    "name": "Your Tool Name",
                    "description": "Description of what your tool does",
                    "endpoint_url": "http://your-tool:5000/api/your-endpoint",
                    "capabilities": ["list", "of", "capabilities"]
                },
                timeout=5
            )
            if response.status_code == 200:
                logger.info("Successfully registered with AI Agent")
                break
            else:
                logger.error(f"Registration failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register with AI Agent: {e}")
            time.sleep(10)  # Wait before retrying

def send_heartbeat():
    while True:
        try:
            logger.debug("Sending heartbeat...")
            response = requests.post(
                'http://ai-agent:5000/api/tools/heartbeat',
                json={"name": "Your Tool Name"},
                timeout=5
            )
            if response.status_code == 200:
                logger.debug("Heartbeat successful")
            else:
                logger.warning(f"Heartbeat failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
        time.sleep(60)  # Send heartbeat every minute

if __name__ == '__main__':
    # Start registration and heartbeat in separate threads
    threading.Thread(target=register_with_agent, daemon=True).start()
    threading.Thread(target=send_heartbeat, daemon=True).start()

    app.run(host='0.0.0.0', port=5000)
```

4. Create Dockerfile:
```dockerfile
FROM kagentic-base:latest

# Copy requirements first
COPY my-new-tool/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set up shared module
RUN mkdir -p /app/shared
COPY shared/ /app/shared/

# Copy service code
COPY my-new-tool/ /app/my-new-tool/

WORKDIR /app/my-new-tool
ENV PYTHONPATH=/app
CMD ["python", "app.py"]
```

5. Register with the AI Agent:
```python
def register_with_agent():
    response = requests.post(
        'http://ai-agent:5000/api/tools/register',
        json={
            "name": "Your Tool Name",
            "description": "Description of what your tool does",
            "endpoint_url": "http://your-tool:5000/api/your-endpoint",
            "capabilities": ["list", "of", "capabilities"]
        }
    )
```

6. Create Kubernetes deployment in k8s/your-tool.yaml:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: your-tool
  namespace: kagentic
spec:
  ports:
    - port: 5000
      targetPort: 5000
  selector:
    app: your-tool
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: your-tool
  namespace: kagentic
spec:
  replicas: 1
  selector:
    matchLabels:
      app: your-tool
  template:
    metadata:
      labels:
        app: your-tool
    spec:
      containers:
      - name: your-tool
        image: docker.io/library/kagentic-your-tool:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 5000
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Code Style

- Use Python type hints
- Follow PEP 8 guidelines
- Add docstrings to functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing

1. Unit Tests:
```bash
python -m pytest tests/
```

2. Integration Tests:
```bash
./integration_tests.sh
```

3. Local Development:
```bash
docker-compose up
```

## Pull Request Process

1. Update the README.md with details of changes to the interface
2. Update the requirements.txt if you've added new dependencies
3. Update the version numbers in any examples files to the new version
4. The PR will be merged once you have the sign-off of at least one maintainer

## Bug Reports

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License

By contributing, you agree that your contributions will be licensed under its MIT License. 

### Tool Lifecycle
Each tool must:
1. Register with the AI Agent on startup
2. Send regular heartbeats to maintain active status
3. Implement a health check endpoint
4. Handle graceful shutdown

The heartbeat mechanism ensures that only active tools are available to the AI Agent. 
If a tool fails to send a heartbeat for 5 minutes, it will be considered inactive and 
won't be used for processing requests. 