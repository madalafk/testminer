#!/bin/bash

echo "🎓 Virtual ASIC Miner - Educational Setup"
echo "=========================================="

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.6+"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Installing..."
    sudo apt-get update && sudo apt-get install python3-pip -y
fi

# Install requirements
echo "📦 Installing required packages..."
pip3 install -r requirements.txt

# Clear screen
clear

# Run the miner
echo "🚀 Starting Virtual ASIC Miner..."
python3 virtual_asic_miner.py
