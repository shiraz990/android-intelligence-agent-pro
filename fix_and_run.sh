#!/bin/bash

echo "🔧 Fixing Android Intelligence Agent..."

# Deactivate if active
deactivate 2>/dev/null

# Remove broken venv
echo "🗑️ Removing broken virtual environment..."
rm -rf venv

# Create fresh venv
echo "📦 Creating fresh virtual environment..."
python3 -m venv venv --clear

# Activate
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install core dependencies
echo "📦 Installing Streamlit..."
pip install streamlit --no-cache-dir

echo "📦 Installing Plotly..."
pip install plotly --no-cache-dir

echo "📦 Installing Requests..."
pip install requests --no-cache-dir

# Verify installations
echo "✅ Verifying installations..."
pip list | grep -E "streamlit|plotly|requests"

# Test Streamlit
echo "🧪 Testing Streamlit..."
python -c "import streamlit; print('Streamlit version:', streamlit.__version__)"

echo ""
echo "✅ Setup complete! Run: streamlit run app.py"
