import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import time
import threading
import importlib.util
import plotly.graph_objects as go

# ── Auto-start DCS simulator in background thread ─────────────────────────────
def _start_dcs_simulator():
    """
    Loads dcs .py from the same folder and runs it in a daemon thread.
    A daemon thread dies automatically when the Streamlit process exits —
    no manual cleanup needed.
    """
    sim_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dcs .py')
    if not os.path.exists(sim_path):
        return  # silently skip if file not found

    spec   = importlib.util.spec_from_file_location("dcs", sim_path)
    module = importlib.util.module_from_spec(spec)

    def _run():
        try:
            spec.loader.exec_module(module)
        except Exception:
            pass  # keep dashboard alive even if simulator crashes

    t = threading.Thread(target=_run, daemon=True)
    t.start()

# Only start once per Streamlit session (not on every rerun)
if 'dcs_started' not in st.session_state:
    _start_dcs_simulator()
    st.session_state['dcs_started'] = True

# ── Page config ──────────────────────────────────────────────────────────────
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

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
model_path     = os.path.join(BASE_DIR, 'fouling_sensor_model (2).pkl')
live_data_path = os.path.join(BASE_DIR, 'live_plant_data.csv')

# Thresholds
RF_WARN  = 0.0005   # yellow warning line
RF_ALARM = 0.0010   # red alarm line

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
    st.sidebar.write(f"Check that the `.pkl` file is in: `{BASE_DIR}`")
    st.sidebar.write(f"Error: {e}")

# ── Sidebar controls ──────────────────────────────────────────────────────────
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
    t3_metric     = st.empty()
    t4_metric     = st.empty()
    dt_metric     = st.empty()
    fouling_metric = st.empty()
    status_alert  = st.empty()

with col2:
    st.markdown("### Real-Time Fouling Accumulation Trend ($R_f$)")
    chart_placeholder = st.empty()

# ── Session history ───────────────────────────────────────────────────────────
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Timestamp', 'Fouling_Factor'])


# ── Chart builder ─────────────────────────────────────────────────────────────
def build_chart(history_df: pd.DataFrame) -> go.Figure:
    """
    Build a Plotly line chart where the Rf trace changes colour depending on
    which zone the *current* value sits in:
      - below RF_WARN  → blue   (#58a6ff)
      - RF_WARN–ALARM  → amber  (#d29922)
      - above RF_ALARM → red    (#f85149)

    The trick: we split the series into contiguous colour segments so each
    segment is drawn as its own Scatter trace with the correct colour.
    """
    fig = go.Figure()

    if history_df.empty:
        _add_threshold_lines(fig)
        _style_figure(fig)
        return fig

    times  = history_df['Timestamp'].tolist()
    values = history_df['Fouling_Factor'].tolist()

    def zone_color(v):
        if v >= RF_ALARM:
            return 'red'
        elif v >= RF_WARN:
            return 'amber'
        return 'blue'

    COLOR_MAP = {
        'blue' : '#58a6ff',
        'amber': '#d29922',
        'red'  : '#f85149',
    }

    # ── Segment the series by colour zone ────────────────────────────────────
    # Each segment: list of (index, time, value) with the same colour
    segments = []
    if values:
        cur_color = zone_color(values[0])
        seg_t  = [times[0]]
        seg_v  = [values[0]]

        for i in range(1, len(values)):
            c = zone_color(values[i])
            if c == cur_color:
                seg_t.append(times[i])
                seg_v.append(values[i])
            else:
                # keep last point of old segment as first of new → smooth join
                segments.append((cur_color, seg_t[:], seg_v[:]))
                cur_color = c
                seg_t = [times[i-1], times[i]]
                seg_v = [values[i-1], values[i]]

        segments.append((cur_color, seg_t, seg_v))

    # ── Draw segments ─────────────────────────────────────────────────────────
    legend_added = set()
    for color_key, seg_t, seg_v in segments:
        show_leg = color_key not in legend_added
        legend_added.add(color_key)

        label = {'blue': 'Rf (normal)', 'amber': 'Rf (warning)', 'red': 'Rf (alarm)'}[color_key]

        fig.add_trace(go.Scatter(
            x=seg_t, y=seg_v,
            mode='lines',
            line=dict(color=COLOR_MAP[color_key], width=2),
            name=label,
            showlegend=show_leg,
            legendgroup=color_key,
            hovertemplate='%{x}<br>Rf = %{y:.6f}<extra></extra>',
        ))

    # ── Threshold lines ───────────────────────────────────────────────────────
    _add_threshold_lines(fig)

    # ── Shaded zones ─────────────────────────────────────────────────────────
    y_max = max(max(values) * 1.25, RF_ALARM * 1.3)

    # Warning zone (amber, between RF_WARN and RF_ALARM)
    fig.add_hrect(
        y0=RF_WARN, y1=RF_ALARM,
        fillcolor='rgba(210,153,34,0.07)',
        line_width=0,
        annotation_text="Warning zone",
        annotation_position="top left",
        annotation_font=dict(size=10, color='#d29922'),
    )
    # Alarm zone (red, above RF_ALARM)
    fig.add_hrect(
        y0=RF_ALARM, y1=y_max,
        fillcolor='rgba(248,81,73,0.07)',
        line_width=0,
        annotation_text="Alarm zone",
        annotation_position="top left",
        annotation_font=dict(size=10, color='#f85149'),
    )

    _style_figure(fig, y_max=y_max)
    return fig


