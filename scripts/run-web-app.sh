#!/bin/bash

# Script to run the JustMaily web application
# This script installs dependencies and starts the Next.js development server

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "     _           _   __  __       _ _       "
echo "    | |_   _ ___| |_|  \/  | __ _(_) |_   _ "
echo " _  | | | | / __| __| |\/| |/ _\` | | | | | |"
echo "| |_| | |_| \__ \ |_| |  | | (_| | | | |_| |"
echo " \___/ \__,_|___/\__|_|  |_|\__,_|_|_|\__, |"
echo "                                       |___/ "
echo -e "${NC}"
echo -e "${GREEN}Enterprise-Grade Hybrid Interface${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "apps/web" ]; then
  echo -e "${RED}Error: This script must be run from the project root directory.${NC}"
  echo "Current directory: $(pwd)"
  echo "Please run this script from the directory containing the 'apps/web' folder."
  exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
  echo -e "${RED}Error: Node.js is not installed.${NC}"
  echo "Please install Node.js from https://nodejs.org/"
  exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d 'v' -f 2)
NODE_MAJOR_VERSION=$(echo $NODE_VERSION | cut -d '.' -f 1)
if [ "$NODE_MAJOR_VERSION" -lt 18 ]; then
  echo -e "${YELLOW}Warning: Node.js version $NODE_VERSION detected.${NC}"
  echo "JustMaily recommends Node.js 18 or higher."
  echo "Continue anyway? (y/n)"
  read -r response
  if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Exiting..."
    exit 1
  fi
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
  echo -e "${RED}Error: npm is not installed.${NC}"
  echo "Please install npm (it usually comes with Node.js)"
  exit 1
fi

# Navigate to the web app directory
cd apps/web

# Check if .env file exists, create if not
if [ ! -f ".env.local" ]; then
  echo -e "${YELLOW}Creating .env.local file with default settings...${NC}"
  cat > .env.local << EOL
# JustMaily Web App Environment Variables
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000

# Auth0 Configuration
NEXT_PUBLIC_AUTH0_DOMAIN=maily.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=your_auth0_client_id
NEXT_PUBLIC_AUTH0_AUDIENCE=https://api.maily.com
AUTH0_CLIENT_SECRET=your_auth0_client_secret

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret

# Feature Flags
NEXT_PUBLIC_FEATURE_AI_MESH=true
NEXT_PUBLIC_FEATURE_TRUST_VERIFICATION=true
NEXT_PUBLIC_FEATURE_REAL_TIME_COLLABORATION=true
EOL
  echo -e "${YELLOW}Please update .env.local with your actual configuration values.${NC}"
fi

# Install dependencies if node_modules doesn't exist or is empty
if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules)" ]; then
  echo -e "${BLUE}Installing dependencies...${NC}"
  npm install
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    exit 1
  fi
  echo -e "${GREEN}Dependencies installed successfully.${NC}"
else
  echo -e "${GREEN}Dependencies already installed.${NC}"
fi

# Start the development server
echo -e "${BLUE}Starting the development server...${NC}"
echo -e "${YELLOW}The web app will be available at: http://localhost:3000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

npm run dev
