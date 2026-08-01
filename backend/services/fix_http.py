import os
import shutil
from datetime import datetime

# The file to fix
file_path = "/Users/shiraz/Documents/Android/AutomationApp/app/src/androidTest/java/com/app/githubactionautomation/ExampleInstrumentedTest.kt"

print("🔧 Fixing HTTP to HTTPS...")
print(f"📁 File: {file_path}")

# Check if file exists
if not os.path.exists(file_path):
    print(f"❌ File not found: {file_path}")
    exit(1)

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Look for the pattern
original = 'http://d.android.com/tools/testing'
suggested = 'https://d.android.com/tools/testing'

if original not in content:
    print(f"❌ Pattern not found: {original}")
    print("Content preview:")
    print(content[:500])
    exit(1)

# Create backup
backup_dir = ".fix_backups"
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"ExampleInstrumentedTest_{timestamp}.backup")

print(f"📦 Creating backup: {backup_path}")
shutil.copy2(file_path, backup_path)

# Apply the fix
new_content = content.replace(original, suggested)

# Write the file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Fix applied successfully!")
print(f"📁 Backup saved to: {backup_path}")
print("\n📝 Updated content preview:")
print(new_content[:300])

# Verify the fix
print("\n🔍 Verifying fix...")
with open(file_path, 'r', encoding='utf-8') as f:
    verified_content = f.read()
    if 'https://d.android.com/tools/testing' in verified_content:
        print("✅ Verified! HTTPS found in file")
    else:
        print("❌ Verification failed - HTTPS not found")