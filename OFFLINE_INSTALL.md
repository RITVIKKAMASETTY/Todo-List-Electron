# Offline Installation Guide — All Required Packages

This file lists **every single package** you need to download from PyPI
and install on the offline Windows machine.

Flask has far fewer dependencies than FastAPI:
- **FastAPI needed**: 20+ packages (starlette, pydantic, pydantic-core, uvicorn, aiosqlite, anyio, h11, httptools...)
- **Flask needs**: only 8 packages + scientific ones below

---

## Complete Package List (17 packages total)

### Group 1 — Flask Web Framework (8 packages)

| Package | Version | What it does | Download link |
|---------|---------|-------------|---------------|
| `flask` | **3.1.0** | The web framework | https://pypi.org/project/flask/3.1.0/#files |
| `werkzeug` | **3.1.3** | Flask's internal HTTP toolkit | https://pypi.org/project/werkzeug/3.1.3/#files |
| `jinja2` | **3.1.6** | HTML template engine | https://pypi.org/project/jinja2/3.1.6/#files |
| `markupsafe` | **3.0.2** | Required by Jinja2 | https://pypi.org/project/markupsafe/3.0.2/#files |
| `click` | **8.1.8** | Command-line support for Flask | https://pypi.org/project/click/8.1.8/#files |
| `itsdangerous` | **2.2.0** | Security signing (required by Flask) | https://pypi.org/project/itsdangerous/2.2.0/#files |
| `blinker` | **1.9.0** | Signal support (required by Flask 3.x) | https://pypi.org/project/blinker/1.9.0/#files |
| `waitress` | **3.0.1** | Windows WSGI server (replaces uvicorn) | https://pypi.org/project/waitress/3.0.1/#files |

### Group 2 — Scientific / AI (9 packages)

| Package | Version | What it does | Download link |
|---------|---------|-------------|---------------|
| `numpy` | **1.26.4** | Arrays and math (used by all models) | https://pypi.org/project/numpy/1.26.4/#files |
| `scipy` | **1.13.1** | Physics optimisation, curve fitting | https://pypi.org/project/scipy/1.13.1/#files |
| `scikit-learn` | **1.5.1** | AI prediction (ensemble regression) | https://pypi.org/project/scikit-learn/1.5.1/#files |
| `joblib` | **1.4.2** | Required by scikit-learn | https://pypi.org/project/joblib/1.4.2/#files |
| `threadpoolctl` | **3.5.0** | Required by scikit-learn | https://pypi.org/project/threadpoolctl/3.5.0/#files |
| `pandas` | **2.2.2** | Data handling in prediction model | https://pypi.org/project/pandas/2.2.2/#files |
| `python-dateutil` | **2.9.0** | Required by pandas | https://pypi.org/project/python-dateutil/2.9.0.post0/#files |
| `six` | **1.16.0** | Required by python-dateutil | https://pypi.org/project/six/1.16.0/#files |
| `pytz` | **2024.2** | Timezone support for pandas | https://pypi.org/project/pytz/2024.2/#files |


### NOT needed (these are Python built-ins — already in Python):
- `sqlite3` ← built into Python
- `threading` ← built into Python
- `json` ← built into Python
- `os`, `sys`, `time`, `math` ← all built into Python

---

## Step-by-Step: Download on Internet Machine

### Option A — Easiest: pip download (recommended)

On any machine WITH internet, run this one command:

```bash
pip download flask waitress numpy scipy scikit-learn pandas --dest C:\offline_packages --python-version 3.11 --platform win_amd64 --only-binary=:all:
```

This downloads all `.whl` files (pre-built for Windows 64-bit Python 3.11)
into a folder called `C:\offline_packages`.

Copy that folder to the offline Windows machine (USB drive / shared folder).

Then on the **offline Windows machine**:

```bash
pip install --no-index --find-links=C:\offline_packages flask waitress numpy scipy scikit-learn pandas
```

Done. pip automatically installs all dependencies from the local folder.

---

### Option B — Manual Download (if Option A fails)

Download these exact files from PyPI. On each link below, click **"Download files"**
and pick the `.whl` file matching **Windows 64-bit / Python 3.11**
(look for `cp311-cp311-win_amd64` in the filename).

#### Exact files to download:

**Flask group:**
```
flask-3.1.0-py3-none-any.whl
werkzeug-3.1.3-py3-none-any.whl
jinja2-3.1.6-py3-none-any.whl
markupsafe-3.0.2-cp311-cp311-win_amd64.whl
click-8.1.8-py3-none-any.whl
itsdangerous-2.2.0-py3-none-any.whl
blinker-1.9.0-py3-none-any.whl
waitress-3.0.1-py3-none-any.whl
```

