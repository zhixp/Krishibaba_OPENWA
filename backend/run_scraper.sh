#!/bin/bash
# Krishi Baba - Daily Price Scraper Runner (Linux/Mac)
# Add to cron: 0 4 * * * /path/to/run_scraper.sh

echo "============================================"
echo "Krishi Baba - Daily Price Update"
date
echo "============================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if you have one
# source venv/bin/activate

echo "Running scraper..."
python3 scripts/watchdog.py

echo ""
echo "============================================"
echo "Completed at $(date)"
echo "============================================"
