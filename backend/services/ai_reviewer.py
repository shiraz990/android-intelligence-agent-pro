import subprocess
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

# ============================================================
# LOCAL MODEL COUNCIL — project-grounded management reports
# ============================================================
# Narratives are built from THIS project's scan first.
# Local models may polish wording only; fluff falls back to grounded text.
# ============================================================

MODELS = {
    "fixer": {
        "name": "qwen2.5-coder:3b",
        "description": "Security risk assessment and remediation",
        "timeout": 300,
        "title": "Security Assessment",
    },
    "analyzer": {
        "name": "deepseek-coder:1.3b",
        "description": "Architecture and maintainability review",
        "timeout": 180,
        "title": "Architecture Assessment",
    },
    "reviewer": {
        "name": "gemma2:2b",
        "description": "Performance and release-readiness review",
        "timeout": 120,
        "title": "Performance & Release Readiness",
    },
}

MODEL_NAMES = {
    "architecture": MODELS["analyzer"]["name"],
    "security": MODELS["fixer"]["name"],
    "performance": MODELS["reviewer"]["name"],
}

_FLUFF_PATTERNS = [
    r"(?i)let me know if you (have|need).*$",
    r"(?i)feel free to (ask|share|provide).*$",
    r"(?i)i hope this helps.*$",
    r"(?i)happy to help.*$",
    r"(?i)if you (can )?provide (more|additional).*$",
    r"(?i)this is a generic example.*$",
    r"(?i)further analysis using specialized tools.*$",
    r"(?i)hindering a comprehensive analysis.*$",
    r"(?i)missing performance data.*$",
    r"(?i)the provided data lacks.*$",
    r"(?i)lacks crucial perfor",
    r"(?i)projectdata\.kt.*$",
    r"(?i)^note:.*$",
    r"(?i)^as an ai.*$",
    r"(?i)^certainly[!.,].*$",
    r"(?i)^sure[!.,].*$",
    r"(?i)android profiler",
    r"(?i)benchmark (results|libraries|library)",
    r"(?i)garbage collection",
    r"(?i)latency measurements?",
    r"(?i)runtime (metrics|profiling|benchmarks)",
    r"(?i)provide further assistance",
    r"(?i)comprehensive analysis",
]

_USELESS_MARKERS = [
    r"(?i)projectdata\.kt",
    r"(?i)missing performance",
    r"(?i)android profiler",
    r"(?i)let me know",
]


def clean_output(text: str) -> str:
    ansi = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi.sub("", text).strip()


def extract_evidence_tokens(
    summary: str, grounded: Optional[Dict[str, str]] = None
) -> List[str]:
    tokens: List[str] = []
    blob = summary or ""
    if grounded:
        blob += "\n" + "\n".join(grounded.values())

    tokens += re.findall(r"CVE-\d{4}-\d+", blob)
    tokens += re.findall(r"`([^`]+)`", blob)
    tokens += re.findall(r"[\w./\\-]+\.(?:kt|java|xml)", blob, flags=re.I)
    tokens += re.findall(r"\*\*(\d+)\*\*", blob)

    out, seen = [], set()
    for t in tokens:
        t = t.strip()
        if len(t) < 2 or t.lower() in seen:
            continue
        if t.lower() in {"high", "medium", "low", "file", "score"}:
            continue
        seen.add(t.lower())
        out.append(t)
    return out[:40]


def polish_review_output(
    text: str,
    role: str = "",
    grounded: Optional[str] = None,
    evidence_tokens: Optional[List[str]] = None,
) -> str:
    """Prefer project-grounded text whenever AI output is weak or ungrounded."""
    if grounded and (not text or text.startswith("❌") or text.startswith("⏰")):
        return grounded
    if not text:
        return grounded or ""

    lower = text.lower()
    if sum(1 for m in _USELESS_MARKERS if re.search(m, lower)) >= 2:
        return grounded or text

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if any(re.search(p, stripped) for p in _FLUFF_PATTERNS):
            continue
        if re.search(r"(?i)location:\s*\*?\*?project\s*data", stripped):
            continue
        if re.search(r"(?i)location:\s*\*?\*?n/?a", stripped):
            continue
        if re.fullmatch(r"[#=\-\s*]+", stripped):
            continue
        lines.append(line)

    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    cleaned = re.sub(
        r"(?im)^[#\s]*=+\s*(PERFORMANCE|SECURITY|ARCHITECTURE)\s+ISSUE\s*=+\s*$",
        "",
        cleaned,
    ).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    title_map = {
        "analyzer": "Architecture Assessment",
        "fixer": "Security Assessment",
        "reviewer": "Performance & Release Readiness",
    }
    if role in title_map and cleaned and not cleaned.lstrip().startswith("#"):
        cleaned = f"## {title_map[role]}\n\n{cleaned}"

    useful = re.sub(r"[#=*_\-\s]", "", cleaned)
    useful = re.sub(
        r"(?i)architectureassessment|securityassessment|performance.?releasereadiness",
        "",
        useful,
    )
    if len(useful) < 120:
        return grounded or cleaned

    if evidence_tokens:
        hits = sum(1 for t in evidence_tokens if t and t.lower() in cleaned.lower())
        if hits < 1:
            return grounded or cleaned

    return cleaned


def check_model_available(model: str) -> bool:
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
        return model in result.stdout
    except Exception:
        return False


