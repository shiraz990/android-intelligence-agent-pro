import subprocess
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Specialized models for different review aspects
MODELS = {
    "architecture": "llama3.2:3b",       # Best reasoning for design patterns
    "security": "qwen2.5-coder:3b",      # Code-specialist for vulnerabilities
    "performance": "gemma2:2b",          # Lightweight, fast for best-practices
}

def clean_output(text):
    """Remove ANSI color codes from Ollama output"""
    ansi = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi.sub('', text).strip()

def check_model_available(model):
    """Check if a model is available in Ollama"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return model in result.stdout
    except:
        return False

def pull_model(model):
    """Pull a model if not available"""
    try:
        st.info(f"📥 Downloading {model}... This may take a few minutes.")
        subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout for download
        )
        return True
    except Exception as e:
        return False

def run_model(model, prompt):
    """Run a single model with the given prompt"""
    try:
        # Check if model exists
        if not check_model_available(model):
            if not pull_model(model):
                return f"❌ Model {model} not available and couldn't be downloaded"

        response = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,  # 3 minutes for generation
            env={**os.environ, "NO_COLOR": "1"}
        )
        if response.returncode != 0:
            return f"❌ Model error: {response.stderr[:200]}"
        return clean_output(response.stdout)
    except subprocess.TimeoutExpired:
        return f"⏰ Model {model} timed out after 180s."
    except Exception as e:
        return f"❌ Error: {str(e)}"

def build_prompts(summary):
    """Build specialized prompts for each model"""
    base = f"""
You are reviewing an Android project. Only use the data provided below. 
Do NOT invent details. If data is missing, state its impact.

Project Data:
{summary}
"""
    return {
        "architecture": base + """
You are a Senior Android Architect. Focus ONLY on:
# Architecture Review (Score /10)
## Detected Pattern
## Strengths
## Critical Weaknesses
## Top 5 Architecture Improvements (numbered, specific)
Keep it under 300 words. Be direct and technical.
""",
        "security": base + """
You are an Android Security Engineer. Focus ONLY on:
# Security Review (Score /10)
## Critical Risks (label each HIGH / MEDIUM / LOW)
## Vulnerable Dependencies (if any listed)
## Top 5 Security Fixes (numbered, most critical first)
Keep it under 300 words. Be precise about CVEs and attack vectors.
""",
        "performance": base + """
You are an Android Performance Engineer. Focus ONLY on:
# Performance & Best Practices Review (Score /10)
## Compose Recomposition Risks
## Memory & Threading Concerns  
## Top 5 Performance Improvements (numbered)
Keep it under 300 words. Be specific about Android performance patterns.
"""
    }

def review_project(summary):
    """Run 3 AI models in parallel with ThreadPoolExecutor"""
    prompts = build_prompts(summary)
    results = {}

    # Check if Ollama is running
    try:
        subprocess.run(["ollama", "list"], capture_output=True, check=True, timeout=5)
    except:
        return {"error": "❌ Ollama is not running. Please start Ollama first."}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_model, MODELS[role], prompt): role
            for role, prompt in prompts.items()
        }
        for future in as_completed(futures):
            role = futures[future]
            try:
                results[role] = future.result()
            except Exception as e:
                results[role] = f"❌ Failed: {str(e)}"

    return results