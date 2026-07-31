import re
import difflib
from typing import Dict, List, Optional


class AutoFixEngine:
    """AI-powered auto-fix engine for Android code issues"""

    def __init__(self):
        self.fix_patterns = {
            "todo": self._fix_todo,
            "println": self._fix_println,
            "null_assertion": self._fix_null_assertion,
            "hardcoded_string": self._fix_hardcoded_string,
            "http_url": self._fix_http_url,
            "magic_number": self._fix_magic_number,
            "deprecated_api": self._fix_deprecated_api,
        }

    def generate_fixes(self, file_path: str, code: str, issues: List[Dict]) -> List[Dict]:
        """Generate fix suggestions for each issue"""
        fixes = []

        for issue in issues:
            fix_function = self.fix_patterns.get(issue.get('type'))
            if fix_function:
                try:
                    fix_result = fix_function(code, issue)
                    if fix_result:
                        fixes.append({
                            'file': file_path,
                            'issue_type': issue.get('type'),
                            'original': fix_result.get('original', ''),
                            'suggested': fix_result.get('suggested', ''),
                            'diff': self._generate_diff(fix_result.get('original', ''),
                                                        fix_result.get('suggested', '')),
                            'confidence': fix_result.get('confidence', 70),
                            'description': fix_result.get('description', 'Auto-fix suggestion')
                        })
                except Exception as e:
                    continue

        return fixes

    def apply_fix(self, file_path: str, fix: Dict) -> bool:
        """Apply a fix to the file (simulated)"""
        # In production, this would modify the actual file
        # For demo, we just return success
        return True

    def _fix_todo(self, code: str, issue: Dict) -> Optional[Dict]:
        """Convert TODO to tracked issue format"""
        return {
            'original': '// TODO:',
            'suggested': '// FIXME: Tracked in issue tracking system',
            'description': 'Convert TODO to tracked issue format',
            'confidence': 80
        }

    def _fix_println(self, code: str, issue: Dict) -> Optional[Dict]:
        """Replace println with proper logging"""
        return {
            'original': 'println(',
            'suggested': 'Log.d(TAG, ',
            'description': 'Replace println with Android Log.d for production',
            'confidence': 85
        }

    def _fix_null_assertion(self, code: str, issue: Dict) -> Optional[Dict]:
        """Replace !! with safe handling"""
        return {
            'original': '!!',
            'suggested': '?.let { ... } ?: ',
            'description': 'Replace !! with safe call and Elvis operator',
            'confidence': 75
        }

    def _fix_hardcoded_string(self, code: str, issue: Dict) -> Optional[Dict]:
        """Extract hardcoded strings to strings.xml"""
        string_value = issue.get('value', '')
        string_name = self._generate_string_name(string_value)
        return {
            'original': f'"{string_value}"',
            'suggested': f'getString(R.string.{string_name})',
            'description': f'Move hardcoded string to strings.xml as R.string.{string_name}',
            'confidence': 80
        }

    def _fix_http_url(self, code: str, issue: Dict) -> Optional[Dict]:
        """Replace HTTP with HTTPS"""
        url = issue.get('value', '')
        if url.startswith('http://'):
            https_url = url.replace('http://', 'https://')
            return {
                'original': url,
                'suggested': https_url,
                'description': 'Replace insecure HTTP with HTTPS',
                'confidence': 95
            }
        return None

    def _fix_magic_number(self, code: str, issue: Dict) -> Optional[Dict]:
        """Extract magic number to constant"""
        magic = issue.get('value', '')
        context = issue.get('context', '')
        constant_name = self._suggest_constant_name(magic, context)
        return {
            'original': magic,
            'suggested': constant_name,
            'description': f'Extract magic number {magic} as {constant_name}',
            'confidence': 70
        }

    def _fix_deprecated_api(self, code: str, issue: Dict) -> Optional[Dict]:
        """Suggest modern alternatives for deprecated APIs"""
        deprecated = issue.get('api', '')
        alternatives = {
            'AsyncTask': 'Coroutine + Dispatcher.IO',
            'Handler()': 'Handler(Looper.getMainLooper())',
            'startActivityForResult': 'ActivityResultLauncher',
            'getExternalStorageDirectory': 'MediaStore',
        }
        if deprecated in alternatives:
            return {
                'original': deprecated,
                'suggested': alternatives[deprecated],
                'description': f'Replace deprecated {deprecated} with {alternatives[deprecated]}',
                'confidence': 85
            }
        return None

    def _generate_diff(self, original: str, suggested: str) -> str:
        """Generate unified diff"""
        original_lines = original.splitlines()
        suggested_lines = suggested.splitlines()
        diff = difflib.unified_diff(
            original_lines,
            suggested_lines,
            fromfile='original',
            tofile='suggested',
            lineterm=''
        )
        return '\n'.join(diff)

    def _suggest_constant_name(self, value: str, context: str) -> str:
        """Generate meaningful constant name based on context"""
        if 'timeout' in context.lower() or 'delay' in context.lower():
            return 'TIMEOUT_SECONDS'
        elif 'retry' in context.lower():
            return 'MAX_RETRY_COUNT'
        elif 'margin' in context.lower() or 'padding' in context.lower():
            return f'PADDING_{value}_DP'
        else:
            return f'CONSTANT_{value}'

    def _generate_string_name(self, string_value: str) -> str:
        """Generate resource name for strings"""
        name = string_value.lower()
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = name.replace(' ', '_')
        return f'label_{name[:30]}'


