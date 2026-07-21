"""
Build Script — PyInstaller Configuration for Windows .exe

Run on Windows to create a standalone executable:
    python build.py

This will produce:
    dist/DigitalTwin/DigitalTwin.exe

The .exe bundles FastAPI, Uvicorn, all models, templates,
static files, and SQLite. No Python installation needed on target.
"""

import PyInstaller.__main__
import os
import shutil

# ── Configuration ────────────────────────────────────────────────
APP_NAME = "DigitalTwin"
ENTRY_POINT = "launcher.py"
ICON = None  # Set to "app/static/images/icon.ico" if you have one

# ── Paths ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")

# ── Data files to include ────────────────────────────────────────
datas = [
    (os.path.join(APP_DIR, "templates"), os.path.join("app", "templates")),
    (os.path.join(APP_DIR, "static"), os.path.join("app", "static")),
]

# ── Hidden imports (modules imported dynamically) ────────────────
hidden_imports = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "fastapi",
    "starlette",
    "aiosqlite",
    "jinja2",
    "numpy",
    "scipy",
    "scipy.optimize",
    "sklearn",
    "sklearn.linear_model",
    "sklearn.preprocessing",
    "pandas",
    "app",
    "app.main",
    "app.config",
    "app.api",
    "app.api.sensor",
    "app.api.dashboard",
    "app.models",
    "app.models.physics",
    "app.models.thermal",
    "app.models.sensor_model",
    "app.models.aging",
    "app.models.drift",
    "app.models.noise",
    "app.models.fault",
    "app.models.state_estimation",
    "app.models.health",
    "app.models.rul",
    "app.models.prediction",
    "app.services",
    "app.services.simulator",
    "app.services.calculations",
    "app.services.alerts",
    "app.database",
    "app.database.database",
]


def build():
    """Run PyInstaller build."""
    print("=" * 60)
    print(f"  Building {APP_NAME}.exe")
    print("=" * 60)

    # Clean previous builds
    for folder in ["build", "dist"]:
        path = os.path.join(BASE_DIR, folder)
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"  Cleaned {folder}/")

    spec_file = os.path.join(BASE_DIR, f"{APP_NAME}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # Build arguments
    args = [
        ENTRY_POINT,
        f"--name={APP_NAME}",
        "--onedir",          # One directory (faster startup than --onefile)
        "--console",         # Show console for server logs
        "--noconfirm",
    ]

    # Add data files
    for src, dst in datas:
        args.append(f"--add-data={src}{os.pathsep}{dst}")

    # Add hidden imports
    for imp in hidden_imports:
        args.append(f"--hidden-import={imp}")

    # Add icon if available
    if ICON and os.path.exists(os.path.join(BASE_DIR, ICON)):
        args.append(f"--icon={ICON}")

    print(f"\n  Running PyInstaller with {len(args)} arguments...\n")
    PyInstaller.__main__.run(args)

    print("\n" + "=" * 60)
    print(f"  Build complete!")
    print(f"  Output: dist/{APP_NAME}/{APP_NAME}.exe")
    print("=" * 60)


if __name__ == "__main__":
    build()
