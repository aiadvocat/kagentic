#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to build a Docker image
build_image() {
    local service=$1
    local image_name=$2
    echo -e "${YELLOW}Building ${service} image...${NC}"
    
    if docker build -t ${image_name}:latest ./${service}; then
        echo -e "${GREEN}Successfully built ${service}${NC}"
        return 0
    else
        echo -e "${RED}Failed to build ${service}${NC}"
        return 1
    fi
}

# Array of services to build
services=(
    "tool-registry:tool-registry"
    "ai-agent:ai-agent"
    "frontend:frontend"
    "web-search-tool:search-tool"
    "example-tool:calculator-tool"
)

# Counter for failed builds
failed=0

# Build each service
for service in "${services[@]}"; do
    IFS=':' read -r -a array <<< "$service"
    directory="${array[0]}"
    image_name="${array[1]}"
    
    if [ -d "$directory" ]; then
        if ! build_image "$directory" "$image_name"; then
            ((failed++))
        fi
    else
        echo -e "${RED}Directory $directory not found${NC}"
        ((failed++))
    fi
done

# Summary
echo
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All images built successfully${NC}"
    exit 0
else
    echo -e "${RED}${failed} build(s) failed${NC}"
    exit 1
fi 