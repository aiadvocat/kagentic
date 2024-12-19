#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check for docker
    if ! command_exists docker; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    # Check for kind
    if ! command_exists kind; then
        echo -e "${RED}kind is not installed. Please install kind first.${NC}"
        exit 1
    fi

    # Check for kubectl
    if ! command_exists kubectl; then
        echo -e "${RED}kubectl is not installed. Please install kubectl first.${NC}"
        exit 1
    fi

    echo -e "${GREEN}All prerequisites met!${NC}"
}

# Function to create and configure the kind cluster
setup_cluster() {
    echo -e "${YELLOW}Setting up kind cluster...${NC}"
    
    # Delete existing cluster if it exists
    if kind get clusters | grep -q "^kagentic$"; then
        echo -e "${YELLOW}Existing cluster found. Deleting...${NC}"
        kind delete cluster --name kagentic
    fi

    # Create new cluster
    if kind create cluster --name kagentic --config=- <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30501
    hostPort: 30501
    protocol: TCP
EOF
    then
        echo -e "${GREEN}Cluster created successfully!${NC}"
    else
        echo -e "${RED}Failed to create cluster${NC}"
        exit 1
    fi

    # Set up storage class
    echo -e "${YELLOW}Setting up storage class...${NC}"
    kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
    kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
}

# Function to build and load images
build_and_load_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    
    # Make build script executable and run it
    chmod +x build.sh
    if ! ./build.sh; then
        echo -e "${RED}Failed to build images${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Loading images into kind cluster...${NC}"
    images=(
        "kagentic-tool-registry:latest"
        "kagentic-ai-agent:latest"
        "kagentic-frontend:latest"
        "kagentic-search-tool:latest"
        "kagentic-calculator-tool:latest"
    )

    for image in "${images[@]}"; do
        echo -e "${YELLOW}Loading $image...${NC}"
        if ! kind load docker-image "$image" --name kagentic; then
            echo -e "${RED}Failed to load $image${NC}"
            exit 1
        fi
    done
}

# Function to deploy applications
deploy_applications() {
    echo -e "${YELLOW}Creating namespace...${NC}"
    kubectl create namespace kagentic

    echo -e "${YELLOW}Creating secrets...${NC}"
    if [ -z "$OPENAI_API_KEY" ] || [ -z "$SEARCH_API_KEY" ]; then
        echo -e "${RED}Please set OPENAI_API_KEY and SEARCH_API_KEY environment variables${NC}"
        exit 1
    fi

    kubectl create secret generic openai-credentials \
        --from-literal=api-key="$OPENAI_API_KEY" \
        -n kagentic

    kubectl create secret generic search-api-credentials \
        --from-literal=search-api-key="$SEARCH_API_KEY" \
        -n kagentic

    echo -e "${YELLOW}Deploying applications...${NC}"
    kubectl apply -f k8s/tool-registry.yaml
    kubectl apply -f k8s/ai-agent.yaml
    kubectl apply -f k8s/search-tool.yaml
    kubectl apply -f k8s/calculator-tool.yaml
    kubectl apply -f k8s/frontend.yaml
}

# Function to verify deployment
verify_deployment() {
    echo -e "${YELLOW}Waiting for pods to be ready...${NC}"
    kubectl wait --for=condition=ready pod -l app -n kagentic --timeout=300s

    echo -e "${YELLOW}Checking pod status...${NC}"
    kubectl get pods -n kagentic

    echo -e "${GREEN}Setup complete! Access the application at http://localhost:30501${NC}"
}

# Main execution
echo -e "${YELLOW}Starting Kagentic setup...${NC}"

check_prerequisites
setup_cluster
build_and_load_images
deploy_applications
verify_deployment

echo -e """
${GREEN}Setup completed successfully!${NC}

To access the application:
1. Open http://localhost:30501 in your browser
2. Monitor pods with: kubectl get pods -n kagentic
3. View logs with: kubectl logs -f <pod-name> -n kagentic

To clean up:
1. Delete cluster: kind delete cluster --name kagentic
2. Remove images: docker rmi $(docker images 'kagentic/*' -q)
""" 

