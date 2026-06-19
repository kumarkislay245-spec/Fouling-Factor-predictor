import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import time

st.set_page_config(
    page_title="Digital Twin | Heat Exchanger Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Root Palette ── */
:root {
    --bg-base:       #0d0f14;
    --bg-panel:      #13161e;
    --bg-card:       #1a1e28;
    --bg-hover:      #1f2435;
    --accent-blue:   #3b82f6;
    --accent-teal:   #14b8a6;
    --accent-amber:  #f59e0b;
    --accent-red:    #ef4444;
    --accent-green:  #22c55e;
    --text-primary:  #e2e8f0;
    --text-muted:    #64748b;
    --text-dim:      #334155;
    --border:        rgba(255,255,255,0.07);
    --border-strong: rgba(255,255,255,0.14);
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem; max-width: 100%; }

/* ── App Background ── */
.stApp { background-color: var(--bg-base); }

/* ── Top header bar ── */
.dash-header {
    display: flex; align-items: center; gap: 14px;
    padding: 0.75rem 0 1.25rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.dash-header .logo {
    width: 40px; height: 40px; border-radius: 10px;
    background: #1e3a5f;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}
.dash-title { font-size: 18px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em; }
.dash-subtitle { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.status-pill {
    margin-left: auto;
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 500;
}
.status-live {
    background: rgba(34,197,94,0.1);
    color: #22c55e;
    border: 1px solid rgba(34,197,94,0.25);
}
.status-live::before {
    content: "";
    width: 6px; height: 6px; border-radius: 50%;
    background: #22c55e;
    animation: pulse 1.5s ease-in-out infinite;
    display: inline-block;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

/* ── KPI Cards ── */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: "";
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-blue::before  { background: var(--accent-blue); }
.kpi-teal::before  { background: var(--accent-teal); }
.kpi-amber::before { background: var(--accent-amber); }
.kpi-red::before   { background: var(--accent-red); }
.kpi-green::before { background: var(--accent-green); }

.kpi-label { font-size: 11px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
.kpi-value { font-size: 26px; font-weight: 700; color: var(--text-primary); line-height: 1.2; margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.kpi-unit  { font-size: 12px; color: var(--text-muted); }
.kpi-badge {
    display: inline-flex; align-items: center; gap: 4px;
    margin-top: 6px; padding: 2px 8px;
    border-radius: 4px; font-size: 11px; font-weight: 500;
}
.badge-ok      { background: rgba(34,197,94,0.1);  color: #22c55e; }
.badge-warn    { background: rgba(245,158,11,0.1); color: #f59e0b; }
.badge-crit    { background: rgba(239,68,68,0.1);  color: #ef4444; }

/* ── Section titles ── */
.section-label {
    font-size: 11px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 1.5rem 0 0.75rem;
    display: flex; align-items: center; gap: 8px;
}
.section-label::after {
    content: ""; flex: 1; height: 1px;
    background: var(--border);
}

/* ── Alert Banner ── */
.alert-banner {
    border-radius: 10px; padding: 0.75rem 1rem;
    font-size: 13px; font-weight: 500;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 1rem; border: 1px solid;
}
.alert-ok   { background: rgba(34,197,94,0.08);  color: #22c55e; border-color: rgba(34,197,94,0.2); }
.alert-warn { background: rgba(245,158,11,0.08); color: #f59e0b; border-color: rgba(245,158,11,0.2); }
.alert-crit { background: rgba(239,68,68,0.08);  color: #ef4444; border-color: rgba(239,68,68,0.2); }

/* ── Chart containers ── */
.chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.25rem 0.5rem;
    margin-bottom: 1rem;
}
.chart-title { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown h3 { color: var(--text-primary) !important; }

/* ── Streamlit metric override for dark theme ── */
[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-size: 22px !important; }
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 12px !important; }

/* ── Streamlit chart label color ── */
.stVegaLiteChart, .stLineChart { filter: brightness(1.1); }

/* ── Process flow diagram ── */
.pfd-row {
    display: flex; align-items: center; gap: 0;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    overflow-x: auto;
}
.pfd-node {
    text-align: center;
    min-width: 80px;
}
.pfd-box {
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px; font-weight: 600;
    color: var(--text-primary);
    background: var(--bg-hover);
    white-space: nowrap;
}
.pfd-val { font-size: 10px; color: var(--text-muted); margin-top: 3px; }
.pfd-arrow {
    flex: 1; text-align: center;
    color: var(--text-dim); font-size: 18px;
    min-width: 30px;
}

/* ── Efficiency bar ── */
.eff-bar-track {
    height: 8px; border-radius: 4px;
    background: var(--bg-hover);
    margin: 6px 0;
    overflow: hidden;
}
.eff-bar-fill {
    height: 100%; border-radius: 4px;
    transition: width 0.4s ease;
}

/* ── Sidebar design basis table ── */
.design-table { width: 100%; font-size: 12px; border-collapse: collapse; }
.design-table td { padding: 5px 0; color: var(--text-muted); border-bottom: 1px solid var(--border); }
.design-table td:last-child { text-align: right; color: var(--text-primary); font-weight: 500; }

/* ── Streamlit overrides ── */
.stCheckbox label, .stRadio label { color: var(--text-muted) !important; font-size: 13px !important; }
.stButton button {
    background: var(--bg-hover) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)



BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'fouling_sensor_model (2).pkl')

# Design basis
T_HOT_IN   = 353.0   # K  – hot stream inlet
T_COLD_IN  = 300.0   # K  – cold stream inlet
AREA       = 15.0    # m² – shell & tube exchanger area
M_HOT      = 2.5     # kg/s
CP_HOT     = 4184.0  # J/kg·K  (water)
U_CLEAN    = 850.0   # W/m²·K  – clean design U (baseline)

RF_WARN    = 0.0005
RF_CRIT    = 0.0010


@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)

model = load_model()


def _init_state():
    if 'sim_step' not in st.session_state:
        st.session_state.sim_step = 0
    if 'history' not in st.session_state:
        _cols = ['Timestamp', 'T3', 'T4', 'U', 'Efficiency', 'Rf', 'LMTD', 'Q_load']
        st.session_state.history = pd.DataFrame(columns=_cols)
    if 'alarm_count' not in st.session_state:
        st.session_state.alarm_count = 0

_init_state()


def simulate_temperatures(step: int):
    """Simulate gradual fouling degradation over time."""
    t3_base = 320.0   # hot outlet – design
    t4_base = 310.0   # cold outlet – design

    # Fouling causes hot outlet to rise (less heat transfer), cold to drop
    fouling_factor = 1 - np.exp(-step / 200)   # asymptotic degradation curve
    t3 = t3_base + fouling_factor * 18.0 + np.random.normal(0, 0.25)
    t4 = t4_base - fouling_factor * 12.0 + np.random.normal(0, 0.25)

    # Hard physical limits
    t3 = float(np.clip(t3, T_COLD_IN + 5, T_HOT_IN - 1))
    t4 = float(np.clip(t4, T_COLD_IN + 1, T_HOT_IN - 5))
    return t3, t4


def calc_lmtd(T_hi, T_ho, T_ci, T_co):
    """Counter-flow LMTD with safe guard for equal-temperature ends."""
    dT1 = T_hi - T_co   # hot in – cold out
    dT2 = T_ho - T_ci   # hot out – cold in
    if dT1 <= 0 or dT2 <= 0:
        return abs(dT1 + dT2) / 2 + 0.01
    if abs(dT1 - dT2) < 0.001:
        return dT1
    return (dT1 - dT2) / np.log(dT1 / dT2)


def calc_thermals(t3: float, t4: float):
    """Return Q, LMTD, U, efficiency, NTU, Rf."""
    Q = M_HOT * CP_HOT * (T_HOT_IN - t3)          # W – actual heat duty
    lmtd = calc_lmtd(T_HOT_IN, t3, T_COLD_IN, t4)
    U = max(50.0, Q / (AREA * lmtd)) if lmtd > 0 else 50.0
    U = min(U, 1500.0)

    # Fouling resistance from Wilson Plot relationship: 1/U = 1/U_clean + Rf
    Rf = max(0.0, 1/U - 1/U_CLEAN)

    # Thermal effectiveness (NTU method – counterflow)
    eff = (T_HOT_IN - t3) / (T_HOT_IN - T_COLD_IN) * 100
    eff = float(np.clip(eff, 2.0, 100.0))

    return Q, lmtd, U, eff, Rf


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem;">
        <div style="font-size:15px; font-weight:600; color:#e2e8f0;">⚙ Control Panel</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">Shell & Tube | Single Pass</div>
    </div>
    """, unsafe_allow_html=True)

    run_live = st.checkbox("▶  Live DCS Stream", value=True)
    refresh_rate = st.select_slider(
        "Refresh interval (s)", options=[1, 2, 3, 5, 10], value=2
    )

    st.markdown("---")

    if st.button("↺  Reset Baseline"):
        st.session_state.sim_step = 0
        st.session_state.alarm_count = 0
        _cols = ['Timestamp', 'T3', 'T4', 'U', 'Efficiency', 'Rf', 'LMTD', 'Q_load']
        st.session_state.history = pd.DataFrame(columns=_cols)
        st.rerun()

    st.markdown("<div class='section-label'>Design Basis</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <table class='design-table'>
        <tr><td>Hot inlet T₁</td><td>{T_HOT_IN} K</td></tr>
        <tr><td>Cold inlet T₂</td><td>{T_COLD_IN} K</td></tr>
        <tr><td>Area A</td><td>{AREA} m²</td></tr>
        <tr><td>Mass flow ṁ</td><td>{M_HOT} kg/s</td></tr>
        <tr><td>Cₚ (hot)</td><td>4 184 J/kg·K</td></tr>
        <tr><td>U (clean)</td><td>{U_CLEAN:.0f} W/m²·K</td></tr>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Alarm Thresholds</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <table class='design-table'>
        <tr><td>Rf Warning</td><td>≥ {RF_WARN:.4f} m²K/W</td></tr>
        <tr><td>Rf Critical</td><td>≥ {RF_CRIT:.4f} m²K/W</td></tr>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if model:
        st.markdown("""
        <div style='font-size:11px; font-weight:600; color:#22c55e; letter-spacing:0.06em; text-transform:uppercase;'>
        ● ML Engine Active
        </div>
        <div style='font-size:10px; color:#64748b; margin-top:3px;'>Predictive fouling soft-sensor</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='font-size:11px; font-weight:600; color:#ef4444; letter-spacing:0.06em; text-transform:uppercase;'>
        ✕ Model Not Found
        </div>
        <div style='font-size:10px; color:#64748b; margin-top:3px;'>Using physics-based Rf only</div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:10px; color:#334155; margin-top:1rem;'>
        Total cycles: {st.session_state.sim_step}<br>
        Alarms fired: {st.session_state.alarm_count}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
status_class = "status-live" if run_live else "status-pill"
status_text  = "LIVE" if run_live else "PAUSED"

st.markdown(f"""
<div class="dash-header">
    <div class="logo">🏭</div>
    <div>
        <div class="dash-title">Industrial Heat Exchanger — Digital Twin</div>
        <div class="dash-subtitle">Real-time fouling detection &nbsp;·&nbsp; Thermal performance monitoring &nbsp;·&nbsp; ML soft-sensor</div>
    </div>
    <div class="status-pill {status_class}">{status_text}</div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# SIMULATION STEP
# ──────────────────────────────────────────────────────────────────────────────
if run_live:
    st.session_state.sim_step += 1

step = st.session_state.sim_step
t3, t4 = simulate_temperatures(step)
Q_load, lmtd, U, eff, Rf_physics = calc_thermals(t3, t4)

# ML prediction (if model exists); else fall back to physics-based Rf
if model:
    try:
        features = np.array([[t3, t4, abs(t3 - t4)]])
        Rf = float(model.predict(features)[0])
        Rf = max(0.0, Rf)
    except Exception:
        Rf = Rf_physics
else:
    Rf = Rf_physics

# Alarm logic
if Rf >= RF_CRIT:
    alarm_level = "CRITICAL"
    st.session_state.alarm_count += 1
elif Rf >= RF_WARN:
    alarm_level = "WARNING"
else:
    alarm_level = "OK"


# ──────────────────────────────────────────────────────────────────────────────
# PROCESS FLOW DIAGRAM  (top strip)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""<div class='section-label'>Process Stream Overview</div>""", unsafe_allow_html=True)
st.markdown(f"""
<div class="pfd-row">
    <div class="pfd-node">
        <div class="pfd-box" style="border-color:#3b82f6; color:#93c5fd;">HOT IN</div>
        <div class="pfd-val">T₁ = {T_HOT_IN:.0f} K</div>
    </div>
    <div class="pfd-arrow">→</div>
    <div class="pfd-node">
        <div class="pfd-box" style="border-color:#6366f1; color:#a5b4fc;">SHELL SIDE</div>
        <div class="pfd-val">ṁ = {M_HOT} kg/s</div>
    </div>
    <div class="pfd-arrow">→</div>
    <div class="pfd-node">
        <div class="pfd-box" style="border-color:#f59e0b; color:#fcd34d;">HOT OUT</div>
        <div class="pfd-val">T₃ = {t3:.1f} K</div>
    </div>
    <div class="pfd-arrow" style="min-width:60px; color:#334155;">|</div>
    <div class="pfd-node">
        <div class="pfd-box" style="border-color:#14b8a6; color:#5eead4;">COLD IN</div>
        <div class="pfd-val">T₂ = {T_COLD_IN:.0f} K</div>
    </div>
    <div class="pfd-arrow">→</div>
    <div class="pfd-node">
        <div class="pfd-box" style="border-color:#22c55e; color:#86efac;">TUBE SIDE</div>
        <div class="pfd-val">A = {AREA} m²</div>
    </div>
    <div class="pfd-arrow">→</div>
    <div class="pfd-node">
        <div class="pfd-box" style="border-color:#22c55e; color:#86efac;">COLD OUT</div>
        <div class="pfd-val">T₄ = {t4:.1f} K</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# ALARM BANNER
# ──────────────────────────────────────────────────────────────────────────────
if alarm_level == "CRITICAL":
    st.markdown(f"""
    <div class="alert-banner alert-crit">
        🚨 <strong>CRITICAL FOULING ALARM</strong> — Rₓ = {Rf:.6f} m²·K/W  |  Exchanger efficiency below threshold.
        Immediate inspection of tube bundles recommended. Schedule shutdown for CIP.
    </div>
    """, unsafe_allow_html=True)
elif alarm_level == "WARNING":
    st.markdown(f"""
    <div class="alert-banner alert-warn">
        ⚠ <strong>FOULING WARNING</strong> — Rₓ = {Rf:.6f} m²·K/W  |  Scaling layer accumulating on tube surfaces.
        Increase monitoring frequency and review water treatment.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="alert-banner alert-ok">
        ✓ <strong>NORMAL OPERATION</strong> — All parameters within design envelope.
        Heat exchanger operating at {eff:.1f}% thermal efficiency.
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# KPI CARDS ROW
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""<div class='section-label'>Live Telemetry</div>""", unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)

# Fouling badge
rf_badge_cls  = "badge-crit" if alarm_level == "CRITICAL" else ("badge-warn" if alarm_level == "WARNING" else "badge-ok")
rf_badge_text = alarm_level

# U degradation vs clean
u_pct = (U / U_CLEAN) * 100
u_badge_cls  = "badge-ok" if u_pct > 80 else ("badge-warn" if u_pct > 60 else "badge-crit")

# Efficiency badge
eff_badge_cls = "badge-ok" if eff > 75 else ("badge-warn" if eff > 55 else "badge-crit")

# Q load in kW
Q_kw = Q_load / 1000

with k1:
    st.markdown(f"""
    <div class="kpi-card kpi-blue">
        <div class="kpi-label">Hot Outlet T₃</div>
        <div class="kpi-value">{t3:.1f}</div>
        <div class="kpi-unit">Kelvin</div>
        <div class="kpi-badge badge-ok">↑ {t3 - 330:.1f} K from design</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card kpi-teal">
        <div class="kpi-label">Cold Outlet T₄</div>
        <div class="kpi-value">{t4:.1f}</div>
        <div class="kpi-unit">Kelvin</div>
        <div class="kpi-badge badge-ok">↓ {320 - t4:.1f} K from design</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card kpi-blue">
        <div class="kpi-label">Heat Duty Q</div>
        <div class="kpi-value">{Q_kw:.1f}</div>
        <div class="kpi-unit">kW</div>
        <div class="kpi-badge badge-ok">LMTD = {lmtd:.1f} K</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card kpi-amber">
        <div class="kpi-label">Overall U</div>
        <div class="kpi-value">{U:.0f}</div>
        <div class="kpi-unit">W/m²·K</div>
        <div class="kpi-badge {u_badge_cls}">{u_pct:.0f}% of clean U</div>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card kpi-teal">
        <div class="kpi-label">Thermal Efficiency η</div>
        <div class="kpi-value">{eff:.1f}</div>
        <div class="kpi-unit">%</div>
        <div class="kpi-badge {eff_badge_cls}">{eff_badge_cls.replace('badge-','').upper()}</div>
    </div>""", unsafe_allow_html=True)

with k6:
    st.markdown(f"""
    <div class="kpi-card kpi-red">
        <div class="kpi-label">Fouling Factor Rₓ</div>
        <div class="kpi-value">{Rf * 1e4:.2f}</div>
        <div class="kpi-unit">× 10⁻⁴ m²·K/W</div>
        <div class="kpi-badge {rf_badge_cls}">{rf_badge_text}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# HISTORY UPDATE
# ──────────────────────────────────────────────────────────────────────────────
timestamp = pd.Timestamp.now().strftime('%H:%M:%S')
new_row = pd.DataFrame([{
    'Timestamp': timestamp,
    'T3': round(t3, 2),
    'T4': round(t4, 2),
    'U':  round(U, 1),
    'Efficiency': round(eff, 2),
    'Rf': round(Rf, 8),
    'LMTD': round(lmtd, 2),
    'Q_load': round(Q_kw, 2),
}])

history = pd.concat([st.session_state.history, new_row]).tail(60)
st.session_state.history = history


# ──────────────────────────────────────────────────────────────────────────────
# CHARTS  (2 columns)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""<div class='section-label'>Trend Analytics</div>""", unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1])

if len(history) > 1:
    hist_idx = history.set_index('Timestamp')

    with left_col:
        st.markdown('<div class="chart-card"><div class="chart-title">Overall Heat Transfer Coefficient U (W/m²·K)</div>', unsafe_allow_html=True)
        st.line_chart(hist_idx[['U']], color=["#3b82f6"], height=180)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="chart-card"><div class="chart-title">Thermal Efficiency η (%)</div>', unsafe_allow_html=True)
        st.line_chart(hist_idx[['Efficiency']], color=["#14b8a6"], height=180)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="chart-card"><div class="chart-title">Fouling Factor Rₓ (m²·K/W) — ML Prediction</div>', unsafe_allow_html=True)
        st.line_chart(hist_idx[['Rf']], color=["#ef4444"], height=180)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="chart-card"><div class="chart-title">Outlet Temperatures T₃ / T₄ (K)</div>', unsafe_allow_html=True)
        st.line_chart(hist_idx[['T3', 'T4']], color=["#f59e0b", "#22c55e"], height=180)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Collecting data… trend charts appear after a few cycles.")


# ──────────────────────────────────────────────────────────────────────────────
# DETAILED DATA TABLE (expandable)
# ──────────────────────────────────────────────────────────────────────────────
with st.expander("📋 Raw Historian Log (last 60 samples)"):
    if len(history) > 0:
        display_hist = history.copy()
        display_hist.columns = ['Time', 'T₃ (K)', 'T₄ (K)', 'U (W/m²K)', 'η (%)', 'Rf (m²K/W)', 'LMTD (K)', 'Q (kW)']
        st.dataframe(display_hist.style.format({
            'T₃ (K)': '{:.2f}', 'T₄ (K)': '{:.2f}',
            'U (W/m²K)': '{:.1f}', 'η (%)': '{:.1f}',
            'Rf (m²K/W)': '{:.8f}', 'LMTD (K)': '{:.2f}', 'Q (kW)': '{:.1f}'
        }), use_container_width=True, height=300)
    else:
        st.caption("No data yet.")


# ──────────────────────────────────────────────────────────────────────────────
# ENGINEERING SUMMARY ROW
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""<div class='section-label'>Engineering Diagnostics</div>""", unsafe_allow_html=True)
diag_c1, diag_c2, diag_c3 = st.columns(3)

with diag_c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Log-Mean Temperature Difference</div>
        <div class="kpi-value" style="font-size:20px;">{lmtd:.2f} K</div>
        <div class="kpi-unit">Counter-flow LMTD</div>
        <div style="margin-top:8px; font-size:11px; color:#64748b;">
            ΔT₁ = {T_HOT_IN - t4:.1f} K &nbsp;|&nbsp; ΔT₂ = {t3 - T_COLD_IN:.1f} K
        </div>
    </div>""", unsafe_allow_html=True)

with diag_c2:
    cleaning_pct = min(100, (Rf / RF_CRIT) * 100)
    bar_color = "#22c55e" if cleaning_pct < 50 else ("#f59e0b" if cleaning_pct < 100 else "#ef4444")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Cleaning Due Index</div>
        <div class="kpi-value" style="font-size:20px;">{cleaning_pct:.0f}%</div>
        <div class="eff-bar-track">
            <div class="eff-bar-fill" style="width:{cleaning_pct:.0f}%; background:{bar_color};"></div>
        </div>
        <div style="font-size:11px; color:#64748b;">
            0% = clean &nbsp;|&nbsp; 100% = shutdown threshold
        </div>
    </div>""", unsafe_allow_html=True)

with diag_c3:
    u_loss = U_CLEAN - U
    u_loss_pct = (u_loss / U_CLEAN) * 100
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">U Degradation from Baseline</div>
        <div class="kpi-value" style="font-size:20px;">−{u_loss:.0f} W/m²·K</div>
        <div class="kpi-unit">{u_loss_pct:.1f}% below clean design</div>
        <div style="margin-top:8px; font-size:11px; color:#64748b;">
            Clean U₀ = {U_CLEAN:.0f} &nbsp;|&nbsp; Current U = {U:.0f} W/m²·K
        </div>
    </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# AUTO REFRESH
# ──────────────────────────────────────────────────────────────────────────────
if run_live:
    time.sleep(refresh_rate)
    st.rerun()