**Scientific group:**
```
numpy-1.26.4-cp311-cp311-win_amd64.whl
scipy-1.13.1-cp311-cp311-win_amd64.whl
scikit_learn-1.5.1-cp311-cp311-win_amd64.whl
joblib-1.4.2-py3-none-any.whl
threadpoolctl-3.5.0-py3-none-any.whl
pandas-2.2.2-cp311-cp311-win_amd64.whl
python_dateutil-2.9.0.post0-py2.py3-none-any.whl
six-1.16.0-py2.py3-none-any.whl
pytz-2024.2-py2.py3-none-any.whl
```

#### Install command (run once for each .whl file):

```bash
pip install flask-3.1.0-py3-none-any.whl
pip install werkzeug-3.1.3-py3-none-any.whl
pip install jinja2-3.1.6-py3-none-any.whl
pip install markupsafe-3.0.2-cp311-cp311-win_amd64.whl
pip install click-8.1.8-py3-none-any.whl
pip install itsdangerous-2.2.0-py3-none-any.whl
pip install blinker-1.9.0-py3-none-any.whl
pip install waitress-3.0.1-py3-none-any.whl
pip install numpy-1.26.4-cp311-cp311-win_amd64.whl
pip install scipy-1.13.1-cp311-cp311-win_amd64.whl
pip install joblib-1.4.2-py3-none-any.whl
pip install threadpoolctl-3.5.0-py3-none-any.whl
pip install scikit_learn-1.5.1-cp311-cp311-win_amd64.whl
pip install six-1.16.0-py2.py3-none-any.whl
pip install python_dateutil-2.9.0.post0-py2.py3-none-any.whl
pip install pytz-2024.2-py2.py3-none-any.whl
pip install pandas-2.2.2-cp311-cp311-win_amd64.whl
```

#### Or install all at once from folder:

Put all `.whl` files in one folder e.g. `C:\whl_files\` then run:

```bash
pip install C:\whl_files\*.whl
```

---

## From Jupyter Notebook (no terminal needed)

If you can only use Jupyter Notebook, put all `.whl` files in a folder
(e.g. `C:\whl_files\`) then run this in a Jupyter cell:

```python
import subprocess, sys, os

whl_folder = r"C:\whl_files"   # ← change this to your folder

# Install in correct order
packages = [
    "markupsafe",
    "click", "itsdangerous", "blinker",
    "jinja2", "werkzeug", "flask",
    "waitress",
    "numpy",
    "scipy",
    "joblib", "threadpoolctl", "scikit_learn",
    "six", "python_dateutil", "pytz", "pandas",
]

whl_files = [f for f in os.listdir(whl_folder) if f.endswith(".whl")]

for pkg in packages:
    match = [f for f in whl_files if f.lower().startswith(pkg.lower())]
    if match:
        path = os.path.join(whl_folder, match[0])
        print(f"Installing {match[0]}...")
        subprocess.run([sys.executable, "-m", "pip", "install", path, "--quiet"])
        print(f"  ✅ Done")
    else:
        print(f"  ⚠️  Not found: {pkg}")

print("\n✅ All packages installed!")
```

---

## Verify Everything Is Installed

Run this in a Jupyter cell to confirm:

```python
packages = ["flask", "werkzeug", "jinja2", "markupsafe", "click",
            "itsdangerous", "blinker", "waitress",
            "numpy", "scipy", "sklearn", "joblib",
            "threadpoolctl", "pandas"]

for pkg in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "?")
        print(f"  ✅ {pkg:<20} {ver}")
    except ImportError:
        print(f"  ❌ {pkg:<20} NOT INSTALLED")
```

---

## Which Python Version?

Download files for the Python version you have on Windows.

Check your Python version in Jupyter:
```python
import sys
print(sys.version)
```

| Your Python | File suffix to look for |
|-------------|------------------------|
| 3.11 | `cp311-cp311-win_amd64` |
| 3.10 | `cp310-cp310-win_amd64` |
| 3.12 | `cp312-cp312-win_amd64` |

Files ending in `-py3-none-any.whl` work on **any** Python 3 version.

---

## PyInstaller (only needed to build the .exe)

PyInstaller is only needed on the machine that builds the `.exe`.
It does NOT need to be installed on the machine that runs the `.exe`.

```
pyinstaller-6.9.0-py3-none-win_amd64.whl
```

Download from: https://pypi.org/project/pyinstaller/#files
