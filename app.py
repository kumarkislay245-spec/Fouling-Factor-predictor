import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import time
import threading
import plotly.graph_objects as go

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
model_path     = os.path.join(BASE_DIR, 'fouling_sensor_model (2).pkl')
live_data_path = os.path.join(BASE_DIR, 'live_plant_data.csv')

RF_WARN  = 0.0005
RF_ALARM = 0.0010

# ── DCS Simulator (runs in background thread) ─────────────────────────────────
def run_dcs_simulator():
    """
    Exact same logic as your dcs .py — runs inside a daemon thread.
    No __file__, no importlib, no path issues.
    """
    # initialise CSV with headers
    df_init = pd.DataFrame(columns=[
        'Hot_Fluid_Outlet_Temperature_T3_K',
        'Cold_Fluid_Outlet_Temperature_T4_K'
    ])
    df_init.to_csv(live_data_path, index=False)

    base_t3 = 320.0
    base_t4 = 310.0

    for i in range(500):
        simulated_t3 = base_t3 + (i * 0.08) + np.random.normal(0, 0.2)
        simulated_t4 = base_t4 - (i * 0.04) + np.random.normal(0, 0.2)

        new_data = pd.DataFrame({
            'Hot_Fluid_Outlet_Temperature_T3_K': [simulated_t3],
            'Cold_Fluid_Outlet_Temperature_T4_K': [simulated_t4]
        })
        new_data.to_csv(live_data_path, mode='a', header=False, index=False)
        time.sleep(2)

