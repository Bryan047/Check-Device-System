import streamlit as st
import pandas as pd
import time

# ==========================================
#  Config: ใส่ Link CSV 
# ==========================================
CSV_URL = "https://docs.google.com/spreadsheets/d/e/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=true&output=csv" #<- your Link google sheet file publish  .csv
# ==========================================

st.set_page_config(page_title="IT Monitor Center", layout="wide", page_icon="📡")

def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        expected_cols = [
            'SystemTime',       # เวลาของ Google
            'LogTime',          # เวลาที่ส่งจาก Agent
            'Asset ID',         # เลขครุภัณฑ์
            'Hostname',         
            'IP',               
            'OS',               
            'CPU',              
            'RAM',              
            'Disk C (%)', 
            'Disk C Free (GB)', 
            'Disk D (%)', 
            'Disk D Free (GB)',
            'Disk E (%)', 
            'Disk E Free (GB)' 
        ]
        
        # เปลี่ยนชื่อหัวตารางตามลำดับ
        if len(df.columns) >= len(expected_cols):
             df.columns.values[:len(expected_cols)] = expected_cols
        return df
    except Exception as e:
        return pd.DataFrame()

def safe_float(val):
    try:
        return float(str(val).replace('%', '').replace('-', '0'))
    except:
        return 0.0

# --- เริ่มหน้าจอ Dashboard ---
st.title("📡 System & Asset Monitor")
st.caption("Real-time Tracking Dashboard")

placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if not df.empty:
            # แปลง LogTime เป็น DateTime Object เพื่อให้จัดรูปแบบได้
            df['LogTime'] = pd.to_datetime(df['LogTime'], errors='coerce')
            
            # Group ข้อมูล (เอาข้อมูลล่าสุดของแต่ละเครื่อง)
            # ใช้ Asset ID เป็นตัวหลักในการแยกเครื่อง (ถ้า Asset ID ซ้ำ จะเอาเวลาล่าสุด)
            latest = df.sort_values('LogTime').groupby('Hostname').tail(1)

            # --- Metrics Summary ---
            c_vals = latest['Disk C (%)'].apply(safe_float)
            d_vals = latest['Disk D (%)'].apply(safe_float)
            e_vals = latest['Disk E (%)'].apply(safe_float)

            critical_count = len(c_vals[c_vals > 90]) + len(d_vals[d_vals > 90]) + len(e_vals[e_vals > 90])
            avg_cpu = latest['CPU'].apply(safe_float).mean()

            #-- แสดงผล Metrics ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🖥️ Active Assets", len(latest))
            col2.metric("🔥 Avg CPU", f"{avg_cpu:.1f}%")
            col3.metric("💻 Common OS", latest['OS'].mode()[0] if not latest.empty else "-")
            col4.metric("🚨 Critical Drives", f"{critical_count}", 
                        delta_color="inverse" if critical_count > 0 else "normal")

            st.divider()
            st.subheader("📋 Machine List")

            # --- เลือก Column ที่จะแสดงในตาราง ---
            display_cols = [
                'LogTime',      
                'Asset ID',     
                'Hostname', 
                'IP', 
                'OS',
                'CPU', 
                'RAM', 
                'Disk C (%)', 
                'Disk C Free (GB)', 
                'Disk D (%)', 
                'Disk D Free (GB)',
                'Disk E (%)', 
                'Disk E Free (GB)'
            ]
            
            existing_cols = [c for c in display_cols if c in latest.columns]
            
            # --- แสดงตาราง ---
            st.dataframe(
                latest[existing_cols].set_index('LogTime'), # ใช้ LogTime เป็น Index ซ้ายสุด
                use_container_width=True,
                height=600,
                column_config={
                    # จัดรูปแบบเวลาให้สวยงาม (DD/MM/YYYY HH:mm)
                    "LogTime": st.column_config.DatetimeColumn(
                        "Last Updated",
                        format="D MMM YYYY, HH:mm:ss",
                        step=60
                    ),
                    "CPU": st.column_config.NumberColumn(format="%.1f%%"),
                    "RAM": st.column_config.NumberColumn(format="%.1f%%"),
                    "Disk C Free (GB)": st.column_config.NumberColumn(format="%.1f GB"),
                    "Disk D Free (GB)": st.column_config.NumberColumn(format="%.1f GB"),
                    "Disk E Free (GB)": st.column_config.NumberColumn(format="%.1f GB"),
                }
            )
            
        else:
            st.warning("⚠️ Waiting for data... (Check CSV Link or Column Order)")
            
    time.sleep(10) # Refresh ทุก 30 วินาที
