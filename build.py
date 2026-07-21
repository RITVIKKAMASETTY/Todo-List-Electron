"""
PyInstaller Build Script for Flask version.
"""

import PyInstaller.__main__
import os
import shutil

APP_NAME   = "DigitalTwin"
ENTRY_POINT = "launcher.py"
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
APP_DIR    = os.path.join(BASE_DIR, "app")

datas = [
    (os.path.join(APP_DIR, "templates"), os.path.join("app", "templates")),
    (os.path.join(APP_DIR, "static"),    os.path.join("app", "static")),
]

hidden_imports = [
    # Flask core
    "flask", "flask.json", "flask.templating",
    "werkzeug", "werkzeug.serving", "werkzeug.routing",
    "jinja2", "jinja2.ext",
    "click", "itsdangerous", "markupsafe",
    # Waitress (WSGI server)
    "waitress", "waitress.server",
    # Scientific
    "numpy", "numpy.core",
    "scipy", "scipy.optimize", "scipy.stats",
    "sklearn", "sklearn.linear_model", "sklearn.preprocessing",
    "pandas",
    # App modules
    "app", "app.main", "app.config",
    "app.api", "app.api.sensor", "app.api.dashboard",
    "app.models",
    "app.models.physics", "app.models.thermal",
    "app.models.sensor_model", "app.models.aging",
    "app.models.drift", "app.models.noise",
    "app.models.fault", "app.models.state_estimation",
    "app.models.health", "app.models.rul", "app.models.prediction",
    "app.services",
    "app.services.simulator", "app.services.calculations",
    "app.services.alerts",
    "app.database", "app.database.database",
    # Standard library (usually bundled but listed for safety)
    "sqlite3", "threading", "json", "os", "sys",
]


def build():
    print("=" * 60)
    print(f"  Building {APP_NAME}.exe  (Flask edition)")
    print("=" * 60)

    for folder in ["build", "dist"]:
        path = os.path.join(BASE_DIR, folder)
        if os.path.exists(path):
            shutil.rmtree(path)

    spec = os.path.join(BASE_DIR, f"{APP_NAME}.spec")
    if os.path.exists(spec):
        os.remove(spec)

    args = [
        ENTRY_POINT,
        f"--name={APP_NAME}",
        "--onedir",
        "--console",
        "--noconfirm",
    ]
    for src, dst in datas:
        args.append(f"--add-data={src}{os.pathsep}{dst}")
    for imp in hidden_imports:
        args.append(f"--hidden-import={imp}")

    PyInstaller.__main__.run(args)

    print("\n" + "=" * 60)
    print("  Build complete!")
    print(f"  Output: dist/{APP_NAME}/{APP_NAME}.exe")
    print("=" * 60)


if __name__ == "__main__":
    build()
