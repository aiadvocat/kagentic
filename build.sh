#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VERSION_TAG=${VERSION_TAG:-"0.1.0"}  # Can be overridden by environment variable
DOCKER_ID=${DOCKER_ID:-"eurogig"}      # Can be overridden by environment variable
PREFIX=${PREFIX:-"kagentic"}         # Can be overridden by environment variable

# Function to build a Docker image
build_image() {
    local service=$1
    local image_name=$2
    local full_image_name="${DOCKER_ID}/${PREFIX}-${image_name}:${VERSION_TAG}"
    
    echo -e "${YELLOW}Building ${service} image as ${full_image_name}...${NC}"
    
    if docker build -t ${full_image_name} -f ${service}/Dockerfile .; then
        # Also tag as latest and for local use
        docker tag ${full_image_name} "${DOCKER_ID}/${PREFIX}-${image_name}:latest"
        docker tag ${full_image_name} "${PREFIX}-${image_name}:latest"
        echo -e "${GREEN}Successfully built ${service}${NC}"
        return 0
    else
        echo -e "${RED}Failed to build ${service}${NC}"
        return 1
    fi
}

# Array of services to build
services=(
    ".:base"  # Build base image first
    "tool-registry:tool-registry"
    "ai-agent:ai-agent"
    "frontend:frontend"
    "web-search-tool:search-tool"
    "example-tool:calculator-tool"
)

# Counter for failed builds
failed=0

echo -e "${YELLOW}Building images with:${NC}"
echo -e "  Docker ID: ${DOCKER_ID}"
echo -e "  Prefix: ${PREFIX}"
echo -e "  Version: ${VERSION_TAG}"

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
    echo -e "${YELLOW}Cleaning up dangling images...${NC}"
    docker image prune -f
    echo -e "\nImage list:"
    for service in "${services[@]}"; do
        IFS=':' read -r -a array <<< "$service"
        image_name="${array[1]}"
        echo -e "${DOCKER_ID}/${PREFIX}-${image_name}:${VERSION_TAG}"
        echo -e "${DOCKER_ID}/${PREFIX}-${image_name}:latest"
    done

    # Prompt for pushing images
    echo -e "\n${YELLOW}Would you like to push the images to Docker Hub? (y/N)${NC}"
    read -r push_response
    
    if [[ "$push_response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Pushing images to Docker Hub...${NC}"
        
        # Check if logged in to Docker Hub
        if ! docker info 2>/dev/null | grep -q "Username"; then
            echo -e "${YELLOW}Please log in to Docker Hub:${NC}"
            docker login
        fi
        
        # Push each image
        for service in "${services[@]}"; do
            IFS=':' read -r -a array <<< "$service"
            image_name="${array[1]}"
            full_image_name="${DOCKER_ID}/${PREFIX}-${image_name}"
            
            echo -e "${YELLOW}Pushing ${full_image_name}:${VERSION_TAG}${NC}"
            if docker push "${full_image_name}:${VERSION_TAG}"; then
                echo -e "${YELLOW}Pushing ${full_image_name}:latest${NC}"
                docker push "${full_image_name}:latest"
            else
                echo -e "${RED}Failed to push ${full_image_name}${NC}"
                exit 1
            fi
        done
        echo -e "${GREEN}All images pushed successfully${NC}"
    else
        echo -e "${YELLOW}Skipping image push${NC}"
    fi

    exit 0
else
    echo -e "${RED}${failed} build(s) failed${NC}"
    exit 1
fi 