# 🏭 Real-Time Industrial Heat Exchanger Soft-Sensor (Digital Twin)

> Real-time heat exchanger fouling detector — predicts when to clean, before efficiency drops. Built with Python, Streamlit & ML.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?style=flat-square&logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?style=flat-square&logo=plotly)
![ML](https://img.shields.io/badge/ML-Scikit--Learn-orange?style=flat-square&logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What is this?

In industrial plants, heat exchangers gradually accumulate fouling (scaling/deposits) on their tube surfaces over time. This reduces heat transfer efficiency, wastes energy, and increases operating costs — but cleaning too early or too late is equally wasteful.

This project solves that by building a **machine learning soft-sensor** that reads live DCS (Distributed Control System) sensor data and predicts the **fouling factor Rᶠ** in real time — giving plant operators an early warning before efficiency drops.

---

## Features

- **Real-time Rᶠ prediction** from live DCS telemetry (T₃, T₄, ΔT)
- **Color-coded trend chart** — line turns amber in warning zone, red in alarm zone
- **Three-tier alarm system** — Stable → Warning → Emergency
- **Digital twin architecture** — ML model mirrors the physical exchanger
- **Predictive maintenance** — schedule cleaning at the right time, not too early or too late
- Live Streamlit dashboard with Plotly chart

---

## How it works

```
DCS Simulator (.py)
       │
       ▼
live_plant_data.csv   ←── writes every 2 seconds
       │
       ▼
ML Soft-Sensor Model (.pkl)
       │
       ▼  predict(T3, T4, ΔT) → Rᶠ
       │
       ▼
Streamlit Dashboard
  ├── Live sensor metrics
  ├── Rᶠ trend chart (color changes by zone)
  └── Alarm banner (Stable / Warning / Emergency)
```

---

## Alarm Thresholds

| Status | Rᶠ Value | Chart Color | Action |
|--------|----------|-------------|--------|
| 🟢 Stable | < 0.0005 | Blue | No action needed |
| ⚠️ Warning | ≥ 0.0005 | Amber | Plan cleaning soon |
| 🚨 Emergency | ≥ 0.0010 | Red | Trigger cleaning cycle immediately |

---

## Project Structure

```
├── app.py                        # Streamlit dashboard (main entry point)
├── dcs_simulator.py              # DCS loop — simulates live plant sensor data
├── fouling_sensor_model (2).pkl  # Trained ML soft-sensor model
├── requirements.txt              # Python dependencies
└── README.md
```

---

## Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/your-username/heat-exchanger-fouling-monitor.git
cd heat-exchanger-fouling-monitor
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the DCS simulator** (in one terminal)
```bash
python dcs_simulator.py
```

**4. Launch the dashboard** (in another terminal)
```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## Requirements

```
streamlit
pandas
numpy
scikit-learn
plotly
```

---

## Live Demo

> Deployed on Streamlit Community Cloud
> 🔗 [your-app-link.streamlit.app](https://your-app-link.streamlit.app)

---

## Why this matters

Fouling in heat exchangers costs the global process industry an estimated **$4.5 billion per year** in energy waste and unplanned shutdowns. Early detection through predictive soft-sensors like this one can reduce that cost significantly — this project demonstrates how ML can be applied directly to industrial process data to solve a real operational problem.

---

## Author

Built by **[Kislay Kumar]**
B.Tech Chemical Engineering | ML + Process Control Enthusiast
[LinkedIn](https://linkedin.com/in/your-profile) · [GitHub](https://github.com/your-username)

---

## License

MIT License — free to use, modify, and deploy.
