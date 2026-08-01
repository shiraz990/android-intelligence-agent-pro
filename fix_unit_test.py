import os
import shutil
from datetime import datetime

file_path = "/Users/shiraz/Documents/Android/AutomationApp/app/src/test/java/com/app/githubactionautomation/ExampleUnitTest.kt"

print(f"🔧 Testing fix on: {file_path}")

if not os.path.exists(file_path):
    print(f"❌ File not found!")
    exit(1)

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The pattern to fix
original = 'http://d.android.com/tools/testing'
suggested = 'https://d.android.com/tools/testing'

print(f"Looking for: {original}")
print(f"Replace with: {suggested}")

if original not in content:
    print(f"❌ Pattern not found in file!")
    print("File content preview:")
    print(content[:500])
    exit(1)

print(f"✅ Pattern found!")

# Create backup
backup_dir = ".fix_backups"
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"ExampleUnitTest_{timestamp}.backup")
shutil.copy2(file_path, backup_path)
print(f"💾 Backup: {backup_path}")

# Apply fix
new_content = content.replace(original, suggested)

# Write the file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Fix applied successfully!")
print(f"\n📝 Updated content preview:")
print(new_content[:300])
