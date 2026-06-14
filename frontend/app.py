import streamlit as st
import pandas as pd
import time
import os


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')

INPUT_FILE = os.path.join(DATA_DIR, 'raw_data.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'ml_inference.csv')

st.set_page_config(page_title="PickAxe Dashboard", layout="wide")
st.title("PickAxe Live Vitals & Data Extrapolation")

try:
    RAW_COLUMNS = ['timestamp', 'hr', 'spo2', 'temp', 'acc_x', 'acc_y', 'acc_z', 'steps']
    df_raw = pd.read_csv(INPUT_FILE, names=RAW_COLUMNS, header=0).tail(50) 
    
    EXTRAPOLATION_COLUMNS = ['timestamp', 'sickness_score', 'sleep_stage', 'sleep_score']
    df_infer = pd.read_csv(OUTPUT_FILE, names=EXTRAPOLATION_COLUMNS, header=0).tail(1) 
    
except FileNotFoundError:
    st.error("Not connected")
    time.sleep(2)
    st.rerun()
except pd.errors.EmptyDataError:
    st.warning("Empty csv files")
    time.sleep(1)
    st.rerun()
except PermissionError:
    # deadlock condition
    time.sleep(0.1)
    st.rerun()

# dashboard code
latest_raw = df_raw.iloc[-1] if not df_raw.empty else None
latest_infer = df_infer.iloc[-1] if not df_infer.empty else None

if latest_raw is not None and latest_infer is not None:
    
    # data extrapolations
    st.subheader("Higher level extrapolations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Sickness likelihood", value=f"{latest_infer.get('sickness_score', 0)}/100")
    with col2:
        st.metric(label="Current sleep stage", value=str(latest_infer.get('sleep_stage', 'Unknown')))
    with col3:
        st.metric(label="Sleep quality score", value=f"{latest_infer.get('sleep_score', 0):.1f}%")

    st.markdown("---")

    st.subheader("Live Vitals")
    
    col4, col5, col6, col7, col8 = st.columns(5)
    
    with col4:
        st.metric(label="Heart Rate/BPM", value=int(latest_raw.get('hr', 0)))
    with col5:
        st.metric(label="SpO2 Percent", value=int(latest_raw.get('spo2', 0)))
    with col6:
        st.metric(label="Skin Temp (C)", value=f"{latest_raw.get('temp', 0):.1f}")
    with col7:
        st.metric(label="Accel (x, y, and z)", value=f"{latest_raw.get('acc_x', 0):.1f}, {latest_raw.get('acc_y', 0):.1f}, {latest_raw.get('acc_z', 0):.1f}")
    with col8:
        # gateway Step Counter
        st.metric(label="Step Counter", value=int(latest_raw.get('steps', 0)))

    st.subheader("Real time analytics")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.write("Heart Rate Trend")

        df_raw['timestamp'] = df_raw['timestamp'].astype(str)
        st.line_chart(df_raw.set_index('timestamp')['hr'])
        
    with chart_col2:
        st.write("Skin Temperature Trend")
        st.line_chart(df_raw.set_index('timestamp')['temp'])

time.sleep(1)
st.rerun()