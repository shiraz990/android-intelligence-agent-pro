import os

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

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
        "file_tree": []
    }

    skip_dirs = {"build", ".gradle", ".idea", ".git", "__pycache__", "node_modules"}

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_path)

            if file.endswith(".kt"):
                content = read_file(full_path)
                project["kotlin_files"].append(full_path)
                project["files"].append({
                    "name": file,
                    "path": full_path,
                    "rel_path": rel_path,
                    "type": "kotlin",
                    "content": content,
                    "lines": len(content.splitlines())
                })
                project["file_tree"].append(rel_path)

            elif file.endswith(".java"):
                content = read_file(full_path)
                project["java_files"].append(full_path)
                project["files"].append({
                    "name": file,
                    "path": full_path,
                    "rel_path": rel_path,
                    "type": "java",
                    "content": content,
                    "lines": len(content.splitlines())
                })
                project["file_tree"].append(rel_path)

            elif file.endswith(".xml"):
                content = read_file(full_path)
                project["xml_files"].append(full_path)
                project["files"].append({
                    "name": file,
                    "path": full_path,
                    "rel_path": rel_path,
                    "type": "xml",
                    "content": content,
                    "lines": len(content.splitlines())
                })
                if file == "AndroidManifest.xml":
                    project["manifest"] = content

            elif file in ("build.gradle", "build.gradle.kts"):
                project["gradle_files"].append(read_file(full_path))

            elif file == "libs.versions.toml":
                project["toml"] = read_file(full_path)

    return project