import hashlib
import json
import os

CACHE_DIR = ".aia_cache"

def _get_cache_path(key):
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{key}.json")

def make_project_hash(project):
    """Create MD5 hash of project content for caching"""
    content = ""
    for f in sorted(project["files"], key=lambda x: x["path"]):
        content += f["path"] + f["content"]
    return hashlib.md5(content.encode()).hexdigest()

def load_cache(key):
    path = _get_cache_path(key)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(key, data):
    path = _get_cache_path(key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def clear_cache():
    if os.path.exists(CACHE_DIR):
        for file in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, file))