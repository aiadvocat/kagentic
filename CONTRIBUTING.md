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

2. Implement the required endpoints in app.py:
```python
@app.route('/api/health', methods=['GET'])
def health_check():
    # Implement health check
    return jsonify({"status": "healthy"})

@app.route('/api/<your-endpoint>', methods=['POST'])
def your_tool_endpoint():
    # Implement your tool's functionality
    pass
```

3. Register with the AI Agent:
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

4. Create Kubernetes deployment in k8s/your-tool.yaml:
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
        image: your-tool:latest
        ports:
        - containerPort: 5000
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