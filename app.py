import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import time

# Dashboard Page Configuration
st.set_page_config(page_title="Real-Time Fouling Monitor", layout="wide")
st.title("🏭 Real-Time Industrial Exchanger Soft-Sensor (Digital Twin)")
st.markdown("---")

# 1. PATH SETUP (PyCharm automatic base directory detect kar lega)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'fouling_sensor_model (2).pkl')
live_data_path = os.path.join(BASE_DIR, 'live_plant_data.csv')


# 2. PICKLE MODEL LOADER
@st.cache_resource
def load_pickle_model():
    # 'rb' (Read Binary) mode mein exact file ko open kar rahe hain
    with open(model_path, 'rb') as file:
        return pickle.load(file)


try:
    model = load_pickle_model()
    st.sidebar.success("🟢 ML Soft-Sensor Engine: ACTIVE")
    st.sidebar.info(f"Loaded: fouling_sensor_model(1).pkl")
except Exception as e:
    st.sidebar.error("❌ Model File Not Found!")
    st.sidebar.write(f"Check karo kya '.pkl' file isi folder mein hai: `{BASE_DIR}`")
    st.sidebar.write(f"Error Log: {e}")

# 3. DASHBOARD LAYOUT
st.subheader("Live Plant Telemetry & Diagnostic Streams")
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Current Sensor States")
    t3_metric = st.empty()
    t4_metric = st.empty()
    dt_metric = st.empty()
    fouling_metric = st.empty()
    status_alert = st.empty()

with col2:
    st.markdown("### Real-Time Fouling Accumulation Trend ($R_f$)")
    chart_placeholder = st.empty()

# Graph ki history maintain karne ke liye Streamlit Session State
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Timestamp', 'Fouling_Factor'])

st.sidebar.markdown("---")
run_monitoring = st.sidebar.checkbox("Start Live DCS Data Stream", value=True)

# 4. REAL-TIME BACKGROUND PROCESSING LOOP
while run_monitoring and 'model' in locals():
    if os.path.exists(live_data_path):
        try:
            df_live = pd.read_csv(live_data_path)
            if not df_live.empty:
                latest_reading = df_live.iloc[-1]

                # Live Data se values nikal rahe hain
                t3 = float(latest_reading['Hot_Fluid_Outlet_Temperature_T3_K'])
                t4 = float(latest_reading['Cold_Fluid_Outlet_Temperature_T4_K'])
                temp_diff = abs(t3 - t4)

                # Model Prediction
                features = np.array([[t3, t4, temp_diff]])
                rf_pred = model.predict(features)[0]

                # Web Screen standard par metrics update
                t3_metric.metric("Hot Fluid Outlet ($T_3$)", f"{t3:.2f} K")
                t4_metric.metric("Cold Fluid Outlet ($T_4$)", f"{t4:.2f} K")
                dt_metric.metric("Engineered Approach ($\Delta T$)", f"{temp_diff:.2f} K")

                # Alarms Logic based on predicted Fouling Factor
                if rf_pred >= 0.0010:
                    fouling_metric.metric("Predicted Fouling ($R_f$)", f"{rf_pred:.6f}", delta="🚨 CRITICAL",
                                          delta_color="inverse")
                    status_alert.error("🚨 EMERGENCY: Severe fouling detected! Triggering cleaning cycle.")
                elif rf_pred >= 0.0005:
                    fouling_metric.metric("Predicted Fouling ($R_f$)", f"{rf_pred:.6f}", delta="⚠️ WARNING")
                    status_alert.warning("⚠️ ALERT: Maintenance required soon. Scaling layer increasing.")
                else:
                    fouling_metric.metric("Predicted Fouling ($R_f$)", f"{rf_pred:.6f}", delta="🟢 STABLE")
                    status_alert.success("🟢 Exchanger health is optimum.")

                # Real-time Line Chart Plotting
                timestamp = pd.Timestamp.now().strftime('%H:%M:%S')
                new_row = pd.DataFrame({'Timestamp': [timestamp], 'Fouling_Factor': [rf_pred]})
                st.session_state.history = pd.concat([st.session_state.history, new_row]).tail(30)
                chart_placeholder.line_chart(st.session_state.history.set_index('Timestamp'))

        except Exception as e:
            pass

    time.sleep(2)
