import os
import re
import shutil
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class AutoFixEngine:

    def __init__(self, project_path=None):
        self.project_path = project_path or os.getcwd()
        self.backup_dir = os.path.join(self.project_path, ".fix_backups")
        self.fix_history_file = os.path.join(self.backup_dir, "fix_history.json")
        self.fix_history = []
        os.makedirs(self.backup_dir, exist_ok=True)
        self._load_history()

    # ──────────────────────────────────────────────
    # History
    # ──────────────────────────────────────────────

    def _load_history(self):
        try:
            if os.path.exists(self.fix_history_file):
                with open(self.fix_history_file, "r") as f:
                    self.fix_history = json.load(f)
        except Exception:
            self.fix_history = []

    def _save_history(self):
        try:
            with open(self.fix_history_file, "w") as f:
                json.dump(self.fix_history, f, indent=2)
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # File utilities
    # ──────────────────────────────────────────────

    def _resolve_file_path(self, file_path: str) -> Optional[str]:
        if not file_path:
            return None
        # Absolute path
        if os.path.isabs(file_path) and os.path.exists(file_path):
            return file_path
        # Relative to project
        joined = os.path.join(self.project_path, file_path)
        if os.path.exists(joined):
            return joined
        # Basename only
        basename = os.path.basename(file_path)
        for root, dirs, files in os.walk(self.project_path):
            # Skip backup dir during search
            dirs[:] = [d for d in dirs if d != ".fix_backups"]
            if basename in files:
                return os.path.join(root, basename)
        return None

    def _create_backup(self, file_path: str) -> Optional[str]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            rel = os.path.relpath(file_path, self.project_path)
            # Flatten the path so it sits directly in backup_dir
            flat_name = rel.replace(os.sep, "__").replace("/", "__")
            backup_path = os.path.join(self.backup_dir, f"{flat_name}.{timestamp}.bak")
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    # ──────────────────────────────────────────────
    # Core: line-number-aware replacement
    # ──────────────────────────────────────────────

    def _replace_line_at(self, content: str, line_number: int, new_line_text: str) -> str:
        """
        Replace the line at `line_number` (1-based) with `new_line_text`.
        Preserves the original line ending (\n or \r\n).
        This is far more reliable than content.replace() because it
        never touches other occurrences of the same text.
        """
        lines = content.splitlines(keepends=True)
        if not (1 <= line_number <= len(lines)):
            return content

        original_line = lines[line_number - 1]

        # Detect and preserve line ending
        if original_line.endswith("\r\n"):
            ending = "\r\n"
        elif original_line.endswith("\n"):
            ending = "\n"
        else:
            ending = ""

        # Preserve leading whitespace (indentation) from original
        indent = len(original_line) - len(original_line.lstrip())
        leading = original_line[:indent]

        lines[line_number - 1] = leading + new_line_text.strip() + ending
        return "".join(lines)

    # ──────────────────────────────────────────────
    # Public: apply a single fix
    # ──────────────────────────────────────────────

    def apply_fix_direct(
        self, file_path: str, original: str, suggested: str, line_number: int = None
    ) -> Tuple[bool, str]:
        """
        Apply a fix to a file on disk.

        If `line_number` is provided, replacement is done at that exact line
        (much more reliable). Falls back to text-based replace if not given.
        """
        resolved = self._resolve_file_path(file_path)
        if not resolved:
            return False, f"File not found: {file_path}"

        if not os.access(resolved, os.W_OK):
            return False, f"Permission denied: {resolved}"

        try:
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return False, f"Could not read file: {e}"

        # Verify the original text actually exists before touching the file
        if original.strip() not in content:
            return False, (
                f"Pattern not found in file — it may have already been fixed.\n"
                f"Looking for: {original.strip()[:80]}"
            )

        # Create backup BEFORE any write
        backup_path = self._create_backup(resolved)
        if not backup_path:
            return False, "Could not create backup — fix aborted for safety."

        # Apply the replacement
        if line_number:
            new_content = self._replace_line_at(content, line_number, suggested.strip())
        else:
            # Text-based fallback: replace only the FIRST occurrence to avoid
            # accidentally touching identical lines elsewhere in the file
            new_content = content.replace(original, suggested, 1)

        if new_content == content:
            return False, "Replacement produced no change — check the before/after text."

        try:
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            # Attempt to restore backup
            shutil.copy2(backup_path, resolved)
            return False, f"Write failed (backup restored): {e}"

        # Record history
        self.fix_history.append({
            "file": os.path.relpath(resolved, self.project_path),
            "backup": os.path.relpath(backup_path, self.project_path),
            "original": original,
            "suggested": suggested,
            "line_number": line_number,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_history()

        return True, f"Fix applied ✅  Backup: {os.path.basename(backup_path)}"

    # ──────────────────────────────────────────────
    # Fix generators — now return ALL matches, not just first
    # ──────────────────────────────────────────────

    def _fix_http_urls(self, code: str, file_path: str) -> List[Dict]:
        """BUG FIX: was returning after first match. Now returns all."""
        fixes = []
        for i, line in enumerate(code.splitlines()):
            if "http://" in line and "https://" not in line:
                match = re.search(r"(http://[^\s\"\'<>]+)", line)
                if match:
                    old_url = match.group(1)
                    new_url = old_url.replace("http://", "https://", 1)
                    suggested = line.replace(old_url, new_url, 1)
                    fixes.append({
                        "file": file_path,
                        "line_number": i + 1,
                        "issue_type": "http_url",
                        "original": line,
                        "suggested": suggested,
                        "description": f"HTTP → HTTPS at line {i + 1}",
                        "confidence": 98,
                        "can_apply": True,
                        "is_applied": False,
                        "requires_review": False,
                        "diff": f"- {line}\n+ {suggested}",
                    })
        return fixes

    def _fix_printlns(self, code: str, file_path: str) -> List[Dict]:
        """BUG FIX: was returning after first match. Now returns all."""
        fixes = []
        lines = code.splitlines()

        # Extract TAG constant if present in this file
        tag = "TAG"
        for line in lines:
            m = re.search(r'(?:val|var)\s+TAG\s*=\s*"([^"]+)"', line)
            if m:
                tag = m.group(1)
                break

        for i, line in enumerate(lines):
            if "println(" not in line:
                continue
            m = re.search(r"println\(([^)]*)\)", line)
            if m:
                inner = m.group(1)
                suggested = line.replace(
                    f"println({inner})", f'Log.d("{tag}", {inner})', 1
                )
                fixes.append({
                    "file": file_path,
                    "line_number": i + 1,
                    "issue_type": "println",
                    "original": line,
                    "suggested": suggested,
                    "description": f"println → Log.d at line {i + 1}",
                    "confidence": 95,
                    "can_apply": True,
                    "is_applied": False,
                    "requires_review": False,
                    "diff": f"- {line}\n+ {suggested}",
                })
        return fixes

    def _fix_todos(self, code: str, file_path: str) -> List[Dict]:
        """BUG FIX: was returning after first match. Now returns all."""
        fixes = []
        for i, line in enumerate(code.splitlines()):
            if "TODO" in line:
                # Wrap TODO content in a proper comment block so it's visible
                suggested = re.sub(
                    r"//\s*TODO[:\s]*(.*)",
                    lambda m: f"// TODO(action-required): {m.group(1).strip()}",
                    line,
                )
                if suggested == line:
                    # Fallback: just mark it
                    suggested = line.replace("TODO", "TODO(action-required)", 1)
                fixes.append({
                    "file": file_path,
                    "line_number": i + 1,
                    "issue_type": "todo",
                    "original": line,
                    "suggested": suggested,
                    "description": f"Mark TODO as action-required at line {i + 1}",
                    "confidence": 80,
                    "can_apply": True,
                    "is_applied": False,
                    "requires_review": True,
                    "diff": f"- {line}\n+ {suggested}",
                })
        return fixes

    def _fix_null_assertions(self, code: str, file_path: str) -> List[Dict]:
        """
        BUG FIX: was completely missing — null_assertion issues were generated
        by app.py but silently dropped because generate_fixes had no handler.
        Now wraps !! with a safe let call.
        """
        fixes = []
        for i, line in enumerate(code.splitlines()):
            if "!!" not in line:
                continue

            # Match: someVar!! or someCall()!!
            m = re.search(r"(\w[\w.()]*)\s*!!", line)
            if m:
                expr = m.group(1)
                # Suggest replacing someVar!! with someVar ?: return  (or ?: continue)
                original_pattern = f"{expr}!!"
                suggested_pattern = f"({expr} ?: run {{ /* handle null */ return }})"
                suggested = line.replace(original_pattern, suggested_pattern, 1)
                fixes.append({
                    "file": file_path,
                    "line_number": i + 1,
                    "issue_type": "null_assertion",
                    "original": line,
                    "suggested": suggested,
                    "description": f"Replace !! null assertion at line {i + 1}",
                    "confidence": 75,
                    "can_apply": True,
                    "is_applied": False,
                    "requires_review": True,   # dev should verify the null handling
                    "diff": f"- {line}\n+ {suggested}",
                })
        return fixes

    def _fix_logd(self, code: str, file_path: str) -> List[Dict]:
        """Remove debug Log.d calls before release."""
        fixes = []
        for i, line in enumerate(code.splitlines()):
            if "Log.d(" in line:
                # Comment it out rather than delete — safer
                suggested = f"// [pre-release] {line.strip()}"
                fixes.append({
                    "file": file_path,
                    "line_number": i + 1,
                    "issue_type": "logd",
                    "original": line,
                    "suggested": suggested,
                    "description": f"Comment out Log.d at line {i + 1}",
                    "confidence": 85,
                    "can_apply": True,
                    "is_applied": False,
                    "requires_review": False,
                    "diff": f"- {line}\n+ {suggested}",
                })
        return fixes

    # ──────────────────────────────────────────────
    # Public: generate all fixes for a file
    # ──────────────────────────────────────────────

    def generate_fixes(self, file_path: str, code: str, issues: List[Dict]) -> List[Dict]:
        """
        BUG FIX: original only returned ONE fix per issue type per file.
        Now calls the correct _fix_* method for every issue type found,
        including null_assertion which was previously unhandled.
        """
        fixes = []

        issue_types = {i.get("type") for i in issues}

        if "http_url" in issue_types:
            fixes.extend(self._fix_http_urls(code, file_path))

        if "println" in issue_types:
            fixes.extend(self._fix_printlns(code, file_path))

        if "todo" in issue_types:
            fixes.extend(self._fix_todos(code, file_path))

        # BUG FIX: this case was missing — null_assertions were silently dropped
        if "null_assertion" in issue_types:
            fixes.extend(self._fix_null_assertions(code, file_path))

        if "logd" in issue_types:
            fixes.extend(self._fix_logd(code, file_path))

        return fixes

    # ──────────────────────────────────────────────
    # Batch & undo
    # ──────────────────────────────────────────────

    def apply_batch_fixes(self, fixes: List[Dict]) -> Tuple[int, List[Dict], List[Dict]]:
        applied, failed = [], []
        for fix in fixes:
            if fix.get("can_apply", True) and not fix.get("is_applied", False):
                success, msg = self.apply_fix_direct(
                    fix["file"],
                    fix["original"],
                    fix["suggested"],
                    line_number=fix.get("line_number"),
                )
                if success:
                    fix["is_applied"] = True
                    applied.append(fix)
                else:
                    failed.append({"fix": fix, "error": msg})
        return len(applied), applied, failed

    def undo_last_fix(self) -> Tuple[bool, str]:
        if not self.fix_history:
            return False, "No fixes to undo."

        entry = self.fix_history[-1]
        original_path = os.path.join(self.project_path, entry["file"])
        backup_path   = os.path.join(self.project_path, entry["backup"])

        if not os.path.exists(backup_path):
            return False, f"Backup file missing: {backup_path}"

        try:
            shutil.copy2(backup_path, original_path)
            self.fix_history.pop()
            self._save_history()
            return True, f"Restored {entry['file']} from backup."
        except Exception as e:
            return False, f"Restore failed: {e}"

    def get_fix_summary(self, fixes: List[Dict]) -> Dict:
        return {
            "total": len(fixes),
            "can_auto_apply": sum(1 for f in fixes if f.get("can_apply")),
            "requires_review": sum(1 for f in fixes if f.get("requires_review")),
            "already_applied": sum(1 for f in fixes if f.get("is_applied")),
        }