def pull_model(model: str) -> bool:
    try:
        subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            timeout=600,
        )
        return True
    except Exception:
        return False


def run_model_with_context(model, code_content, issue_description, file_path="", timeout=180):
    if len(code_content) > 2500:
        code_content = code_content[:2000] + "\n... (truncated) ...\n" + code_content[-500:]

    prompt = f"""You are a senior Android engineer writing a concise remediation note.
Be professional. Do not invent files/lines not present in CODE. Do not ask for more data.

FILE: {file_path}
ISSUE: {issue_description}
CODE:
{code_content}

### Finding
[one sentence]
### Change
ORIGINAL: [exact line from CODE]
FIXED: [corrected line]
RATIONALE: [one sentence]
"""
    try:
        if not check_model_available(model) and not pull_model(model):
            return f"❌ Model {model} not available"
        response = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            env={**os.environ, "NO_COLOR": "1"},
        )
        if response.returncode != 0:
            return f"❌ Model error: {response.stderr[:200]}"
        return clean_output(response.stdout)
    except subprocess.TimeoutExpired:
        return f"⏰ Model {model} timed out after {timeout}s."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def run_model(model, prompt, timeout=180):
    try:
        if not check_model_available(model) and not pull_model(model):
            return f"❌ Model {model} not available"
        response = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            env={**os.environ, "NO_COLOR": "1"},
        )
        if response.returncode != 0:
            return f"❌ Model error: {response.stderr[:200]}"
        return clean_output(response.stdout)
    except subprocess.TimeoutExpired:
        return "⏰ Model timed out."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def build_prompts(
    summary: str, grounded: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    if len(summary) > 3500:
        summary = summary[:3500] + "\n... (truncated) ..."
    grounded = grounded or {}

    shared = """
RULES:
1. Polish the PROJECT-SPECIFIC DRAFT for engineering leadership.
2. Keep EVERY number, file name, CVE, and count from the draft and facts.
3. Improve wording only. Do NOT invent new findings.
4. No chatbot language. No requests for Profiler/benchmarks/GC data.
5. Output: Executive summary, Findings, Recommended actions.
"""

    def one(role_key: str, role_name: str, focus: str) -> str:
        draft = (grounded.get(role_key) or "").strip() or "(use facts only — keep concrete)"
        return f"""Produce the {role_name} section of an Android assessment.

STATIC ANALYSIS FACTS:
{summary}

PROJECT-SPECIFIC DRAFT (source of truth):
{draft}

ROLE: {role_name}
Focus: {focus}
{shared}
"""

    return {
        "analyzer": one(
            "analyzer",
            "Principal Android Architect",
            "MVVM/Repository, tests, duplication, deprecated APIs",
        ),
        "fixer": one(
            "fixer",
            "Principal Mobile Security Engineer",
            "CVEs, secrets, HTTP, null-assertion risk",
        ),
        "reviewer": one(
            "reviewer",
            "Principal Android Performance & Release Engineer",
            "println/Log.d, !!, Compose, complexity, tests (static only)",
        ),
    }


def review_project(
    summary,
    code_content="",
    issue_description="",
    grounded: Optional[Dict[str, str]] = None,
):
    """
    Project-first narratives. Models may polish; ungrounded AI text is discarded.
    """
    grounded = dict(grounded or {})
    if len(summary) > 4000:
        summary = summary[:4000] + "\n... (summary truncated) ..."

    evidence = extract_evidence_tokens(summary, grounded)

    try:
        subprocess.run(["ollama", "list"], capture_output=True, check=True, timeout=5)
        ollama_ok = True
    except Exception:
        ollama_ok = False

    if not ollama_ok:
        return grounded if grounded else {
            "error": "❌ Ollama is not running. Start with: ollama serve"
        }

    if code_content and issue_description:
        results = dict(grounded)
        try:
            results["fixer"] = run_model_with_context(
                MODELS["fixer"]["name"],
                code_content[:2000],
                issue_description,
                timeout=MODELS["fixer"]["timeout"],
            )
        except Exception as e:
            results["fixer"] = grounded.get("fixer") or f"❌ Failed: {e}"
        try:
            results["analyzer"] = run_model_with_context(
                MODELS["analyzer"]["name"],
                code_content[:1500],
                issue_description,
                timeout=120,
            )
        except Exception:
            pass
        return results

    # Default to grounded project text; replace only if polish stays grounded
    results = dict(grounded)
    prompts = build_prompts(summary, grounded=grounded)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(
                run_model, info["name"], prompts[role], info["timeout"]
            ): role
            for role, info in MODELS.items()
        }
        for future in as_completed(futures):
            role = futures[future]
            base = grounded.get(role, "")
            try:
                raw = future.result()
                results[role] = polish_review_output(
                    raw,
                    role=role,
                    grounded=base,
                    evidence_tokens=evidence,
                )
            except Exception:
                results[role] = base

    return results


def get_model_info():
    return MODELS


def get_best_model_for_fixes():
    return MODELS["fixer"]["name"]


def get_model_for_analysis():
    return MODELS["analyzer"]["name"]


def role_display_label(role: str) -> str:
    info = MODELS.get(role, {})
    title = info.get("title", role.title())
    name = info.get("name", "")
    return f"{title} · {name}" if name else title
