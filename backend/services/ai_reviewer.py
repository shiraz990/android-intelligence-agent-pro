import subprocess
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ============================================================
# OPTIMIZED MODELS FOR EXACT LINE ERRORS & FIXES
# ============================================================
# Qwen2.5-Coder: Best for exact code fixes and line-by-line analysis
# DeepSeek-Coder: Best for complex bug detection
# Gemma2: Fast and good for final review
# ============================================================

MODELS = {
    # PRIMARY: Best for exact line errors and fixes
    "fixer": {
        "name": "qwen2.5-coder:3b",
        "description": "Best for exact line errors and generating fixes",
        "timeout": 300  # 5 minutes
    },
    # SECONDARY: Catches different bugs the primary misses
    "analyzer": {
        "name": "deepseek-coder:1.3b",
        "description": "Best for complex bug detection and edge cases",
        "timeout": 180  # 3 minutes
    },
    # REVIEWER: Final sanity check
    "reviewer": {
        "name": "gemma2:2b",
        "description": "Fast final review and best practices",
        "timeout": 120  # 2 minutes
    }
}

# For backward compatibility
MODEL_NAMES = {
    "architecture": MODELS["analyzer"]["name"],
    "security": MODELS["fixer"]["name"],
    "performance": MODELS["reviewer"]["name"],
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
        print(f"📥 Downloading {model}... This may take a few minutes.")
        subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            timeout=600
        )
        return True
    except Exception as e:
        print(f"❌ Failed to pull {model}: {e}")
        return False


def run_model_with_context(model, code_content, issue_description, file_path="", timeout=180):
    """
    Run a model with specific context for exact line error fixing

    Args:
        model: The model name to use
        code_content: The code to analyze
        issue_description: Description of the issue
        file_path: The file path (for context)
        timeout: Timeout in seconds

    Returns:
        The model's response with exact line fixes
    """
    # Truncate code if too long (save first 2000 chars + last 500 chars)
    if len(code_content) > 2500:
        code_content = code_content[:2000] + "\n... (truncated) ...\n" + code_content[-500:]

    prompt = f"""
You are an expert Android developer. Analyze the following code and provide EXACT line-by-line fixes.

FILE: {file_path}

ISSUE TO FIX:
{issue_description}

CODE:
INSTRUCTIONS:
1. Identify the EXACT lines that need fixing
2. Show the ORIGINAL lines
3. Show the CORRECTED lines
4. Explain WHY this is the correct fix
5. Keep the fix focused and minimal

Format your response as:
=== ISSUE ===
[Brief description of the issue]

=== LINE X ===
ORIGINAL: [line content]
FIXED: [line content]
WHY: [explanation]

=== LINE Y ===
ORIGINAL: [line content]
FIXED: [line content]
WHY: [explanation]

Provide the complete corrected code at the end if multiple lines need changing.
"""

    try:
        # Check if model exists
        if not check_model_available(model):
            if not pull_model(model):
                return f"❌ Model {model} not available"

        # Run with increased timeout and better error handling
        response = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            env={**os.environ, "NO_COLOR": "1"}
        )
        if response.returncode != 0:
            return f"❌ Model error: {response.stderr[:200]}"
        return clean_output(response.stdout)
    except subprocess.TimeoutExpired:
        return f"⏰ Model {model} timed out after {timeout}s. Try:\n1. Use smaller code snippets\n2. Disable AI Review for large projects\n3. Use faster models (gemma2:2b)"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def run_model(model, prompt, timeout=180):
    """Run a model with the given prompt"""
    try:
        if not check_model_available(model):
            if not pull_model(model):
                return f"❌ Model {model} not available"

        response = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            env={**os.environ, "NO_COLOR": "1"}
        )
        if response.returncode != 0:
            return f"❌ Model error: {response.stderr[:200]}"
        return clean_output(response.stdout)
    except subprocess.TimeoutExpired:
        return f"⏰ Model {model} timed out. Try using a smaller model or disabling AI review."
    except Exception as e:
        return f"❌ Error: {str(e)}"

