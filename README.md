# Digital Twin — Zirconia Oxygen Sensor (OBOGS)

A full-stack **Digital Twin** system for monitoring, simulating, and predicting the health of a **Zirconia Oxygen Sensor** in an **Aircraft On-Board Oxygen Generation System (OBOGS)**.

---

## 🖥️ Dashboard Preview

Live real-time monitoring dashboard with:
- **Health ring gauge** — composite sensor health (0-100%)
- **6 live time-series charts** — O₂, temperature, voltage, pressure, drift, health
- **Remaining Useful Life** countdown with confidence intervals
- **Fault detection** — heater failure, pressure leak, cracks, wiring faults
- **Alert feed** — severity-colored real-time alerts
- **Flight phase indicator** — Ground → Climb → Cruise → Descent
- **Fault injection** — test any failure scenario with one click

---

## ⚡ Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/DigitalTwin.git
cd DigitalTwin

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python launcher.py
# OR
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 5. Open in browser
#    http://127.0.0.1:8000
```

---

## 🏗️ Architecture

```
Sensor Simulator
      │
      ▼
FastAPI Backend
      │
      ├── Physics Model     (Nernst Equation)
      ├── Thermal Model     (Heat Balance: dT/dt)
      ├── Aging Model       (Arrhenius Degradation)
      ├── Drift Model       (Calibration Error)
      ├── Noise Model       (White + Flicker + EMI)
      ├── Fault Detection   (Residual Analysis)
      ├── State Estimation  (Extended Kalman Filter)
      ├── Health Index      (Composite Score 0-100)
      ├── RUL Prediction    (Monte Carlo)
      └── AI Forecasting    (Ensemble Regression)
            │
            ▼
      SQLite Database
            │
            ▼
      HTML Dashboard (Chart.js)
```

---

## 📦 Build Windows .exe

> Run this **on Windows** only (PyInstaller is platform-specific)

```bash
# Install PyInstaller (already in requirements.txt)
pip install pyinstaller

# Build the .exe
python build.py

# Output:
#   dist/DigitalTwin/DigitalTwin.exe
```

Double-click `DigitalTwin.exe` → server starts → browser opens automatically.

---

## 📐 Physics Models

| Model | Formula | Purpose |
|-------|---------|---------|
| Nernst Equation | `E = (RT/nF) × ln(P_ref/P_O₂)` | Ideal sensor voltage |
| Heat Balance | `dT/dt = (Q_heat - Q_conv - Q_rad) / mCp` | Sensor temperature |
| Arrhenius | `k = A × exp(-Ea/kT)` | Degradation rate |
| Coffin-Manson | `N_f = C × ΔT^(-n)` | Thermal fatigue cycles |
| Kalman Filter | `x̂ = x̂⁻ + K(z - Hx̂⁻)` | True O₂ estimation |

See [DOCUMENTATION.md](DOCUMENTATION.md) for full derivations and worked examples.

---

## 🗂️ Project Structure

```
DigitalTwin/
├── launcher.py          # Entry point
├── build.py             # PyInstaller build script
├── requirements.txt     # Dependencies
├── DOCUMENTATION.md     # Full technical documentation
│
└── app/
    ├── main.py          # FastAPI application
    ├── config.py        # Physical constants & thresholds
    ├── api/             # REST endpoints
    ├── models/          # 11 physics & ML models
    ├── services/        # Simulator, pipeline, alerts
    ├── database/        # SQLite manager
    ├── templates/       # HTML pages
    └── static/          # CSS & JavaScript
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard |
| GET | `/api/sensor/live` | Latest reading |
| GET | `/api/dashboard/summary` | All metrics |
| GET | `/api/health/history` | Health trend |
| GET | `/api/alerts/recent` | Active alerts |
| POST | `/api/sensor/fault?fault_type=X` | Inject fault |
| GET | `/docs` | Interactive API docs |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| Database | SQLite (aiosqlite) |
| Frontend | HTML + CSS + Vanilla JS |
| Charts | Chart.js |
| Physics | NumPy + SciPy |
| ML | scikit-learn |
| Packaging | PyInstaller |

---

## 📖 Full Documentation

See **[DOCUMENTATION.md](DOCUMENTATION.md)** for:
- Complete formula derivations with physics explanations
- Why each formula was chosen
- All 11 model descriptions
- Database schema
- Configuration reference
- Run & build instructions
