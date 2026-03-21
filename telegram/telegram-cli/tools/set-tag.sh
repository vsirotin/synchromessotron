#!/bin/bash
#
# set-tag.sh — Create and push a release tag with optional post-task updates.
#
# Usage:
#   bash set-tag.sh v1.0.0          # Create draft release tag, update version files
#   bash set-tag.sh v1.0.0-stable   # Create stable release tag (no version updates)
#
# The script:
# - For v1.0.0: bumps version.yaml, updates release notes + commit text, then tags
# - For v1.0.0-stable: creates a secondary stable tag for the same release
#
# Requirements:
# - Must be run from telegram/telegram-cli directory (where pyproject.toml lives)
# - Requires git to be configured
# - Release notes entry must be provided (interactively)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Defaults
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"  # telegram/telegram-cli
WORKSPACE_ROOT="$(dirname "$(dirname "$(dirname "$PROJECT_ROOT")")")"  # repo root

VERSION_FILE="$PROJECT_ROOT/src/version.yaml"
RELEASE_NOTES="$PROJECT_ROOT/release-notes.md"
COMMIT_TEXT="$WORKSPACE_ROOT/commit-text-proposal.txt"

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

# Detect if this is a stable tag
IS_STABLE=false
if [[ "$TAG" == *"-stable" ]]; then
    IS_STABLE=true
    BASE_TAG="${TAG%-stable}"
else
    BASE_TAG="$TAG"
fi

echo -e "${YELLOW}Creating release tag: $TAG${NC}"
echo "Stable release: $IS_STABLE"
echo "Project root: $PROJECT_ROOT"
echo

# =========================================================================
# If stable tag: just create the tag (release already exists)
# =========================================================================
if [[ "$IS_STABLE" == "true" ]]; then
    echo -e "${YELLOW}Creating stable tag (secondary tag for existing release)...${NC}"
    git tag "$TAG" || {
        echo -e "${RED}Error: Failed to create tag $TAG (may already exist)${NC}"
        exit 1
    }
    git push origin "$TAG" || {
        echo -e "${RED}Error: Failed to push tag ${NC}"
        git tag -d "$TAG"  # Clean up local tag on failure
        exit 1
    }
    echo -e "${GREEN}✓ Stable tag created and pushed: $TAG${NC}"
    exit 0
fi

# =========================================================================
# For regular tag: update version files
# =========================================================================

echo -e "${YELLOW}Updating version files...${NC}"

# Extract version components from tag
VERSION="${TAG#v}"  # Remove 'v' prefix

# Read current version.yaml
if [[ ! -f "$VERSION_FILE" ]]; then
    echo -e "${RED}Error: $VERSION_FILE not found${NC}"
    exit 1
fi

# Parse YAML (simple approach - assumes well-formed file)
CURRENT_VERSION=$(grep "^version:" "$VERSION_FILE" | awk '{print $2}')
CURRENT_BUILD=$(grep "^build:" "$VERSION_FILE" | awk '{print $2}')

echo "Current version: $CURRENT_VERSION (build: $CURRENT_BUILD)"
echo "New version: $VERSION"

# Increment build number
NEW_BUILD=$((CURRENT_BUILD + 1))

# Get current datetime in ISO 8601 format
DATETIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# =========================================================================
# Prompt for release notes entry
# =========================================================================
echo
echo -e "${YELLOW}Enter release notes for version $VERSION:${NC}"
echo "(Press Ctrl+D when done)"
RELEASE_NOTES_ENTRY=$(cat)

if [[ -z "$RELEASE_NOTES_ENTRY" ]]; then
    echo -e "${RED}Error: Release notes entry cannot be empty${NC}"
    exit 1
fi

# =========================================================================
# Update version.yaml
# =========================================================================
echo
echo -e "${YELLOW}Updating version.yaml...${NC}"
cat > "$VERSION_FILE" << EOF
version: $VERSION
build: $NEW_BUILD
datetime: $DATETIME
EOF
echo -e "${GREEN}✓ Updated: version=$VERSION, build=$NEW_BUILD${NC}"

# =========================================================================
# Update release-notes.md
# =========================================================================
echo -e "${YELLOW}Updating release-notes.md...${NC}"

# Create new entry
NEW_ENTRY="## Version: $VERSION
$RELEASE_NOTES_ENTRY
"

# Read existing release notes (skip header)
HEADER=$(head -n 2 "$RELEASE_NOTES")
BODY=$(tail -n +3 "$RELEASE_NOTES")

# Write updated release notes
{
    echo "$HEADER"
    echo ""
    echo "$NEW_ENTRY"
    echo "$BODY"
} > "$RELEASE_NOTES"

echo -e "${GREEN}✓ Updated release-notes.md${NC}"

# =========================================================================
# Update commit-text-proposal.txt at workspace root
# =========================================================================
echo -e "${YELLOW}Updating commit-text-proposal.txt...${NC}"

COMMIT_TEXT_CONTENT="dist: Project: telegram/telegram-cli. Version: $VERSION. Release version $VERSION."

echo "$COMMIT_TEXT_CONTENT" > "$COMMIT_TEXT"
echo -e "${GREEN}✓ Updated commit-text-proposal.txt${NC}"

# =========================================================================
# Create and push tag
# =========================================================================
echo
echo -e "${YELLOW}Creating and pushing tag: $TAG${NC}"

git add "$VERSION_FILE" "$RELEASE_NOTES" "$COMMIT_TEXT"
git tag "$TAG" || {
    echo -e "${RED}Error: Failed to create tag $TAG (may already exist)${NC}"
    echo "Reverting changes..."
    git checkout "$VERSION_FILE" "$RELEASE_NOTES" "$COMMIT_TEXT"
    exit 1
}

git push origin "$TAG" || {
    echo -e "${RED}Error: Failed to push tag${NC}"
    echo "Reverting changes..."
    git tag -d "$TAG"
    git checkout "$VERSION_FILE" "$RELEASE_NOTES" "$COMMIT_TEXT"
    exit 1
}

echo
echo -e "${GREEN}✓ Release tag created and pushed: $TAG${NC}"
echo -e "${GREEN}✓ Version updated to: $VERSION${NC}"
echo
echo "Next steps:"
echo "  1. Monitor the Release workflow on GitHub: https://github.com/vsirotin/synchromessotron/actions"
echo "  2. Review the release on: https://github.com/vsirotin/synchromessotron/releases"
echo "  3. (Optional) Push a -stable tag to mark as stable:"
echo "     bash set-tag.sh $TAG-stable"
