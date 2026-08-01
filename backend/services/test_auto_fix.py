# test_auto_fix.py
from backend.services.auto_fixer import AutoFixEngine

# Create a test file
test_code = """
class Test {
    fun test() {
        println("Hello World")
    }
}
"""

with open("test_fix.kt", "w") as f:
    f.write(test_code)

# Test the fix
fixer = AutoFixEngine(".")
issues = [{'type': 'println'}]
fixes = fixer.generate_fixes("test_fix.kt", test_code, issues)

print(f"Found {len(fixes)} fixes")

if fixes:
    print(f"Fix: {fixes[0]['original']} -> {fixes[0]['suggested']}")
    success, msg = fixer.apply_fix("test_fix.kt", fixes[0])
    print(f"Result: {msg}")

    # Check the file
    with open("test_fix.kt", "r") as f:
        new_code = f.read()
    print("\nNew file content:")
    print(new_code)