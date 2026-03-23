#!/bin/bash
#
# set-tag.sh — Create and push a release tag.
#
# Usage:
#   bash set-tag.sh v1.0.0          # Create draft release tag
#   bash set-tag.sh v1.0.0-stable   # Create stable release tag
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
if [[ $# -ne 1 ]]; then
    echo -e "${RED}Error: Missing tag argument${NC}"
    echo "Usage: bash set-tag.sh <version>"
    echo "Examples:"
    echo "  bash set-tag.sh v1.0.0"
    echo "  bash set-tag.sh v1.0.0-stable"
    exit 1
fi

TAG="$1"

# Validate tag format
if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-stable)?$ ]]; then
    echo -e "${RED}Error: Invalid tag format: $TAG${NC}"
    echo "Expected: v1.0.0 or v1.0.0-stable"
    exit 1
fi

echo -e "${YELLOW}Creating and pushing tag: $TAG${NC}"

git tag "$TAG" || {
    echo -e "${RED}Error: Failed to create tag $TAG (may already exist)${NC}"
    exit 1
}

git push origin "$TAG" || {
    echo -e "${RED}Error: Failed to push tag${NC}"
    git tag -d "$TAG"  # Clean up local tag on failure
    exit 1
}

echo -e "${GREEN}✓ Tag created and pushed: $TAG${NC}"
