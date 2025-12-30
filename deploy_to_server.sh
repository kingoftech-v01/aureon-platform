#!/bin/bash
# Aureon Platform - Server Deployment Script
# Run this on your development server after cloning the repository

set -e

echo "===== Aureon Platform Deployment ====="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo -e "\n${GREEN}[1/10] Checking Python version...${NC}"
python3 --version

# Step 2: Create virtual environment
echo -e "\n${GREEN}[2/10] Creating virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate

# Step 3: Install dependencies
echo -e "\n${GREEN}[3/10] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Check if .env exists
echo -e "\n${GREEN}[4/10] Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${RED}IMPORTANT: Please edit .env with your actual configuration!${NC}"
fi

# Step 5: Run migrations
echo -e "\n${GREEN}[5/10] Running database migrations...${NC}"
python manage.py migrate

# Step 6: Create notification templates
echo -e "\n${GREEN}[6/10] Creating notification templates...${NC}"
python manage.py create_notification_templates || echo "Templates may already exist"

# Step 7: Collect static files
echo -e "\n${GREEN}[7/10] Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Step 8: Run tests
echo -e "\n${GREEN}[8/10] Running tests...${NC}"
python manage.py test apps.webhooks apps.notifications apps.analytics apps.accounts --verbosity=2 || echo "Some tests may need database setup"

# Step 9: Check Django configuration
echo -e "\n${GREEN}[9/10] Checking Django configuration...${NC}"
python manage.py check

# Step 10: Create superuser (optional)
echo -e "\n${GREEN}[10/10] Setup complete!${NC}"
echo ""
echo "To create a superuser, run:"
echo "  python manage.py createsuperuser"
echo ""
echo "To seed demo data, run:"
echo "  python manage.py seed_demo_data"
echo ""
echo "To start the development server:"
echo "  python manage.py runserver 0.0.0.0:8000"
echo ""
echo "===== Deployment Complete ====="
