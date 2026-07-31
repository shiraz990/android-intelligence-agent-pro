import re

DEPRECATED_APIS = [
    "AsyncTask", "Handler()", "Looper.getMainLooper()",
    "startActivityForResult", "onActivityResult",
    "requestPermissions", "getExternalStorageDirectory",
    "LinearLayout", "RelativeLayout"
]

SECURITY_PATTERNS = [
    (r'AIza[0-9A-Za-z\-_]{35}', "🚨 Google API Key"),
    (r'AAAA[A-Za-z0-9_\-]{140}', "🚨 Firebase Server Key"),
    (r'(?i)password\s*=\s*"[^"]+"', "🚨 Hardcoded password"),
    (r'(?i)secret\s*=\s*"[^"]+"', "🚨 Hardcoded secret"),
    (r'MD5|SHA1(?!_)', "⚠ Weak hash algorithm"),
]

def analyze_rules(files):
    result = {
        "todos": 0, "fixmes": 0, "printlns": 0, "logd": 0,
        "http_urls": 0, "api_keys": 0, "large_files": 0,
        "deprecated_apis": [], "magic_numbers": 0,
        "null_assertions": 0, "security_issues": [],
        "complex_files": []
    }

    for file in files:
        if file["type"] not in ["kotlin", "java"]:
            continue

        code = file["content"]
        lines = code.splitlines()
        name = file["name"]

        result["todos"] += code.count("TODO")
        result["fixmes"] += code.count("FIXME")
        result["printlns"] += code.count("println(")
        result["logd"] += code.count("Log.d(")
        result["http_urls"] += len(re.findall(r"http://[^\s\"']+", code))
        result["null_assertions"] += code.count("!!")

        if len(lines) > 300:
            result["large_files"] += 1

        complexity = sum(code.count(kw) for kw in ["if ", "else if", "when ", "for ", "while ", "catch ", "&&", "||"])
        if complexity > 20:
            result["complex_files"].append({"file": name, "complexity": complexity})

        magic = re.findall(r'(?<![.\w])(?!0x)\b([2-9]\d{1,4})\b(?!\s*[,;.]?\s*//)', code)
        result["magic_numbers"] += len(magic)

        for api in DEPRECATED_APIS:
            if api in code:
                result["deprecated_apis"].append({"file": name, "api": api})

        for pattern, label in SECURITY_PATTERNS:
            matches = re.findall(pattern, code)
            if matches:
                result["security_issues"].append({
                    "file": name,
                    "issue": label,
                    "count": len(matches)
                })

    return result