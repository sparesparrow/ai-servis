#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Hardware Control Server with Conan${NC}"

# Check if Conan is installed
if ! command -v conan &> /dev/null; then
    echo -e "${RED}Conan is not installed. Please install it with: pip install conan${NC}"
    exit 1
fi

# Create build directory
BUILD_DIR="platforms/cpp/build"
mkdir -p "$BUILD_DIR"

# Install dependencies with Conan
echo -e "${YELLOW}Installing dependencies with Conan...${NC}"
cd "$BUILD_DIR"
conan install ../../.. --profile ../../../profiles/linux-release --build missing

# Configure with CMake
echo -e "${YELLOW}Configuring with CMake...${NC}"
TOOLCHAIN_ABS="/workspace/build-release/conan/conan_toolchain.cmake"
cmake -S ../ -B . -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_ABS" -DCMAKE_BUILD_TYPE=Release

# Build
echo -e "${YELLOW}Building...${NC}"
cmake --build . --parallel "$(nproc)"

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}Hardware server executable: ${BUILD_DIR}/hardware-server${NC}"
echo -e "${GREEN}MCP server executable: ${BUILD_DIR}/mcp-server${NC}"
