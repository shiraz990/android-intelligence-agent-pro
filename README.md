Complete Guide: Running CodePulse AI on Windows & macOS

📋 Step-by-Step Setup Guide
Prerequisites (Both Platforms)
Before starting, ensure you have:

Python 3.9 or higher – Download from python.org

Git (optional, for cloning) – Download from git-scm.com

Ollama – Download from ollama.com

8GB+ RAM (16GB recommended)

5GB+ free disk space

🪟 Windows Setup Guide
Step 1: Install Python
Download Python 3.11+ from python.org

IMPORTANT: ✅ Check "Add Python to PATH" during installation

Click "Install Now"

Verify: Open Command Prompt and run:

cmd
python --version
# Should show: Python 3.11.x
Step 2: Install Ollama
Download from ollama.com/download/windows

Run OllamaSetup.exe (No admin rights needed)

Verify:

cmd
ollama --version
# Should show: ollama version 0.x.x
Step 3: Clone or Download the Project
cmd
# Using Git:
git clone https://github.com/shiraz990/android-intelligence-agent.git
cd android-intelligence-agent

# OR download ZIP from GitHub and extract
Step 4: Set Up Virtual Environment
cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Your prompt should show (venv)
Step 5: Install Dependencies
cmd
# Upgrade pip
python -m pip install --upgrade pip

# Install required packages
python -m pip install streamlit plotly pandas requests weasyprint
Step 6: Pull AI Models
cmd
# This takes 5-10 minutes (downloads ~2GB)
ollama pull qwen2.5-coder:3b
ollama pull deepseek-coder:1.3b
ollama pull gemma2:2b

# Verify models
ollama list
Step 7: Start Ollama & Run the App
cmd
# Start Ollama (keep this window open)
start /B ollama serve

# In the same terminal, run the app
streamlit run app_professional.py
Windows Troubleshooting
Issue	Solution
python not found	Reinstall with "Add to PATH" checked
pip not found	Use python -m pip install ...
ollama not found	Use full path: C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe
Execution Policy error	Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
🍎 macOS Setup Guide
Step 1: Install Python
Option A: Using Homebrew (Recommended)

bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
Option B: From Official Site

Download from python.org/downloads/mac-osx

Run the installer

Verify:

bash
python3 --version
# Should show: Python 3.11.x
Step 2: Install Ollama
bash
# One-liner install
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version
Step 3: Clone the Project
bash
git clone https://github.com/shiraz990/android-intelligence-agent.git
cd android-intelligence-agent
Step 4: Set Up Virtual Environment
bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Your prompt should show (venv)
Step 5: Install Dependencies
bash
# Upgrade pip
python -m pip install --upgrade pip

# Install required packages
python -m pip install streamlit plotly pandas requests weasyprint
Step 6: Pull AI Models
bash
# This takes 5-10 minutes
ollama pull qwen2.5-coder:3b
ollama pull deepseek-coder:1.3b
ollama pull gemma2:2b

# Verify
ollama list
Step 7: Start Ollama & Run the App
bash
# Start Ollama in background
ollama serve &

# Run the app
streamlit run app_professional.py
macOS Troubleshooting
Issue	Solution
python3 not found	Install via Homebrew or official installer
Permission denied	Use sudo or install without --user
ollama command not found	Reinstall or add to PATH
🚀 Running the App (Both Platforms)
Quick Start
bash
# Make sure you're in the virtual environment
# Windows: venv\Scripts\activate
# macOS: source venv/bin/activate

# Run the app
streamlit run app_professional.py
The app will open at: http://localhost:8501