def _add_threshold_lines(fig):
    fig.add_hline(
        y=RF_WARN,
        line=dict(color='#d29922', width=1.2, dash='dash'),
        annotation_text=f"Warning  {RF_WARN}",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color='#d29922'),
    )
    fig.add_hline(
        y=RF_ALARM,
        line=dict(color='#f85149', width=1.5),
        annotation_text=f"Alarm  {RF_ALARM}",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color='#f85149'),
    )


def _style_figure(fig, y_max=None):
    if y_max is None:
        y_max = RF_ALARM * 1.4

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=36),
        paper_bgcolor='#0d1117',
        plot_bgcolor='#0d1117',
        font=dict(color='#8b949e', size=11),
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='right',  x=1,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11),
        ),
        xaxis=dict(
            showgrid=False,
            showticklabels=True,
            tickangle=-45,
            tickfont=dict(size=9),
            color='#8b949e',
            nticks=8,
            linecolor='#21262d',
        ),
        yaxis=dict(
            gridcolor='rgba(48,54,61,0.6)',
            gridwidth=0.5,
            range=[0, y_max],
            tickfont=dict(size=10),
            color='#8b949e',
            linecolor='#21262d',
            title=dict(text='Rf (m²·K/W)', font=dict(size=11, color='#8b949e')),
            tickformat='.4f',
        ),
        hovermode='x unified',
    )


# ── Real-time loop ─────────────────────────────────────────────────────────────
while run_monitoring and model is not None:
    if os.path.exists(live_data_path):
        try:
            df_live = pd.read_csv(live_data_path)
            if not df_live.empty:
                latest = df_live.iloc[-1]

                t3        = float(latest['Hot_Fluid_Outlet_Temperature_T3_K'])
                t4        = float(latest['Cold_Fluid_Outlet_Temperature_T4_K'])
                temp_diff = abs(t3 - t4)

                features = np.array([[t3, t4, temp_diff]])
                rf_pred  = float(model.predict(features)[0])

                # ── Sensor metrics ────────────────────────────────────────────
                t3_metric.metric("Hot Fluid Outlet (T₃)",        f"{t3:.2f} K")
                t4_metric.metric("Cold Fluid Outlet (T₄)",       f"{t4:.2f} K")
                dt_metric.metric("Engineered Approach (ΔT)",     f"{temp_diff:.2f} K")

                # ── Alarm logic (fixed: outer ≥ alarm, elif ≥ warn, else ok) ─
                if rf_pred >= RF_ALARM:
                    fouling_metric.metric(
                        "Predicted Fouling (Rᶠ)", f"{rf_pred:.6f}",
                        delta="🚨 CRITICAL", delta_color="inverse")
                    status_alert.error(
                        "🚨 EMERGENCY: Severe fouling detected! Triggering cleaning cycle.")

                elif rf_pred >= RF_WARN:
                    fouling_metric.metric(
                        "Predicted Fouling (Rᶠ)", f"{rf_pred:.6f}",
                        delta="⚠️ WARNING", delta_color="off")
                    status_alert.warning(
                        "⚠️ ALERT: Maintenance required soon. Scaling layer increasing.")

                else:
                    fouling_metric.metric(
                        "Predicted Fouling (Rᶠ)", f"{rf_pred:.6f}",
                        delta="🟢 STABLE", delta_color="normal")
                    status_alert.success("🟢 Exchanger health is optimum.")

                # ── History & chart ───────────────────────────────────────────
                timestamp = pd.Timestamp.now().strftime('%H:%M:%S')
                new_row = pd.DataFrame(
                    {'Timestamp': [timestamp], 'Fouling_Factor': [rf_pred]})
                st.session_state.history = pd.concat(
                    [st.session_state.history, new_row]).tail(60)

                fig = build_chart(st.session_state.history)
                chart_placeholder.plotly_chart(
                    fig, use_container_width=True, config={'displayModeBar': False})

        except Exception as e:
            status_alert.warning(f"⚠️ Read error: {e}")

    time.sleep(2)
