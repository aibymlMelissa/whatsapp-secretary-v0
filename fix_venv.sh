#!/bin/bash

# Script to fix Python virtual environment with hardcoded paths

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Fixing Python Virtual Environment${NC}"
echo -e "${YELLOW}This will recreate the venv with correct paths${NC}"

cd backend

# Backup requirements if needed
if [ -f "venv/bin/pip" ]; then
    echo -e "\n${YELLOW}Backing up currently installed packages...${NC}"
    venv/bin/python3 -m pip freeze > requirements_backup.txt 2>/dev/null || true
fi

# Remove old venv
if [ -d "venv" ]; then
    echo -e "\n${YELLOW}Removing old virtual environment...${NC}"
    rm -rf venv
fi

# Create new venv
echo -e "\n${GREEN}Creating new virtual environment...${NC}"
python3 -m venv venv

# Upgrade pip
echo -e "\n${GREEN}Upgrading pip...${NC}"
venv/bin/python3 -m pip install --upgrade pip

# Install requirements
echo -e "\n${GREEN}Installing dependencies from requirements.txt...${NC}"
venv/bin/pip install -r requirements.txt

echo -e "\n${GREEN}✓ Virtual environment fixed successfully!${NC}"
echo -e "${YELLOW}You can now use: venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8001${NC}"

# Cleanup backup
rm -f requirements_backup.txt
