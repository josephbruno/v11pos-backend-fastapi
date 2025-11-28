#!/bin/bash

# 📦 Download and Setup Sample Images for POS System
# This script downloads sample images and uploads them to the server

set -e

echo "📦 Downloading sample images for POS system..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create directories
mkdir -p uploads/products
mkdir -p uploads/categories

# Base API URL
API_URL="https://apipos.v11tech.com"

# Sample image URLs (using placeholder service)
PLACEHOLDER_API="https://picsum.photos"

echo -e "${GREEN}[1/4] Downloading category images...${NC}"

# Download category images
categories=(
    "beverages:200"
    "appetizers:201"
    "main-dishes:202"
    "desserts:203"
    "pizzas:204"
    "burgers:205"
    "pasta:206"
    "salads:207"
)

for item in "${categories[@]}"; do
    IFS=':' read -r name id <<< "$item"
    echo "  Downloading ${name}.jpg..."
    curl -L "${PLACEHOLDER_API}/400/300?random=${id}" -o "uploads/categories/${name}.jpg" 2>/dev/null
done

echo -e "${GREEN}[2/4] Downloading product images...${NC}"

# Download product images
products=(
    "coca-cola:300"
    "orange-juice:301"
    "mineral-water:302"
    "iced-tea:303"
    "latte:304"
    "cappuccino:305"
    "espresso:306"
    "americano:307"
    "spring-rolls:310"
    "buffalo-wings:311"
    "margherita-pizza:320"
    "pepperoni-pizza:321"
    "bbq-chicken-pizza:322"
    "vegetarian-pizza:323"
    "classic-burger:330"
    "cheese-burger:331"
    "chicken-burger:332"
    "veggie-burger:333"
    "spaghetti-carbonara:340"
    "penne-arrabiata:341"
    "fettuccine-alfredo:342"
    "grilled-chicken:350"
    "beef-steak:351"
    "fish-chips:352"
    "chocolate-cake:360"
    "cheesecake:361"
    "tiramisu:362"
    "ice-cream-sundae:363"
)

for item in "${products[@]}"; do
    IFS=':' read -r name id <<< "$item"
    echo "  Downloading ${name}.jpg..."
    curl -L "${PLACEHOLDER_API}/500/400?random=${id}" -o "uploads/products/${name}.jpg" 2>/dev/null
done

echo -e "${GREEN}[3/4] Setting permissions...${NC}"
chmod -R 755 uploads/

echo -e "${GREEN}[4/4] Verifying downloads...${NC}"
category_count=$(ls -1 uploads/categories/*.jpg 2>/dev/null | wc -l)
product_count=$(ls -1 uploads/products/*.jpg 2>/dev/null | wc -l)

echo -e "  Categories: ${GREEN}${category_count} images${NC}"
echo -e "  Products: ${GREEN}${product_count} images${NC}"

echo ""
echo -e "${GREEN}✓ Sample images downloaded successfully!${NC}"
echo ""
echo -e "${YELLOW}Image locations:${NC}"
echo -e "  Categories: ${PWD}/uploads/categories/"
echo -e "  Products: ${PWD}/uploads/products/"
echo ""
echo -e "${YELLOW}Access images via:${NC}"
echo -e "  ${API_URL}/uploads/categories/beverages.jpg"
echo -e "  ${API_URL}/uploads/products/coca-cola.jpg"
echo ""
