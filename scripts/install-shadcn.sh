#!/bin/bash
# Script to install all shadcn/ui components
cd $(dirname $0)/..

# Navigate to web app directory
cd apps/web

# Initialize shadcn/ui if not already initialized
if [ ! -f "components.json" ]; then
  npx shadcn-ui@0.6.0 init
fi

# Install all components
npx shadcn-ui@0.6.0 add button
npx shadcn-ui@0.6.0 add card
npx shadcn-ui@0.6.0 add dialog
npx shadcn-ui@0.6.0 add dropdown-menu
npx shadcn-ui@0.6.0 add avatar
npx shadcn-ui@0.6.0 add toast
npx shadcn-ui@0.6.0 add tabs
npx shadcn-ui@0.6.0 add form
npx shadcn-ui@0.6.0 add select
npx shadcn-ui@0.6.0 add input
npx shadcn-ui@0.6.0 add textarea
npx shadcn-ui@0.6.0 add checkbox
npx shadcn-ui@0.6.0 add radio-group
npx shadcn-ui@0.6.0 add slider
npx shadcn-ui@0.6.0 add switch
npx shadcn-ui@0.6.0 add accordion
npx shadcn-ui@0.6.0 add alert
npx shadcn-ui@0.6.0 add badge
npx shadcn-ui@0.6.0 add calendar
npx shadcn-ui@0.6.0 add command
npx shadcn-ui@0.6.0 add popover
npx shadcn-ui@0.6.0 add progress
npx shadcn-ui@0.6.0 add sheet
npx shadcn-ui@0.6.0 add table

echo "✅ All shadcn/ui components have been installed!"
