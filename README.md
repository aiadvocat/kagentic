# Kagentic - Extensible AI System

A microservices-based AI system running in Kubernetes that allows for dynamic tool registration and usage. The system consists of a chat interface, an AI agent that can use various tools, and a collection of tools that can register themselves with the agent.

## System Architecture

The system consists of the following components running in the Kubernetes namespace 'kagentic':

- **Frontend**: Streamlit-based chat interface
- **AI Agent**: Core service that processes requests and coordinates with tools
- **Tool Registry**: PostgreSQL database for tool management
- **Tools**:
  - Calculator Tool: Handles mathematical operations
  - Search Tool: Performs web searches using SearchAPI.io

## Prerequisites

- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured to access your cluster
- Docker installed
- Python 3.9+
- OpenAI API key
- SearchAPI.io API key

## Quick Start

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/kagentic.git
    cd kagentic
    ```

2. Create the namespace:
    ```bash
    kubectl create namespace kagentic
    ```

3. Create required secrets:
    ```bash
    # OpenAI API key
    kubectl create secret generic openai-credentials \
      --from-literal=api-key='your-openai-api-key' \
      -n kagentic

    # SearchAPI credentials
    kubectl create secret generic search-api-credentials \
      --from-literal=search-api-key='your-searchapi-key' \
      -n kagentic
    ```

4. Build Docker images:
    ```bash
    chmod +x build.sh
    ./build.sh
    ```

5. Deploy services:
    ```bash
    kubectl apply -f k8s/tool-registry.yaml
    kubectl apply -f k8s/ai-agent.yaml
    kubectl apply -f k8s/search-tool.yaml
    kubectl apply -f k8s/calculator-tool.yaml
    kubectl apply -f k8s/frontend.yaml
    ```

6. Access the application:
    ```bash
    kubectl get svc frontend -n kagentic
    ```
    Access the UI using the LoadBalancer IP/Port or use port-forwarding:
    ```bash
    kubectl port-forward svc/frontend 8501:8501 -n kagentic
    ```

## Detailed Setup

### Local Development

1. Set up Python virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    ```

2. Install dependencies:
    ```bash
    for dir in */requirements.txt; do
        pip install -r "$dir"
    done
    ```

3. Set environment variables:
    ```bash
    export OPENAI_API_KEY='your-openai-api-key'
    export SEARCH_API_KEY='your-searchapi-key'
    ```

### Database Setup

The tool registry database will be automatically initialized when the PostgreSQL container starts. The schema is defined in `tool-registry/init.sql`.

## Monitoring

Check service status:
```bash
kubectl get pods -n kagentic
kubectl logs -f <pod-name> -n kagentic
```

View tool registry database:
```bash
kubectl exec -it <tool-registry-pod> -n kagentic -- psql -U kagentic -d tool_registry
```

## Troubleshooting

1. **Pods not starting**
    ```bash
    kubectl describe pod <pod-name> -n kagentic
    kubectl logs <pod-name> -n kagentic
    ```

2. **Database connection issues**
    ```bash
    kubectl exec -it <ai-agent-pod> -n kagentic -- env | grep DATABASE_URL
    ```

3. **Tool registration failing**
    ```bash
    kubectl logs -f <tool-pod> -n kagentic
    ```

## License

[MIT License](LICENSE)

## Kind Cluster Setup

1. **Install kind**
    ```bash
    # On Linux
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind

    # On macOS
    brew install kind
    ```

2. **Create the cluster**
    ```bash
    # Create cluster using our config
    kind create cluster --config kind-config.yaml

    # Verify cluster is running
    kubectl cluster-info --context kind-kagentic
    ```

3. **Load Docker images into kind**
    ```bash
    # After running ./build.sh, load the images into kind
    kind load docker-image tool-registry:latest --name kagentic
    kind load docker-image ai-agent:latest --name kagentic
    kind load docker-image frontend:latest --name kagentic
    kind load docker-image search-tool:latest --name kagentic
    kind load docker-image calculator-tool:latest --name kagentic
    ```

4. **Special Considerations for kind**
    - Images must be loaded into the kind cluster after building
    - Use NodePort or ClusterIP instead of LoadBalancer
    - Access services via localhost and mapped ports
    - For persistent storage, use local-path provisioner:
    ```bash
    kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
    kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
    ```

### Troubleshooting kind Setup

1. **Image pulling errors**
    ```bash
    # Verify images are loaded
    docker exec -it kagentic-control-plane crictl images
    ```

2. **Storage issues**
    ```bash
    # Check storage class
    kubectl get storageclass
    
    # Check PVC status
    kubectl get pvc -n kagentic
    ```

3. **Port access issues**
    ```bash
    # Verify port mappings
    docker ps --format "{{.Names}}\t{{.Ports}}" | grep kagentic
    ```

4. **Clean up**
    ```bash
    # Delete cluster
    kind delete cluster --name kagentic
    
    # Remove all built images
    docker rmi tool-registry:latest ai-agent:latest frontend:latest search-tool:latest calculator-tool:latest
    ```