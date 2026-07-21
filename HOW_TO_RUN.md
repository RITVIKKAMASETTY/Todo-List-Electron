# How to Run This Project

**Read this file completely before doing anything.**

There are **two things** you might want to do:

| Task | Time | What you get |
|------|------|--------------|
| **A. Run the dashboard locally** | 2 minutes | Live dashboard at http://127.0.0.1:8000 |
| **B. Build the Windows .exe** | 10 minutes | A standalone app with no Python needed |

---

## Your Situation: Jupyter Notebook on Windows

> ✅ **Good news**: You do NOT need a separate terminal.
> Everything can be done from inside Jupyter Notebook using `!` commands.

---

## A. Run the Dashboard Locally

### Method 1 — Run from Jupyter Notebook (Recommended)

Open Jupyter Notebook. Navigate to the project folder. Click **New → Python 3**.

Run these cells **one at a time** (Shift+Enter):

**Cell 1 — Install dependencies (only needed once)**
```python
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
```

**Cell 2 — Start the server (non-blocking)**
```python
%run jupyter_run.py
```

That's it. The browser opens automatically. The notebook stays usable.

> **Why `jupyter_run.py` instead of `launcher.py`?**
> `launcher.py` blocks the cell forever (it runs a web server that never stops).
> `jupyter_run.py` runs the server in the background using a thread,
> so your Jupyter notebook stays interactive.

**To stop the server:**
Go to **Kernel → Restart** in the Jupyter menu.

---

### Method 2 — Using Jupyter's Built-in Terminal

Jupyter Notebook has its own terminal. You don't need a separate Command Prompt.

1. In the Jupyter file browser, click **New → Terminal**
2. A black terminal window opens inside your browser
3. Type these commands:

```bash
cd C:\path\to\DigitalTwin

pip install -r requirements.txt

python launcher.py
```

The browser opens automatically. To stop, press **Ctrl+C** in the terminal.

---

### Method 3 — Command Prompt / PowerShell (if available)

```bash
# Open Command Prompt (Win+R → type cmd → Enter)

cd C:\path\to\DigitalTwin

# Activate virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python launcher.py
```

Dashboard opens at **http://127.0.0.1:8000**

---

## B. Build the Windows .exe

### Method 1 — One-Click Build Script (Recommended for Jupyter)

This is the easiest way. A single script does everything automatically.

Open Jupyter Notebook. Navigate to the project folder. Click **New → Python 3**.

**Cell 1 — (Optional) Set your project folder if Jupyter opened in wrong location**
```python
import os
print("Current folder:", os.getcwd())

# If the folder above is NOT your DigitalTwin folder, uncomment and fix:
# os.chdir(r"C:\Users\YourName\Downloads\DigitalTwin")
```

**Cell 2 — Run the full build script**
```python
%run build_exe_jupyter.py
```

The script will:
- ✅ Check Python version
- ✅ Verify project files exist
- ✅ Install all dependencies
- ✅ Install PyInstaller
- ✅ Clean old build files
- ✅ Build the .exe (5-15 minutes — wait for it)
- ✅ Confirm success and open the output folder

> ⏳ The cell will show `[*]` for 5-15 minutes while building. **Do not interrupt.**
> When done it prints a big `✅ BUILD SUCCESSFUL!` box.

---

### Method 2 — Using Jupyter's Built-in Terminal

1. In the Jupyter file browser, click **New → Terminal**
2. Run:

```bash
cd C:\path\to\DigitalTwin

pip install -r requirements.txt
pip install pyinstaller

python build.py
```

---

## Where Is the .exe After Building?

```
DigitalTwin\
└── dist\
    └── DigitalTwin\
        ├── DigitalTwin.exe     ← Double-click this to run
        └── _internal\          ← KEEP THIS FOLDER NEXT TO THE .exe
```

> ⚠️ **IMPORTANT**: The `_internal` folder must always be in the same folder
> as `DigitalTwin.exe`. Do not separate them.
> To share the app, zip the entire `dist\DigitalTwin\` folder.

---

## What Happens When You Double-Click the .exe

1. A black terminal window appears (this is the server — don't close it)
2. Your browser opens automatically at `http://127.0.0.1:8000`
3. The dashboard loads with live sensor data
4. To stop: close the black terminal window

---

## Common Problems and Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Dependencies not installed | Run Cell 1 again |
| `Address already in use` | Server already running | Stop the old server first (Kernel → Restart) |
| `command not found: uvicorn` | Virtual env not active | Use `python -m uvicorn ...` instead |
| Cell 2 stuck at `[*]` for >20 min | PyInstaller is slow | Normal — just wait |
| `.exe` opens and closes instantly | Missing `_internal` folder | Keep both together |
| Dashboard shows no data | Server just started | Wait 5 seconds and refresh |

---

## Do You Need to Run Each File Separately?

**No.** You only ever need to run **one** of these:

| File | What it does | When to use |
|------|-------------|-------------|
| `jupyter_run.py` | Starts server in background (Jupyter-friendly) | Running locally in Jupyter |
| `launcher.py` | Starts server + opens browser (blocks terminal) | Running from Command Prompt |
| `build.py` | Builds the Windows .exe | One-time build only |

All the other files (`app/main.py`, `app/models/physics.py`, etc.) are imported automatically — you never run them directly.

---

## File That Does What

```
You run ONE of these:
┌─────────────────┐         ┌──────────────────┐
│  jupyter_run.py │  ──OR── │   launcher.py    │
│ (for Jupyter)   │         │ (for terminal)   │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         └──────────┬────────────────┘
                    ▼
              app/main.py           ← FastAPI app
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
  app/models/  app/services/  app/database/
  (11 models)  (simulator,    (SQLite)
               pipeline,
               alerts)
```

---

## Quick Command Reference

```bash
# Run locally (terminal)
python launcher.py

# Run locally (Jupyter cell)
%run jupyter_run.py

# Build .exe (terminal)
python build.py

# Build .exe (Jupyter cell)
import subprocess, sys
subprocess.run([sys.executable, "build.py"])

# Check what's running on port 8000
# Windows:
netstat -ano | findstr :8000

# Kill it (replace 1234 with PID from above)
taskkill /PID 1234 /F
```
