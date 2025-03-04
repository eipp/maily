#!/bin/bash
# Source environment variables from .env files

ENV_FILE=".env"

if [ -n "$1" ]; then
  ENV_FILE=".env.$1"
fi

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Environment file $ENV_FILE not found"
  exit 1
fi

# Load environment variables
echo "Loading environment variables from $ENV_FILE"

# Parse and export variables
while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip comments and empty lines
  if [[ $line =~ ^#.*$ ]] || [[ -z $line ]]; then
    continue
  fi

  # Remove any trailing comments
  line=$(echo "$line" | sed 's/#.*$//')
  
  # Trim whitespace
  line=$(echo "$line" | xargs)
  
  if [[ $line == *"="* ]]; then
    key=$(echo "$line" | cut -d '=' -f 1)
    value=$(echo "$line" | cut -d '=' -f 2-)
    
    # Remove quotes if present
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    
    # Export the variable
    export "$key"="$value"
  fi
done < "$ENV_FILE"

echo "Environment variables loaded from $ENV_FILE" 