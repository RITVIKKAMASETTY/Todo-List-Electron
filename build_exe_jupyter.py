"""
build_exe_jupyter.py
====================
Run this from a Jupyter Notebook cell to build the Windows .exe.

USAGE (in a Jupyter Notebook cell):
    %run build_exe_jupyter.py

This script will:
    Step 1 — Check Python version
    Step 2 — Install all dependencies
    Step 3 — Install PyInstaller
    Step 4 — Build the .exe  (takes 5-15 minutes, please wait)
    Step 5 — Confirm .exe was created and show location
"""

import subprocess
import sys
import os
import time

# ── Helper ────────────────────────────────────────────────────────
def run(description, command):
    print(f"\n{'─'*55}")
    print(f"  {description}")
    print(f"{'─'*55}")
    result = subprocess.run(command, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"\n  ❌ FAILED — see error above")
        sys.exit(1)
    print(f"  ✅ Done")
    return result

# ═════════════════════════════════════════════════════════════════
print()
print("╔═══════════════════════════════════════════════════════╗")
print("║   Digital Twin — Windows .exe Builder                ║")
print("║   Zirconia Oxygen Sensor (OBOGS)                     ║")
print("╚═══════════════════════════════════════════════════════╝")
print()

# ── Step 1: Python check ──────────────────────────────────────────
print("STEP 1 — Checking Python")
print(f"  Python version : {sys.version.split()[0]}")
print(f"  Python location: {sys.executable}")

major, minor = sys.version_info[:2]
if major < 3 or minor < 10:
    print(f"\n  ❌ Python 3.10+ is required. You have {major}.{minor}")
    print("     Download from: https://www.python.org/downloads/")
    sys.exit(1)
print("  ✅ Python version OK")

# ── Step 2: Check project folder ─────────────────────────────────
print("\nSTEP 2 — Checking project folder")
cwd = os.getcwd()
print(f"  Current folder: {cwd}")

required = ["app", "launcher.py", "build.py", "requirements.txt"]
missing = [f for f in required if not os.path.exists(f)]

if missing:
    print(f"\n  ❌ Missing files: {missing}")
    print(f"     You are in the wrong folder!")
    print(f"     Current folder: {cwd}")
    print()
    print("     Fix: Add this line BEFORE running this script:")
    print(r"     os.chdir(r'C:\path\to\your\DigitalTwin')")
    sys.exit(1)
print("  ✅ All project files found")

# ── Step 3: Install dependencies ─────────────────────────────────
print("\nSTEP 3 — Installing dependencies from requirements.txt")
run(
    "pip install -r requirements.txt",
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
     "--quiet", "--progress-bar", "on"]
)

# ── Step 4: Install PyInstaller ───────────────────────────────────
print("\nSTEP 4 — Installing PyInstaller")
run(
    "pip install pyinstaller",
    [sys.executable, "-m", "pip", "install", "pyinstaller",
     "--quiet", "--progress-bar", "on"]
)

# Verify it installed
try:
    import PyInstaller
    print(f"  PyInstaller version: {PyInstaller.__version__}")
except ImportError:
    print("  ❌ PyInstaller not found after install — try restarting Jupyter kernel")
    sys.exit(1)

# ── Step 5: Clean old build ───────────────────────────────────────
print("\nSTEP 5 — Cleaning previous build (if any)")
import shutil
for folder in ["build", "dist"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"  Removed old {folder}/")
    else:
        print(f"  No old {folder}/ to clean")
print("  ✅ Clean")

# ── Step 6: BUILD ────────────────────────────────────────────────
print("\nSTEP 6 — Building .exe with PyInstaller")
print("  ⏳ This will take 5 to 15 minutes on Windows.")
print("  ⏳ The cell will show [*] while building.")
print("  ⏳ Do NOT interrupt — just wait.")
print()

start = time.time()
run(
    "python build.py",
    [sys.executable, "build.py"]
)
elapsed = time.time() - start

# ── Step 7: Verify ────────────────────────────────────────────────
print("\nSTEP 7 — Checking output")
exe_path = os.path.join("dist", "DigitalTwin", "DigitalTwin.exe")
internal  = os.path.join("dist", "DigitalTwin", "_internal")

if os.path.exists(exe_path):
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    abs_path = os.path.abspath(exe_path)

    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║              ✅  BUILD SUCCESSFUL!                    ║")
    print("╠═══════════════════════════════════════════════════════╣")
    print(f"║  .exe location:                                       ║")
    print(f"║  {abs_path[:51].ljust(51)} ║")
    print(f"║                                                       ║")
    print(f"║  File size : {size_mb:>6.1f} MB                              ║")
    print(f"║  Build time: {elapsed:>6.0f} seconds                          ║")
    print("╠═══════════════════════════════════════════════════════╣")
    print("║  HOW TO USE:                                          ║")
    print("║  1. Open dist\\DigitalTwin\\                           ║")
    print("║  2. Double-click DigitalTwin.exe                      ║")
    print("║  3. Browser opens → http://127.0.0.1:8000            ║")
    print("║                                                       ║")
    print("║  ⚠️  Keep _internal\\ folder next to the .exe          ║")
    print("║     Zip the whole dist\\DigitalTwin\\ folder to share  ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    # Open the output folder in Windows Explorer
    try:
        dist_folder = os.path.abspath(os.path.join("dist", "DigitalTwin"))
        os.startfile(dist_folder)
        print("  📁 Opened dist\\DigitalTwin\\ in Windows Explorer")
    except Exception:
        pass

else:
    print()
    print("  ❌ BUILD FAILED — DigitalTwin.exe not found")
    print(f"     Expected at: {os.path.abspath(exe_path)}")
    print()
    print("  Common causes:")
    print("  • Antivirus blocked PyInstaller (add project folder to exclusions)")
    print("  • Wrong project folder (check STEP 2 above)")
    print("  • Missing files in app/ folder")
    print()
    print("  Check the full error output above for more details.")
