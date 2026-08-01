import re
import hashlib
from typing import List, Dict  # Add this import


def detect_technologies(gradle_text):
    tech_map = {
        "Jetpack Compose": "compose",
        "Material3": "material3",
        "Navigation": "navigation",
        "Retrofit": "retrofit",
        "Room": "room",
        "WorkManager": "workmanager",
        "Coroutines": "coroutines",
        "Hilt": "hilt",
    }
    detected = {}
    for name, keyword in tech_map.items():
        detected[name] = keyword in gradle_text.lower()
    return detected


def detect_duplicates(files, block_size=8):
    block_hashes = {}
    duplicates = []

    for file in files:
        if file["type"] not in ["kotlin", "java"]:
            continue

        lines = [l.strip() for l in file["content"].splitlines() if l.strip()]

        for i in range(len(lines) - block_size):
            block = "\n".join(lines[i:i + block_size])
            h = hashlib.md5(block.encode()).hexdigest()

            if h in block_hashes:
                existing = block_hashes[h]
                if existing["file"] != file["name"]:
                    duplicates.append({
                        "file_a": existing["file"],
                        "file_b": file["name"],
                        "line_a": existing["line"],
                        "line_b": i + 1,
                        "preview": lines[i][:80]
                    })
            else:
                block_hashes[h] = {"file": file["name"], "line": i + 1}

    seen = set()
    unique = []
    for d in duplicates:
        key = f"{d['file_a']}-{d['file_b']}-{d['line_a']}"
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique[:20]


def analyze_compose(files):
    issues = []
    for file in files:
        if file["type"] != "kotlin":
            continue

        code = file["content"]
        name = file["name"]

        if "@Composable" not in code:
            continue

        if re.search(r'LaunchedEffect\(\s*\)', code):
            issues.append({
                "file": name,
                "issue": "LaunchedEffect called without a key — will re-launch on every recomposition",
                "severity": "error"
            })

        if "mutableStateOf" in code and "remember" not in code:
            issues.append({
                "file": name,
                "issue": "mutableStateOf used without remember — state will reset on recomposition",
                "severity": "error"
            })

        if "data class" in code and "@Stable" not in code and "@Immutable" not in code:
            issues.append({
                "file": name,
                "issue": "Data class passed to Composable without @Stable/@Immutable annotation",
                "severity": "info"
            })

    return issues


def detect_fixable_issues(file_path: str, code: str) -> List[Dict]:
    """Detect fixable issues in a file"""
    issues = []

    # Use the full file path
    if 'http://' in code and 'https://' not in code:
        issues.append({
            'type': 'http_url',
            'file': file_path,
            'severity': 'high',
            'line_number': 0
        })

    if 'TODO' in code and 'FIXME' not in code:
        issues.append({
            'type': 'todo',
            'file': file_path,
            'severity': 'medium',
            'line_number': 0
        })

    if '!!' in code:
        issues.append({
            'type': 'null_assertion',
            'file': file_path,
            'severity': 'high',
            'line_number': 0
        })

    if 'println(' in code:
        issues.append({
            'type': 'println',
            'file': file_path,
            'severity': 'low',
            'line_number': 0
        })

    return issues