# Start DCS thread only once per session
if 'dcs_started' not in st.session_state:
    t = threading.Thread(target=run_dcs_simulator, daemon=True)
    t.start()
    st.session_state['dcs_started'] = True

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Real-Time Fouling Monitor", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
    .stMetric label  { font-size: 0.78rem !important; color: #8b949e !important; }
    .stMetric [data-testid="metric-container"] > div:first-child { font-size: 0.78rem; }
</style>
""", unsafe_allow_html=True)

st.title("🏭 Real-Time Industrial Exchanger Soft-Sensor (Digital Twin)")
st.markdown("---")

# ── Model loader ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_pickle_model():
    with open(model_path, 'rb') as f:
        return pickle.load(f)

try:
    model = load_pickle_model()
    st.sidebar.success("🟢 ML Soft-Sensor Engine: ACTIVE")
    st.sidebar.info("Loaded: fouling_sensor_model (2).pkl")
except Exception as e:
    model = None
    st.sidebar.error("❌ Model File Not Found!")
    st.sidebar.write(f"Expected location: `{BASE_DIR}`")
    st.sidebar.write(f"Error: {e}")

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
run_monitoring = st.sidebar.checkbox("Start Live DCS Data Stream", value=True)
st.sidebar.markdown("**Alarm thresholds**")
st.sidebar.markdown(f"- ⚠️ Warning : `Rf ≥ {RF_WARN}`")
st.sidebar.markdown(f"- 🚨 Alarm   : `Rf ≥ {RF_ALARM}`")

# ── Layout ────────────────────────────────────────────────────────────────────
st.subheader("Live Plant Telemetry & Diagnostic Streams")
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Current Sensor States")
    t3_metric      = st.empty()
    t4_metric      = st.empty()
    dt_metric      = st.empty()
    fouling_metric = st.empty()
    status_alert   = st.empty()

with col2:
    st.markdown("### Real-Time Fouling Accumulation Trend ($R_f$)")
    chart_placeholder = st.empty()

if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Timestamp', 'Fouling_Factor'])

# ── Chart builder ─────────────────────────────────────────────────────────────
def build_chart(history_df):
    fig = go.Figure()

    if history_df.empty:
        _add_thresholds(fig)
        _style(fig)
        return fig

    times  = history_df['Timestamp'].tolist()
    values = history_df['Fouling_Factor'].tolist()

    def zone(v):
        if v >= RF_ALARM: return 'red'
        if v >= RF_WARN:  return 'amber'
        return 'blue'

    COLORS = {'blue': '#58a6ff', 'amber': '#d29922', 'red': '#f85149'}
    LABELS = {'blue': 'Rf (normal)', 'amber': 'Rf (warning)', 'red': 'Rf (alarm)'}

    segments, cur_color = [], zone(values[0])
    seg_t, seg_v = [times[0]], [values[0]]

    for i in range(1, len(values)):
        c = zone(values[i])
        if c == cur_color:
            seg_t.append(times[i])
            seg_v.append(values[i])
        else:
            segments.append((cur_color, seg_t[:], seg_v[:]))
            cur_color = c
            seg_t = [times[i-1], times[i]]
            seg_v = [values[i-1], values[i]]
    segments.append((cur_color, seg_t, seg_v))

    seen = set()
    for ck, st_, sv in segments:
        fig.add_trace(go.Scatter(
            x=st_, y=sv, mode='lines',
            line=dict(color=COLORS[ck], width=2),
            name=LABELS[ck],
            showlegend=ck not in seen,
            legendgroup=ck,
            hovertemplate='%{x}<br>Rf = %{y:.6f}<extra></extra>',
        ))
        seen.add(ck)

    _add_thresholds(fig)

    y_max = max(max(values) * 1.25, RF_ALARM * 1.3)
    fig.add_hrect(y0=RF_WARN, y1=RF_ALARM,
        fillcolor='rgba(210,153,34,0.07)', line_width=0,
        annotation_text="Warning zone", annotation_position="top left",
        annotation_font=dict(size=10, color='#d29922'))
    fig.add_hrect(y0=RF_ALARM, y1=y_max,
        fillcolor='rgba(248,81,73,0.07)', line_width=0,
        annotation_text="Alarm zone", annotation_position="top left",
        annotation_font=dict(size=10, color='#f85149'))

    _style(fig, y_max)
    return fig

def _add_thresholds(fig):
    fig.add_hline(y=RF_WARN,
        line=dict(color='#d29922', width=1.2, dash='dash'),
        annotation_text=f"Warning {RF_WARN}",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color='#d29922'))
    fig.add_hline(y=RF_ALARM,
        line=dict(color='#f85149', width=1.5),
        annotation_text=f"Alarm {RF_ALARM}",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color='#f85149'))

def _style(fig, y_max=None):
    if y_max is None: y_max = RF_ALARM * 1.4
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=36),
        paper_bgcolor='#0d1117', plot_bgcolor='#0d1117',
        font=dict(color='#8b949e', size=11),
        legend=dict(orientation='h', yanchor='bottom', y=1.02,
                    xanchor='right', x=1, bgcolor='rgba(0,0,0,0)',
                    font=dict(size=11)),
        xaxis=dict(showgrid=False, tickangle=-45,
                   tickfont=dict(size=9), color='#8b949e',
                   nticks=8, linecolor='#21262d'),
        yaxis=dict(gridcolor='rgba(48,54,61,0.6)', gridwidth=0.5,
                   range=[0, y_max], tickfont=dict(size=10),
                   color='#8b949e', linecolor='#21262d',
                   title=dict(text='Rf (m²·K/W)',
                              font=dict(size=11, color='#8b949e')),
                   tickformat='.4f'),
        hovermode='x unified')

# ── Real-time loop ─────────────────────────────────────────────────────────────
while run_monitoring and model is not None:
    if os.path.exists(live_data_path):
        try:
            df_live = pd.read_csv(live_data_path)
            if not df_live.empty:
                latest    = df_live.iloc[-1]
                t3        = float(latest['Hot_Fluid_Outlet_Temperature_T3_K'])
                t4        = float(latest['Cold_Fluid_Outlet_Temperature_T4_K'])
                temp_diff = abs(t3 - t4)

                features = np.array([[t3, t4, temp_diff]])
                rf_pred  = float(model.predict(features)[0])

                t3_metric.metric("Hot Fluid Outlet (T₃)",    f"{t3:.2f} K")
                t4_metric.metric("Cold Fluid Outlet (T₄)",   f"{t4:.2f} K")
                dt_metric.metric("Temperature Difference (ΔT)", f"{temp_diff:.2f} K")

                if rf_pred >= RF_ALARM:
                    fouling_metric.metric("Predicted Fouling (Rᶠ)", f"{rf_pred:.6f}",
                        delta="🚨 CRITICAL", delta_color="inverse")
                    status_alert.error(
                        "🚨 EMERGENCY: Severe fouling detected! Triggering cleaning cycle.")
                elif rf_pred >= RF_WARN:
                    fouling_metric.metric("Predicted Fouling (Rᶠ)", f"{rf_pred:.6f}",
                        delta="⚠️ WARNING", delta_color="off")
                    status_alert.warning(
                        "⚠️ ALERT: Maintenance required soon. Scaling layer increasing.")
                else:
                    fouling_metric.metric("Predicted Fouling (Rᶠ)", f"{rf_pred:.6f}",
                        delta="🟢 STABLE", delta_color="normal")
                    status_alert.success("🟢 Exchanger health is optimum.")

                timestamp = pd.Timestamp.now().strftime('%H:%M:%S')
                new_row = pd.DataFrame(
                    {'Timestamp': [timestamp], 'Fouling_Factor': [rf_pred]})
                st.session_state.history = pd.concat(
                    [st.session_state.history, new_row]).tail(60)

                fig = build_chart(st.session_state.history)
                chart_placeholder.plotly_chart(
                    fig, use_container_width=True,
                    config={'displayModeBar': False})

        except Exception as e:
            status_alert.warning(f"⚠️ Read error: {e}")

    time.sleep(2)
