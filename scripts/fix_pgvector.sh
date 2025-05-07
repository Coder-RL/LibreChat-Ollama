#!/bin/bash
# Fix script for pgvector on macOS with PostgreSQL 16

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Fixing pgvector for macOS (M4 Mac) ===${NC}"

# Check PostgreSQL installation
echo -e "\n${YELLOW}Checking PostgreSQL installation...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed or not in PATH!${NC}"
    exit 1
fi

echo -e "${GREEN}PostgreSQL is installed.${NC}"
PG_VERSION=$(psql --version | awk '{print $3}')
echo -e "PostgreSQL version: ${YELLOW}$PG_VERSION${NC}"

# Uninstall existing pgvector
echo -e "\n${YELLOW}Removing any existing pgvector installation...${NC}"
brew uninstall --ignore-dependencies pgvector 2>/dev/null || true
brew cleanup

# Install pgvector
echo -e "\n${YELLOW}Installing pgvector...${NC}"
brew install pgvector

# Find pgvector extension files
echo -e "\n${YELLOW}Locating pgvector extension files...${NC}"
PGVECTOR_EXTENSION_DIR=$(find /opt/homebrew/Cellar/pgvector -name "extension" -type d 2>/dev/null)

if [ -z "$PGVECTOR_EXTENSION_DIR" ]; then
    echo -e "${RED}Could not find pgvector extension directory!${NC}"
    # Try alternative location for Intel Macs
    PGVECTOR_EXTENSION_DIR=$(find /usr/local/Cellar/pgvector -name "extension" -type d 2>/dev/null)
    
    if [ -z "$PGVECTOR_EXTENSION_DIR" ]; then
        echo -e "${RED}Could not find pgvector extension directory in alternate location either!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Found pgvector extension at: ${YELLOW}$PGVECTOR_EXTENSION_DIR${NC}"

# Find PostgreSQL extension directory
echo -e "\n${YELLOW}Locating PostgreSQL extension directory...${NC}"

# Try to get the extension directory from PostgreSQL
PG_EXTENSION_DIR=$(psql -d ollama_ai_db -t -c "SHOW extension_dir;")
PG_EXTENSION_DIR=$(echo "$PG_EXTENSION_DIR" | tr -d '[:space:]')

# If that fails, try to locate it manually
if [ -z "$PG_EXTENSION_DIR" ]; then
    echo -e "${YELLOW}Could not get extension directory from PostgreSQL. Trying to locate manually...${NC}"
    
    # Check for Apple Silicon path
    if [ -d "/opt/homebrew/opt/postgresql/share/postgresql/extension" ]; then
        PG_EXTENSION_DIR="/opt/homebrew/opt/postgresql/share/postgresql/extension"
    # Check for versioned path (PostgreSQL@16)
    elif [ -d "/opt/homebrew/opt/postgresql@16/share/postgresql@16/extension" ]; then
        PG_EXTENSION_DIR="/opt/homebrew/opt/postgresql@16/share/postgresql@16/extension"
    # Check Intel Mac paths
    elif [ -d "/usr/local/opt/postgresql/share/postgresql/extension" ]; then
        PG_EXTENSION_DIR="/usr/local/opt/postgresql/share/postgresql/extension"
    elif [ -d "/usr/local/opt/postgresql@16/share/postgresql@16/extension" ]; then
        PG_EXTENSION_DIR="/usr/local/opt/postgresql@16/share/postgresql@16/extension"
    else
        echo -e "${RED}Could not locate PostgreSQL extension directory!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}PostgreSQL extension directory: ${YELLOW}$PG_EXTENSION_DIR${NC}"

# Check if user has write permissions to PostgreSQL directories
if [ ! -w "$PG_EXTENSION_DIR" ]; then
    echo -e "${RED}You don't have write permissions to $PG_EXTENSION_DIR${NC}"
    echo -e "${YELLOW}Try running the script with sudo${NC}"
    exit 1
fi

# Create extension directory if it doesn't exist
if [ ! -d "$PG_EXTENSION_DIR" ]; then
    echo -e "${YELLOW}Creating PostgreSQL extension directory...${NC}"
    mkdir -p "$PG_EXTENSION_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create extension directory!${NC}"
        exit 1
    fi
fi

# Copy pgvector extension files to PostgreSQL
echo -e "\n${YELLOW}Copying pgvector extension files to PostgreSQL...${NC}"
cp -v "$PGVECTOR_EXTENSION_DIR"/* "$PG_EXTENSION_DIR"

# Restart PostgreSQL
echo -e "\n${YELLOW}Restarting PostgreSQL...${NC}"
brew services restart postgresql || brew services restart postgresql@16

# Wait for PostgreSQL to restart
echo -e "${YELLOW}Waiting for PostgreSQL to restart...${NC}"
sleep 5

# Create pgvector extension in database
echo -e "\n${YELLOW}Creating pgvector extension in database...${NC}"
psql -d ollama_ai_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify installation
echo -e "\n${YELLOW}Verifying pgvector installation...${NC}"
if psql -d ollama_ai_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';" | grep -q "vector"; then
    echo -e "${GREEN}✅ pgvector is successfully installed and enabled!${NC}"
    
    # Test vector operations
    echo -e "\n${YELLOW}Testing vector operations...${NC}"
    psql -d ollama_ai_db -c "
    DROP TABLE IF EXISTS vector_test;
    CREATE TABLE vector_test (id serial primary key, embedding vector(3));
    INSERT INTO vector_test (embedding) VALUES ('[1,2,3]');
    INSERT INTO vector_test (embedding) VALUES ('[4,5,6]');
    SELECT id, embedding <-> '[3,1,2]' AS distance FROM vector_test ORDER BY distance LIMIT 1;
    DROP TABLE vector_test;
    "
    
    echo -e "\n${GREEN}✅ pgvector is now properly installed and working!${NC}"
else
    echo -e "${RED}❌ pgvector installation verification failed!${NC}"
    exit 1
fi
