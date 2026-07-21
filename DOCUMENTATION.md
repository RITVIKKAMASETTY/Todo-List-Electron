# Digital Twin: Zirconia Oxygen Sensor (OBOGS)

## Complete Technical Documentation

A full-stack Digital Twin system for monitoring, simulating, and predicting the health of a **Zirconia Oxygen Sensor** operating inside an **Aircraft On-Board Oxygen Generation System (OBOGS)**.

---

## Table of Contents

1. [What is This Project?](#1-what-is-this-project)
2. [System Architecture](#2-system-architecture)
3. [How to Run Locally](#3-how-to-run-locally)
4. [How to Build Windows .exe](#4-how-to-build-windows-exe)
5. [Folder Structure](#5-folder-structure)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [Model 1 — Physics Model (Nernst Equation)](#8-model-1--physics-model-nernst-equation)
9. [Model 2 — Thermal Model (Heat Balance)](#9-model-2--thermal-model-heat-balance)
10. [Model 3 — Sensor Model (Impedance & Sensitivity)](#10-model-3--sensor-model-impedance--sensitivity)
11. [Model 4 — Aging Model (Arrhenius Degradation)](#11-model-4--aging-model-arrhenius-degradation)
12. [Model 5 — Drift Model (Calibration Error)](#12-model-5--drift-model-calibration-error)
13. [Model 6 — Noise Model (Electrical Noise)](#13-model-6--noise-model-electrical-noise)
14. [Model 7 — Fault Detection Model](#14-model-7--fault-detection-model)
15. [Model 8 — State Estimation (Extended Kalman Filter)](#15-model-8--state-estimation-extended-kalman-filter)
16. [Model 9 — Health Index (Composite Score)](#16-model-9--health-index-composite-score)
17. [Model 10 — Remaining Useful Life (RUL)](#17-model-10--remaining-useful-life-rul)
18. [Model 11 — Prediction Model (AI Forecasting)](#18-model-11--prediction-model-ai-forecasting)
19. [Services Layer](#19-services-layer)
20. [Frontend Dashboard](#20-frontend-dashboard)
21. [Configuration Reference](#21-configuration-reference)
22. [Tech Stack](#22-tech-stack)

---

## 1. What is This Project?

This is **not** just a dashboard. It is a **digital twin** — a virtual replica of a real physical sensor that:

- **Simulates** realistic sensor behavior including degradation over time
- **Monitors** oxygen concentration, temperature, pressure, voltage, and more
- **Detects** faults (heater failure, pressure leaks, cracks, wiring issues)
- **Estimates** the true oxygen concentration using sensor fusion (Kalman Filter)
- **Predicts** when the sensor will need replacement (Remaining Useful Life)
- **Alerts** maintenance crews before failure occurs

### The Physical System

```
Engine Bleed Air → Heat Exchanger → Compressor → Molecular Sieve (OBOGS)
                                                        │
                                                        ▼
                                                 Oxygen-Rich Air
                                                        │
                                                        ▼
                                              Zirconia Oxygen Sensor  ← THIS is what we model
                                                        │
                                                        ▼
                                                   Controller → Pilot Mask
```

The **Zirconia Oxygen Sensor** uses a solid electrolyte (yttria-stabilized zirconia, YSZ) heated to ~700°C. Oxygen ions migrate through the ceramic, generating a voltage proportional to the oxygen concentration difference across it. This voltage is described by the **Nernst Equation**.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    SENSOR SIMULATOR                          │
│  Generates synthetic flight data with aging & faults         │
└──────────────────────┬───────────────────────────────────────┘
                       │ Sensor Reading (every 1 second)
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI BACKEND                            │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Physics    │→│   Thermal   │→│   Aging     │          │
│  │   Model     │  │   Model     │  │   Model     │          │
│  │  (Nernst)   │  │  (Heat Bal) │  │ (Arrhenius) │          │
│  └─────────────┘  └─────────────┘  └──────┬──────┘          │
│                                            │                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────▼──────┐         │
│  │   Noise     │→│   Drift     │→│   Sensor    │          │
│  │   Model     │  │   Model     │  │   Model     │          │
│  └─────────────┘  └─────────────┘  └──────┬──────┘          │
│                                            │                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────▼──────┐         │
│  │   Fault     │→│   State     │→│   Health    │          │
│  │  Detection  │  │ Estimation  │  │   Index     │          │
│  │             │  │   (EKF)     │  │             │          │
│  └─────────────┘  └─────────────┘  └──────┬──────┘          │
│                                            │                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────▼──────┐         │
│  │    RUL      │→│ Prediction  │→│   Alert     │          │
│  │  (Monte     │  │ (Ensemble)  │  │   Engine    │          │
│  │   Carlo)    │  │             │  │             │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────┬───────────────────────────────────────┘
                       │ Store results
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    SQLite DATABASE                            │
│  sensor_data │ health │ predictions │ alerts                 │
└──────────────────────┬───────────────────────────────────────┘
                       │ Fetch via REST API
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                HTML + CSS + JavaScript DASHBOARD              │
│  Live gauges │ Charts │ Health ring │ Alerts │ RUL counter   │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow (Per Tick — Every 1 Second)

1. **Simulator** generates a sensor reading (O₂, temp, pressure, voltage, etc.)
2. **Physics Model** calculates what a perfect sensor would output (Nernst equation)
3. **Thermal Model** estimates the sensor element temperature (heat balance)
4. **Aging Model** calculates how much the sensor has degraded (Arrhenius)
5. **Drift Model** adds calibration drift (linear + sinusoidal + quadratic)
6. **Noise Model** adds electrical noise (white + flicker + EMI)
7. **State Estimation** fuses sensor + physics to find true O₂ (Kalman Filter)
8. **Fault Detection** checks for anomalies (residual analysis)
9. **Health Index** combines all degradation into one score (0-100)
10. **RUL** predicts hours until replacement (Monte Carlo)
11. **Prediction** forecasts future values (ensemble regression)
12. **Alert Engine** fires alerts if thresholds are crossed
13. All results are stored in **SQLite** and served to the **Dashboard**

---

## 3. How to Run Locally

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Step-by-Step

```bash
# 1. Navigate to the project directory
cd DigitalTwin

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the server
python launcher.py
# OR
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 6. Open your browser to:
#    http://127.0.0.1:8000
```

The server will:
- Initialize the SQLite database automatically
- Start the sensor simulator in the background
- Begin generating and processing data immediately
- Auto-open your browser (if using `launcher.py`)

### Stopping the Server

Press `Ctrl+C` in the terminal.

---

## 4. How to Build Windows .exe

### On Windows:

```bash
# 1. Install PyInstaller (already in requirements.txt)
pip install pyinstaller

# 2. Run the build script
python build.py

# 3. The .exe will be at:
#    dist/DigitalTwin/DigitalTwin.exe
```

### What the .exe Does

- Bundles Python + FastAPI + all models + templates + static files
- Creates a portable application — no Python installation needed on target
- Double-click to start → server starts → browser opens → dashboard loads

### Note

The `.exe` must be built **on Windows** (PyInstaller creates platform-specific binaries). The project is developed on macOS but the build script is designed for Windows packaging.

---

## 5. Folder Structure

```
DigitalTwin/
│
├── launcher.py              # Entry point (starts server + opens browser)
├── build.py                 # PyInstaller build script for .exe
├── requirements.txt         # Python dependencies
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application (heart of the system)
│   ├── config.py            # All constants, thresholds, and settings
│   │
│   ├── api/                 # REST API endpoints
│   │   ├── sensor.py        # /api/sensor/* endpoints
│   │   └── dashboard.py     # / and /api/dashboard/* endpoints
│   │
│   ├── models/              # Physics & ML models (the brain)
│   │   ├── physics.py       # Nernst equation
│   │   ├── thermal.py       # Heat balance
│   │   ├── sensor_model.py  # Impedance & sensitivity
│   │   ├── aging.py         # Arrhenius degradation
│   │   ├── drift.py         # Calibration drift
│   │   ├── noise.py         # Electrical noise sources
│   │   ├── fault.py         # Fault detection
│   │   ├── state_estimation.py  # Extended Kalman Filter
│   │   ├── health.py        # Composite health index
│   │   ├── rul.py           # Remaining Useful Life
│   │   └── prediction.py    # Time-series forecasting
│   │
│   ├── services/            # Business logic & orchestration
│   │   ├── simulator.py     # Synthetic sensor data generator
│   │   ├── calculations.py  # Model pipeline orchestrator
│   │   └── alerts.py        # Alert engine
│   │
│   ├── database/
│   │   ├── database.py      # SQLite connection & CRUD operations
│   │   └── twin.db          # SQLite database (auto-created)
│   │
│   ├── templates/           # HTML pages (Jinja2)
│   │   ├── dashboard.html   # Main dashboard
│   │   └── sensor.html      # Sensor detail page
│   │
│   └── static/              # CSS, JavaScript, images
│       ├── css/style.css     # Design system (dark theme, glassmorphism)
│       └── js/
│           ├── charts.js     # Chart.js configuration
│           └── dashboard.js  # Real-time data fetching & UI updates
│
└── venv/                    # Python virtual environment
```

---

## 6. Database Schema

### `sensor_data` — Raw sensor readings

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| timestamp | TEXT | ISO 8601 timestamp |
| oxygen | REAL | Oxygen concentration (%) |
| temperature | REAL | Air temperature (°C) |
| pressure | REAL | Air pressure (psi) |
| flow | REAL | Air flow rate (L/min) |
| humidity | REAL | Moisture (%) |
| voltage | REAL | Sensor output voltage (V) |
| current | REAL | Sensor current (A) |
| vibration | REAL | Vibration level (g) |
| heater_temp | REAL | Internal heater temperature (°C) |
| altitude | REAL | Flight altitude (feet) |
| flight_hours | REAL | Total operating hours |
| thermal_cycles | INTEGER | Number of heat/cool cycles |

### `health` — Health assessment records

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | ISO 8601 timestamp |
| health_score | REAL | Composite health (0-100) |
| drift | REAL | Calibration drift (%) |
| noise | REAL | Noise RMS |
| aging_factor | REAL | Aging factor (0-1) |
| sensitivity | REAL | Sensor sensitivity (0-1) |
| fault_probability | REAL | Fault probability (0-1) |

### `predictions` — Future value predictions

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | ISO 8601 timestamp |
| predicted_oxygen | REAL | Forecasted O₂ (%) |
| predicted_temperature | REAL | Forecasted temp (°C) |
| predicted_health | REAL | Forecasted health score |
| remaining_life | REAL | Hours until replacement |
| confidence | REAL | Prediction confidence (0-1) |

### `alerts` — System alerts

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | ISO 8601 timestamp |
| alert_type | TEXT | Category (health_critical, drift_warning, etc.) |
| severity | TEXT | info / warning / critical |
| message | TEXT | Human-readable alert message |
| acknowledged | INTEGER | 0 = unread, 1 = acknowledged |

---

## 7. API Endpoints

### Dashboard & Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard HTML page |
| GET | `/dashboard` | Same dashboard page |
| GET | `/sensor-detail` | Sensor detail page |

### Sensor Data API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sensor/live` | Latest sensor reading (JSON) |
| GET | `/api/sensor/history?minutes=N` | Historical readings |
| POST | `/api/sensor` | Manually inject a reading |
| GET | `/api/sensor/status` | Simulator status |
| POST | `/api/sensor/fault?fault_type=X&severity=Y` | Inject a fault |
| POST | `/api/sensor/clear-faults` | Clear all faults |

### Dashboard Data API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary` | Aggregated system status |
| GET | `/api/dashboard/twin` | Complete digital twin state |
| GET | `/api/health/history?limit=N` | Health score history |
| GET | `/api/predictions/latest` | Latest prediction |
| GET | `/api/alerts/recent?limit=N` | Recent alerts |

### Fault Types for Injection

| Fault Type | What It Simulates |
|------------|-------------------|
| `heater_failure` | Heater element stops working → sensor cools down |
| `pressure_leak` | Air pressure drops rapidly |
| `sensor_crack` | Ceramic element cracks → erratic voltage |
| `voltage_drop` | Output voltage drops → degraded signal |
| `wiring_fault` | Electrical connection degrades → current anomaly |

---

## 8. Model 1 — Physics Model (Nernst Equation)

**File:** `app/models/physics.py`

### What Does It Do?

Calculates the **ideal voltage** a perfect zirconia sensor would produce for a given oxygen concentration and temperature. This is the theoretical "truth" — any deviation from this is due to aging, drift, noise, or faults.

### The Nernst Equation

```
E = (R × T) / (n × F) × ln(P_ref / P_O₂)
```

| Symbol | Value | Meaning |
|--------|-------|---------|
| E | Calculated | Electromotive force (voltage) in Volts |
| R | 8.314 J/(mol·K) | Universal gas constant |
| T | Sensor temp (K) | Absolute temperature (Celsius + 273.15) |
| n | 4 | Electrons transferred per O₂ molecule |
| F | 96,485 C/mol | Faraday constant |
| P_ref | 0.2095 atm | Reference O₂ partial pressure (ambient air = 20.95%) |
| P_O₂ | Calculated | Measured O₂ partial pressure |

### Why This Formula?

The Nernst equation is **the fundamental governing equation** for all solid-state electrochemical oxygen sensors. Zirconia (ZrO₂) acts as a solid electrolyte — oxygen ions (O²⁻) migrate through the ceramic from high-O₂ side to low-O₂ side, generating a measurable voltage. This is not an approximation; it is the exact physics of how the sensor works.

### Example Calculation

At 700°C (973.15K) with 93% O₂ in OBOGS output and 29 psi total pressure:

```
P_O₂ = (93/100) × (29/14.696) = 1.836 atm
E = (8.314 × 973.15) / (4 × 96485) × ln(0.2095 / 1.836)
E = 0.02096 × ln(0.1141)
E = 0.02096 × (-2.170)
E = -0.04549 V
```

The negative voltage means O₂ is higher on the measurement side than the reference side (typical for OBOGS which enriches oxygen).

### Additional Functions

- **Inverse Nernst**: Convert voltage back to O₂ percentage
- **Pressure Compensation**: Adjust readings for altitude-induced pressure changes
- **Altitude to Pressure**: Barometric formula for flight altitude

---

## 9. Model 2 — Thermal Model (Heat Balance)

**File:** `app/models/thermal.py`

### What Does It Do?

Models the sensor's operating temperature. The zirconia sensor **must** be heated to ~700°C for the ionic conduction to work. If the heater fails or loses efficiency, the sensor readings become unreliable.

### Heat Balance Equation

```
dT/dt = (Q_heater - Q_convection - Q_radiation) / (m × Cp)
```

| Term | Formula | Meaning |
|------|---------|---------|
| Q_heater | PID-controlled, max 8W | Electrical heat input |
| Q_convection | h × A × (T_sensor - T_air) | Heat lost to air flow |
| Q_radiation | ε × σ × A × (T⁴_sensor - T⁴_ambient) | Heat lost as infrared radiation |
| m × Cp | 0.015 kg × 500 J/(kg·K) | Thermal mass of sensor element |

### Why These Formulas?

- **Convection (Newton's Cooling Law)**: Air flowing over the sensor carries away heat. Faster flow = more cooling. This is basic heat transfer physics.
- **Radiation (Stefan-Boltzmann Law)**: At 700°C, the sensor glows faintly and radiates significant infrared energy. `ε = 0.85` because zirconia is a good emitter.
- **Euler Integration**: We use `T_new = T_old + dT/dt × Δt` to step the temperature forward each tick. Simple but effective for our 1-second time step.

### Constants

| Symbol | Value | Meaning |
|--------|-------|---------|
| h | 50 W/(m²·K) base | Convective heat transfer coefficient |
| A | 2×10⁻⁴ m² | Sensor surface area |
| ε | 0.85 | Emissivity |
| σ | 5.67×10⁻⁸ W/(m²·K⁴) | Stefan-Boltzmann constant |
| m | 0.015 kg | Sensor element mass |
| Cp | 500 J/(kg·K) | Specific heat capacity |

### Why It Matters

If the thermal model detects the sensor is cooling below 600°C, it signals a **heater failure** — one of the most critical faults. The health score drops and an alert fires.

---

## 10. Model 3 — Sensor Model (Impedance & Sensitivity)

**File:** `app/models/sensor_model.py`

### What Does It Do?

Models the electrical characteristics of the sensor: impedance, sensitivity, and response time. A degrading sensor has higher impedance, lower sensitivity, and slower response.

### Impedance Model

```
Z_total = R_bulk + R_electrode + R_grain_boundary
```

Each resistance follows Arrhenius temperature dependence:

```
R(T) = R_ref × exp(Ea / k × (1/T - 1/T_ref))
```

| Component | Ref Resistance | Activation Energy | Aging Effect |
|-----------|---------------|-------------------|--------------|
| R_bulk (zirconia ceramic) | 50 Ω | 0.9 eV | +30% at end of life |
| R_electrode (platinum) | 30 Ω | 1.1 eV | +80% at end of life |
| R_grain_boundary | 20 Ω | 1.0 eV | +50% at end of life |

### Why Arrhenius for Impedance?

Ionic conduction in zirconia is a thermally activated process. The ions need energy to hop between lattice sites. Higher temperature → more ions hopping → lower resistance. This is fundamental solid-state physics (the same reason semiconductors conduct better when hot).

### Sensitivity Curve

```
S(T) = S₀ × exp(-Ea / (k × T)) × (1 - 0.4 × aging_factor)
```

Sensitivity tells us "how much voltage change per unit oxygen change." A new sensor at 700°C has sensitivity = 1.0. An old sensor might have sensitivity = 0.6, meaning it only responds to 60% of the actual O₂ change.

### Response Time (First-Order Lag)

```
τ × dy/dt + y = x
```

Discretized: `y_new = y_old + (x - y_old) × dt / (τ + dt)`

| Condition | Response Time (τ) |
|-----------|-------------------|
| New sensor, 700°C | ~2 seconds |
| New sensor, 500°C | ~8 seconds |
| Old sensor, 700°C | ~6 seconds |

### Why It Matters

This model tells us: "Even if the true O₂ changes instantly, the sensor output takes τ seconds to catch up." Older sensors are sluggish. This lag is crucial for flight safety — a slow sensor could miss a rapid O₂ drop.

---

## 11. Model 4 — Aging Model (Arrhenius Degradation)

**File:** `app/models/aging.py`

### What Does It Do?

Simulates how the sensor degrades over thousands of flight hours. The sensor doesn't fail suddenly — it slowly loses accuracy, sensitivity, and reliability.

### Arrhenius Degradation Rate

```
k = A × exp(-Ea / (k_B × T))
```

| Symbol | Value | Meaning |
|--------|-------|---------|
| A | 1×10⁻⁴ | Pre-exponential factor |
| Ea | 1.2×10⁻¹⁹ J | Activation energy for degradation |
| k_B | 1.381×10⁻²³ J/K | Boltzmann constant |
| T | Temperature (K) | Higher temp = faster degradation |

### Why Arrhenius?

The Arrhenius equation is the universal law for thermally activated processes. Electrode sintering (grain growth), chemical poisoning, and mechanical fatigue all follow this pattern. NASA and aircraft manufacturers use Arrhenius models for all high-temperature sensor life predictions.

### Sensitivity Decay

```
S(t) = S₀ × exp(-k × t)
```

A brand new sensor (S₀ = 1.0) at 700°C after 3000 hours might have S = 0.75 — it only responds to 75% of the real oxygen change.

### Electrode Sintering (Grain Growth)

```
d² - d₀² = K × t     (Parabolic growth law)
```

The platinum electrode grains grow larger over time at high temperature. Larger grains = smaller triple-phase boundary (TPB) = fewer reaction sites = lower performance.

### Thermal Cycling Fatigue (Coffin-Manson)

```
N_f = C × (ΔT)^(-n)
```

| Symbol | Value | Meaning |
|--------|-------|---------|
| C | 10⁶ | Material constant |
| n | 2.5 | Coffin-Manson exponent |
| ΔT | ~675°C | Temperature swing (25°C → 700°C) |

Every time the sensor heats up from cold to 700°C and cools back down, it accumulates fatigue damage. After N_f cycles, cracking occurs. Miner's rule sums the damage: `D = Σ(n_i / N_f_i)`. When D = 1, failure.

### Why It Matters

The aging model is the core of predictive maintenance. It answers: "How much life does this sensor have left?" without removing and testing it.

### Combined Aging Factor

```
aging = 0.4 × time_aging + 0.3 × cycle_damage + 0.3 × electrode_degradation
```

Multiplied by a humidity factor (humidity accelerates chemical poisoning of the electrode).

---

## 12. Model 5 — Drift Model (Calibration Error)

**File:** `app/models/drift.py`

### What Does It Do?

Models the gradual shift in sensor calibration. A drifting sensor reports O₂ = 92% when the true value is 95%. This error grows over time.

### Drift Formula

```
drift(t) = α×t + β×sin(ω×t) + γ×t² + random_walk + temp_offset
```

| Component | Formula | Rate | Why |
|-----------|---------|------|-----|
| Linear drift | α × t | 0.001 %/hour | Steady baseline shift from electrode aging |
| Sinusoidal drift | β × sin(ω×t) | ±0.05% | Periodic effects (thermal cycling, day/night) |
| Quadratic drift | γ × t² | 10⁻⁷ × t² | Accelerating drift as sensor nears end of life |
| Random walk | N(0, 0.001) cumulative | Stochastic | Unpredictable micro-changes in electrode surface |
| Temperature offset | 0.01 × (T - 700) | 0.01 %/°C | Off-temperature operation shifts baseline |

### Why These Components?

Real sensor calibration drift has been studied extensively (see IEEE Sensors Journal literature). It is never purely linear — there are periodic environmental effects, accelerating degradation, and stochastic variations. Our five-component model captures all of these mechanisms.

### Example

After 1000 flight hours:
```
Linear:     0.001 × 1000 = 1.0%
Sinusoidal: 0.05 × sin(10) = ~0.027%
Quadratic:  10⁻⁷ × 10⁶ = 0.1%
Random:     ~0.3% (accumulated)
Total drift: ~1.4%
```

The sensor now reads 91.6% instead of 93%. The digital twin knows this and compensates.

---

## 13. Model 6 — Noise Model (Electrical Noise)

**File:** `app/models/noise.py`

### What Does It Do?

Simulates the electrical noise present in every real sensor signal. Without noise modeling, the digital twin would be unrealistically clean.

### Noise Sources

| Source | Distribution | Amplitude | Why It Exists |
|--------|-------------|-----------|---------------|
| **White noise** | Gaussian N(0, σ) | σ = 0.02% | Thermal noise in electronics (Johnson-Nyquist noise) |
| **1/f Flicker noise** | Cauchy × 0.1 | 0.005 base, ×4 with aging | Contact resistance fluctuations, gets worse with age |
| **Quantization noise** | Uniform ±step/2 | step = 0.01% | ADC digitization (12-bit typical) |
| **EMI spikes** | Bernoulli × Uniform | 2% probability, ±0.5% | Electromagnetic interference from aircraft avionics |

### Combined Noise

```
noise_total = white + flicker + quantization + EMI_spike
noise_rms = √(white² + flicker² + quantization² + EMI²)
```

### Signal-to-Noise Ratio

```
SNR = 20 × log₁₀(|signal| / noise_rms)    [dB]
```

A healthy sensor has SNR > 40 dB. Below 20 dB, the signal is unreliable.

### Why Model Noise?

1. **Realistic simulation**: Real sensor data is noisy. Clean data would be unrealistic.
2. **Aging indicator**: Noise increases as the sensor degrades (especially 1/f noise). Rising noise is an early warning sign.
3. **Filter design**: The Kalman filter needs to know the noise characteristics to optimally estimate the true value.

---

## 14. Model 7 — Fault Detection Model

**File:** `app/models/fault.py`

### What Does It Do?

Detects five types of sensor faults by comparing measured values against expected physics-based predictions.

### Fault Types & Detection Methods

#### 1. Heater Failure
```
IF heater_temp < 600°C THEN fault detected
severity = 1 - (heater_temp / 600)
```
**Why 600°C?** Below this temperature, zirconia's ionic conductivity drops dramatically and the Nernst equation becomes unreliable.

#### 2. Pressure Leak
```
pressure_drop_rate = (P_previous - P_current) / dt × 60    [psi/min]
IF pressure_drop_rate > 0.5 psi/min THEN fault detected
```
**Why?** A sudden pressure drop in the OBOGS system means a seal failure. Gradual changes are normal (altitude).

#### 3. Sensor Crack
```
CV = (std_dev(voltage_last_10) / mean(voltage_last_10)) × 100    [%]
IF CV > 5% THEN fault detected
```
**Why Coefficient of Variation?** A cracked ceramic produces erratic, unpredictable voltage spikes. Normal CV < 2%.

#### 4. Voltage Drop
```
IF voltage < 0.6V THEN fault detected
severity = 1 - (voltage / 0.6)
```
**Why 0.6V?** This represents significant signal degradation below the normal operating range (~0.82V).

#### 5. Wiring Fault
```
impedance = voltage / current
IF impedance < 10Ω (short) OR impedance > 500Ω (open) THEN fault
```
**Why?** Normal impedance is 50-200Ω. Extreme values indicate wiring damage.

### Overall Fault Probability

```
fault_prob = max(severities) + 0.05 × max(num_faults - 1, 0)
```

Multiple simultaneous faults compound the probability (5% boost per additional fault).

---

## 15. Model 8 — State Estimation (Extended Kalman Filter)

**File:** `app/models/state_estimation.py`

### What Does It Do?

Answers the question: **"What is the TRUE oxygen concentration?"**

The sensor gives a noisy, drifted, aged measurement. The physics model gives a theoretical prediction. The Kalman filter fuses both to produce the best estimate.

### State Vector

```
x = [O₂_true, T_sensor, drift, sensitivity]
```

### The Two Steps

**1. Predict Step:**
```
x̂⁻ = F × x̂⁺         (propagate state forward)
P⁻ = F × P⁺ × Fᵀ + Q  (propagate uncertainty)
```

**2. Update Step:**
```
y = z - H × x̂⁻          (innovation: how wrong were we?)
S = H × P⁻ × Hᵀ + R     (innovation covariance)
K = P⁻ × Hᵀ × S⁻¹       (Kalman gain: how much to trust measurement)
x̂⁺ = x̂⁻ + K × y        (corrected state)
P⁺ = (I - K × H) × P⁻   (corrected uncertainty)
```

### Matrices

| Matrix | Size | Role |
|--------|------|------|
| F (state transition) | 4×4 | Near-identity (slow dynamics) |
| H (observation) | 2×4 | Maps state to measurements |
| Q (process noise) | 4×4 | How much state changes between ticks |
| R (measurement noise) | 2×2 | How noisy the sensor is |
| K (Kalman gain) | 4×2 | Optimal weighting of prediction vs. measurement |
| P (covariance) | 4×4 | Uncertainty in state estimate |

### Why Kalman Filter?

The Kalman filter is the **mathematically optimal** way to combine noisy measurements with a model prediction. It is used in:
- GPS navigation
- Spacecraft attitude determination
- Aircraft autopilot systems
- Financial trading algorithms

For our digital twin, it provides:
- Best estimate of true O₂ (better than raw sensor reading)
- Confidence intervals on that estimate
- Tracking of hidden states (drift, sensitivity) that can't be measured directly

---

## 16. Model 9 — Health Index (Composite Score)

**File:** `app/models/health.py`

### What Does It Do?

Combines all degradation indicators into a single 0-100 score. A pilot or maintenance engineer just needs to check one number.

### Health Formula

```
H = (w₁ × drift_health + w₂ × noise_health + w₃ × fault_health
   + w₄ × sensitivity_health + w₅ × age_health) × 100
```

### Weights & Normalization

| Component | Weight | Normalization | Meaning |
|-----------|--------|---------------|---------|
| Drift health | 0.25 | 1 - \|drift\| / 3.0 | How much has calibration shifted? |
| Noise health | 0.15 | 1 - noise_rms / 0.5 | How noisy is the signal? |
| Fault health | 0.25 | 1 - fault_probability | Is a fault developing? |
| Sensitivity health | 0.20 | sensitivity (0-1) | Can the sensor still respond to O₂ changes? |
| Age health | 0.15 | 1 - aging_factor | How old is the sensor? |

### Health Categories

| Score | Category | Action |
|-------|----------|--------|
| 95-100 | Excellent | No action needed |
| 85-95 | Good | Normal operation |
| 70-85 | Fair | Monitor closely |
| 50-70 | Poor | Schedule maintenance |
| 0-50 | Critical | **Replace immediately** |

### Degradation Rate

```
slope = linear_regression(health_history)
```

Tracks how fast health is declining. Rapid degradation triggers earlier warnings.

### Why Weighted Average?

Each degradation mechanism has different impact on sensor reliability. Fault probability and drift are weighted highest (0.25 each) because they directly affect measurement accuracy. Noise is weighted lowest (0.15) because moderate noise can be filtered out. These weights can be tuned based on field data.

---

## 17. Model 10 — Remaining Useful Life (RUL)

**File:** `app/models/rul.py`

### What Does It Do?

Predicts **how many hours** until the sensor needs replacement.

### Deterministic RUL

Fits an exponential decay to health history:

```
H(t) = H₀ × exp(-k × t)
```

Then solves for time when health reaches threshold (60%):

```
RUL = -ln(threshold / H_current) / k
```

### Monte Carlo RUL (Confidence Intervals)

Because `k` (degradation rate) is uncertain, we sample it from a distribution and compute RUL for each sample:

```python
for i in range(100):
    k_sample = Normal(k_mean, k_std)
    RUL_sample = -ln(60 / H_current) / k_sample
    
RUL_mean = mean(all_samples)
RUL_95_lower = percentile(all_samples, 2.5)
RUL_95_upper = percentile(all_samples, 97.5)
```

This gives us: "The sensor has approximately 850 ± 120 hours of life remaining (95% confidence)."

### Curve Fitting

Uses `scipy.optimize.curve_fit` to fit the exponential decay model to historical health data. R² tells us how well the model fits.

### Why Exponential Decay?

Sensor degradation follows exponential decay because:
1. Arrhenius degradation is exponential
2. Electrode sintering follows parabolic-then-exponential growth
3. Fatigue damage accumulates exponentially near end of life

This is consistent with published degradation models for YSZ oxygen sensors (see Solid State Ionics literature).

### Why Monte Carlo?

Deterministic RUL gives one number. But maintenance decisions need confidence. "Replace in 850 hours" vs. "Replace in 730-970 hours with 95% confidence" — the latter is far more useful for scheduling.

---

## 18. Model 11 — Prediction Model (AI Forecasting)

**File:** `app/models/prediction.py`

### What Does It Do?

Forecasts future values of O₂, temperature, and health score using an ensemble of statistical methods.

### Methods Used

#### 1. Exponential Moving Average (EMA)
```
EMA(t) = α × x(t) + (1-α) × EMA(t-1)
```
α = 0.3. Gives more weight to recent values. Simple but robust for steady-state prediction.

#### 2. Linear Regression
```
y = mx + b
```
Uses `sklearn.linear_model.LinearRegression` to fit a straight line through recent data and extrapolate forward. Best for capturing steady trends.

#### 3. Polynomial Regression (degree 2)
```
y = a₀ + a₁×t + a₂×t²
```
Uses `sklearn.preprocessing.PolynomialFeatures` + `LinearRegression`. Captures acceleration/deceleration in trends (e.g., health declining faster over time).

#### 4. Ensemble Average
```
prediction = mean(linear, polynomial, EMA)
confidence_band = ±2 × std(linear, polynomial, EMA)
```

### Why Ensemble Instead of Deep Learning?

1. **No training data needed**: Statistical methods work out of the box with just time-series history
2. **Interpretable**: You can see exactly why the prediction is what it is
3. **Lightweight**: No 2GB PyTorch dependency in the .exe
4. **Sufficient accuracy**: For trend prediction in slowly varying systems, ensembles match LSTM performance
5. **Upgrade path**: Can replace with LSTM later without changing the API

---

## 19. Services Layer

### Simulator (`app/services/simulator.py`)

Generates synthetic sensor data with:

- **Flight profiles**: Ground → Climb → Cruise → Descent → Ground (repeating cycle)
  - Ground: 60 ticks, sea level
  - Climb: 120 ticks, altitude increases to 35,000 ft
  - Cruise: 600 ticks, stable at 35,000 ft with turbulence noise
  - Descent: 120 ticks, altitude decreases
- **Aging**: Sensor gradually degrades (voltage drops, noise increases, drift accumulates)
- **Time acceleration**: 1 real second = 10 simulated flight hours (configurable)
- **Fault injection**: Manually inject any of 5 fault types via the API

### Calculations Pipeline (`app/services/calculations.py`)

Orchestrates all 11 models in sequence for every sensor reading. Maintains rolling history for trend-dependent models. Runs prediction every 10th tick to save CPU.

### Alert Engine (`app/services/alerts.py`)

| Condition | Alert Type | Severity |
|-----------|-----------|----------|
| Health < 50% | health_critical | 🔴 Critical |
| Health < 75% | health_warning | 🟡 Warning |
| Drift > 3% | drift_critical | 🔴 Critical |
| Drift > 1.5% | drift_warning | 🟡 Warning |
| RUL < 100 hrs | rul_critical | 🔴 Critical |
| RUL < 500 hrs | rul_warning | 🟡 Warning |
| O₂ < 85% | oxygen_low | 🔴 Critical |
| Fault prob > 70% | fault_critical | 🔴 Critical |
| Heater < 600°C | heater_low | 🔴 Critical |

De-duplication: Same alert type won't repeat within 5 minutes.

---

## 20. Frontend Dashboard

### Technology

- **HTML5** + **CSS3** + **Vanilla JavaScript**
- **Chart.js** (CDN) for real-time time-series charts
- **Google Fonts** (Inter for UI, JetBrains Mono for numbers)

### Design

- Dark theme with glassmorphism cards
- Gradient text for key metrics
- SVG health ring gauge with color transitions
- Real-time updates every 1 second via `fetch()` API
- 6 time-series charts (O₂, temperature, health, voltage/current, drift, pressure/flow)
- Flight phase indicator (Ground → Climb → Cruise → Descent)
- Alert feed with severity-colored cards
- Fault injection buttons for testing
- Responsive layout (desktop + mobile)

### Pages

1. **Dashboard** (`/`) — Main overview with all metrics, charts, health ring, RUL, alerts
2. **Sensor Detail** (`/sensor-detail`) — Full telemetry table with extended charts

---

## 21. Configuration Reference

All constants are in `app/config.py`. Key settings:

### Physical Constants

| Constant | Value | Used In |
|----------|-------|---------|
| R_GAS | 8.314 J/(mol·K) | Nernst equation |
| FARADAY | 96,485 C/mol | Nernst equation |
| BOLTZMANN | 1.381×10⁻²³ J/K | Arrhenius, impedance |
| STEFAN_BOLTZMANN | 5.67×10⁻⁸ W/(m²·K⁴) | Thermal radiation |

### Simulation Settings

| Setting | Value | Meaning |
|---------|-------|---------|
| SIMULATION_INTERVAL | 1.0 s | Time between readings |
| SIMULATION_TIME_ACCELERATION | 10 | 1 real second = 10 simulated hours |
| SENSOR_MAX_HOURS | 5,000 | Maximum rated sensor life |
| RUL_HEALTH_THRESHOLD | 60% | Replace sensor below this health |

### Alert Thresholds

| Threshold | Value | Triggers |
|-----------|-------|----------|
| ALERT_HEALTH_WARNING | 75% | Warning alert |
| ALERT_HEALTH_CRITICAL | 50% | Critical alert |
| ALERT_DRIFT_WARNING | 1.5% | Warning alert |
| ALERT_DRIFT_CRITICAL | 3.0% | Critical alert |
| ALERT_RUL_WARNING | 500 hrs | Warning alert |
| ALERT_RUL_CRITICAL | 100 hrs | Critical alert |
| ALERT_OXYGEN_LOW | 85% | Critical alert |

---

## 22. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI | Async, fast, auto-docs at /docs, modern Python |
| Database | SQLite (aiosqlite) | Zero config, embedded, perfect for single-user app |
| Frontend | HTML + CSS + JS | Simple, no build step, easy to understand and modify |
| Charts | Chart.js 4.4 (CDN) | Lightweight, beautiful charts, no npm needed |
| Physics | NumPy + SciPy | Industry standard for numerical computing |
| ML | scikit-learn | Lightweight, no GPU needed, great for ensemble methods |
| Packaging | PyInstaller | Creates standalone .exe, no Python needed on target |
| Python | 3.10+ | Modern async support, type hints |

### Why NOT React?

At this stage, React adds complexity without benefit:
- Extra build step (webpack/vite)
- Node.js dependency
- Harder to package into .exe
- The frontend only needs: show values, display charts, show alerts
- Plain HTML does all of this with zero overhead
- Can always upgrade to React later — the REST API stays the same

---

## Quick Reference: Running Commands

```bash
# Start development server (with auto-reload)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Start production server
python launcher.py

# Build Windows .exe (run on Windows)
python build.py

# View API documentation
# Open: http://127.0.0.1:8000/docs

# Inject a fault via curl
curl -X POST "http://127.0.0.1:8000/api/sensor/fault?fault_type=heater_failure&severity=0.5"

# Clear all faults
curl -X POST "http://127.0.0.1:8000/api/sensor/clear-faults"

# Get live sensor data
curl http://127.0.0.1:8000/api/sensor/live

# Get dashboard summary
curl http://127.0.0.1:8000/api/dashboard/summary
```