def build_prompts(summary):
    """Build specialized prompts for each model with reduced length"""
    # Truncate summary if too long
    if len(summary) > 2000:
        summary = summary[:2000] + "\n... (truncated) ..."

    base = f"""
You are reviewing an Android project. Only use the data provided below. 
Do NOT invent details. If data is missing, state its impact.

Project Data:
{summary}
"""
    return {
        "analyzer": base + """
You are a Senior Android Architect focused on EXACT CODE FIXES.
Analyze the code for:
1. Architecture issues
2. Code smells
3. Anti-patterns

Provide the exact lines that need changing and the corrected code.

Format:
=== ARCHITECTURE ISSUE ===
Location: [file name:line number]
Issue: [description]
Fix: [exact code change]
""",
        "fixer": base + """
You are a Senior Android Security Engineer focused on EXACT SECURITY FIXES.
Analyze the code for:
1. Security vulnerabilities
2. Hardcoded secrets
3. Unsafe practices

Provide the exact lines that need changing and the corrected code.

Format:
=== SECURITY ISSUE ===
Location: [file name:line number]
Issue: [description]
Fix: [exact code change]
""",
        "reviewer": base + """
You are a Senior Android Performance Engineer focused on EXACT PERFORMANCE FIXES.
Analyze the code for:
1. Performance bottlenecks
2. Memory leaks
3. Best practices violations

Provide the exact lines that need changing and the corrected code.

Format:
=== PERFORMANCE ISSUE ===
Location: [file name:line number]
Issue: [description]
Fix: [exact code change]
"""
    }

def review_project(summary, code_content="", issue_description=""):
    """
    Run AI models for exact line error detection and fixing

    Args:
        summary: Project summary
        code_content: The code to analyze (optional)
        issue_description: Description of the issue (optional)

    Returns:
        Dictionary with reviews from each model
    """
    # Check if summary is too long and truncate
    if len(summary) > 3000:
        summary = summary[:3000] + "\n... (summary truncated for performance) ..."

    prompts = build_prompts(summary)
    results = {}

    try:
        subprocess.run(["ollama", "list"], capture_output=True, check=True, timeout=5)
    except:
        return {"error": "❌ Ollama is not running. Start with: ollama serve"}

    # If we have specific code and issue, use the specialized prompt
    if code_content and issue_description:
        # Use only the fixer model for speed
        model = MODELS["fixer"]["name"]
        timeout = MODELS["fixer"]["timeout"]
        try:
            results["fixer"] = run_model_with_context(
                model,
                code_content[:2000],  # Truncate code
                issue_description,
                timeout=timeout
            )
        except Exception as e:
            results["fixer"] = f"❌ Failed: {str(e)}"

        # Also run the analyzer if time permits
        try:
            model2 = MODELS["analyzer"]["name"]
            results["analyzer"] = run_model_with_context(
                model2,
                code_content[:1500],  # Smaller chunk
                issue_description,
                timeout=120
            )
        except:
            results["analyzer"] = "⏰ Skipped (time constraint)"
    else:
        # Use the standard parallel review with shorter prompts
        with ThreadPoolExecutor(max_workers=2) as executor:  # Reduced from 3 to 2
            futures = {}
            for role, model_info in MODELS.items():
                model = model_info["name"]
                timeout = model_info["timeout"]
                prompt_key = "analyzer" if role == "analyzer" else "fixer" if role == "fixer" else "reviewer"
                futures[executor.submit(run_model, model, prompts.get(prompt_key, ""), timeout)] = role

            for future in as_completed(futures):
                role = futures[future]
                try:
                    results[role] = future.result()
                except Exception as e:
                    results[role] = f"❌ Failed: {str(e)}"

    return results

def get_model_info():
    """Return information about the currently configured models"""
    return MODELS

def get_best_model_for_fixes():
    """Return the best model for exact line fixes"""
    return MODELS["fixer"]["name"]

def get_model_for_analysis():
    """Return the best model for code analysis"""
    return MODELS["analyzer"]["name"]