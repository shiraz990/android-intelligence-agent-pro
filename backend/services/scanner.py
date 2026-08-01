import os
import subprocess


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


def get_git_stats(project_path):
    """Returns per-file commit count and last modified date"""
    stats = {}
    try:
        log = subprocess.run(
            ["git", "-C", project_path, "log", "--name-only", "--format=%ad", "--date=short"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()

        current_date = None
        for line in log.splitlines():
            line = line.strip()
            if not line:
                continue
            if len(line) == 10 and line[4] == "-":
                current_date = line
            elif line.endswith((".kt", ".java", ".xml")):
                if line not in stats:
                    stats[line] = {"commits": 0, "last_modified": current_date}
                stats[line]["commits"] += 1

        total_commits = subprocess.run(
            ["git", "-C", project_path, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()

        authors = subprocess.run(
            ["git", "-C", project_path, "shortlog", "-sn", "--no-merges"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()

        return {
            "file_stats": stats,
            "total_commits": int(total_commits) if total_commits.isdigit() else 0,
            "authors": [line.strip() for line in authors.splitlines()[:5]]
        }
    except Exception:
        return {"file_stats": {}, "total_commits": 0, "authors": []}


def scan_project(project_path):
    project = {
        "path": project_path,
        "kotlin_files": [],
        "java_files": [],
        "xml_files": [],
        "gradle_files": [],
        "manifest": "",
        "toml": "",
        "files": [],
        "file_tree": [],
        "git": get_git_stats(project_path)
    }

    skip_dirs = {"build", ".gradle", ".idea", ".git", "__pycache__", "node_modules"}

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_path)

            # Store the absolute path
            full_path_abs = os.path.abspath(full_path)

            if file.endswith(".kt"):
                content = read_file(full_path_abs)
                project["kotlin_files"].append(full_path_abs)
                project["files"].append({
                    "name": file,
                    "path": full_path_abs,  # Full absolute path
                    "rel_path": rel_path,
                    "type": "kotlin",
                    "content": content,
                    "lines": len(content.splitlines()),
                    "size_kb": round(len(content.encode()) / 1024, 1)
                })
                project["file_tree"].append(rel_path)

            elif file.endswith(".java"):
                content = read_file(full_path_abs)
                project["java_files"].append(full_path_abs)
                project["files"].append({
                    "name": file,
                    "path": full_path_abs,  # Full absolute path
                    "rel_path": rel_path,
                    "type": "java",
                    "content": content,
                    "lines": len(content.splitlines()),
                    "size_kb": round(len(content.encode()) / 1024, 1)
                })
                project["file_tree"].append(rel_path)

            elif file.endswith(".xml"):
                content = read_file(full_path_abs)
                project["xml_files"].append(full_path_abs)
                project["files"].append({
                    "name": file,
                    "path": full_path_abs,  # Full absolute path
                    "rel_path": rel_path,
                    "type": "xml",
                    "content": content,
                    "lines": len(content.splitlines()),
                    "size_kb": round(len(content.encode()) / 1024, 1)
                })
                if file == "AndroidManifest.xml":
                    project["manifest"] = content

            elif file in ("build.gradle", "build.gradle.kts"):
                project["gradle_files"].append(read_file(full_path_abs))

            elif file == "libs.versions.toml":
                project["toml"] = read_file(full_path_abs)

    return project