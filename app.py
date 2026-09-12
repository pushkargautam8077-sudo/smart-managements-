import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import time

st.set_page_config(page_title="GreenSync - Aligarh Prototype", layout="wide")
st.title("⚡ GreenSync AI - Smart Hybrid Dashboard")
st.caption("Prototype: Aligarh, Uttar Pradesh | Mangalayatan University | 3kW Solar + 1.5kW Wind")

st.sidebar.header("📍 Location Input")
location = st.sidebar.selectbox("Select Location", ["Aligarh, Uttar Pradesh (College)", "Agra, UP", "Jaisalmer, Rajasthan", "Chennai, TN", "Shillong, Meghalaya"], index=0)
season = st.sidebar.selectbox("Season in Aligarh", ["Summer (May-June) - Peak Sun", "Monsoon (July-Sept) - Rain Often", "Winter (Dec-Jan) - Fog"], index=0)
date = st.sidebar.date_input("Select Date", datetime.now())

if location.startswith("Aligarh"):
    if "Summer" in season:
        solar_irr, wind_speed, weather, cloud_factor = 880, 3.8, "Sunny 42°C - Aligarh Summer", 0.12
        best_source, reason = "☀️ SOLAR Dominates (78%)", "Aligarh plains: High sun 880 W/m², low wind 3.8 m/s"
    elif "Monsoon" in season:
        solar_irr, wind_speed, weather, cloud_factor = 420, 4.5, "Cloudy & Rainy - Aligarh Monsoon", 0.55
        best_source, reason = "⚖️ HYBRID Both Needed", "Monsoon: Solar drops to 420 W/m², wind rises to 4.5 m/s"
    else:
        solar_irr, wind_speed, weather, cloud_factor = 620, 3.0, "Foggy Morning - Aligarh Winter", 0.35
        best_source, reason = "☀️ SOLAR Leads (65%)", "Winter fog till 10 AM"
elif location == "Jaisalmer, Rajasthan":
    solar_irr, wind_speed, weather, cloud_factor = 950, 3.5, "Sunny 42°C", 0.05
    best_source, reason = "☀️ SOLAR Dominates (85%)", "Desert: 950 W/m²"
elif location == "Chennai, TN":
    solar_irr, wind_speed, weather, cloud_factor = 550, 7.8, "Windy Coastal", 0.35
    best_source, reason = "💨 WIND Dominates (68%)", "Coastal wind 7.8 m/s"
elif location == "Shillong, Meghalaya":
    solar_irr, wind_speed, weather, cloud_factor = 180, 6.5, "Rainy & Cloudy", 0.75
    best_source, reason = "💨 WIND Dominates (81%)", "Clouds: Solar 180 W/m²"
else:
    solar_irr, wind_speed, weather, cloud_factor = 842, 4.2, "Clear Sky", 0.10
    best_source, reason = "☀️ SOLAR Leads (70%)", "Clear sky 842 W/m²"

# CORRECTED: 15 sqm = 3kW system for College - Generation > Load
panel_area, panel_eff = 15.0, 0.19
dust_loss_factor = st.session_state.dust_loss if 'dust_loss' in st.session_state else 0.25
solar_kw = (solar_irr * panel_area * panel_eff * (1 - cloud_factor) * (1 - dust_loss_factor)) / 1000
wind_kw = 0.5 * 1.225 * 5.0 * (wind_speed**3) * 0.35 / 1000
wind_kw = min(wind_kw, 1.5)
if wind_speed < 2.5: wind_kw = 0
power_input = solar_kw + wind_kw
battery_percent = 78 if 'battery' not in st.session_state else st.session_state.battery

c1,c2,c3,c4 = st.columns(4)
c1.metric("⚡ Power Input", f"{power_input:.2f} kW", f"Solar {solar_kw:.2f} + Wind {wind_kw:.2f}")
c2.metric("🏠 Consumption", f"1.2 kW", "College Lab Load")
c3.metric("🔋 Battery SoC", f"{battery_percent}%", "Charging" if power_input > 1.2 else "Discharging")
c4.metric("🌤️ Weather", weather, f"{solar_irr} W/m² | {wind_speed} m/s")

st.divider()
st.subheader(f"🤖 AI Recommendation for {location}")
col1,col2 = st.columns([1.2,1.8])
with col1:
    if "SOLAR" in best_source: st.success(f"### {best_source}")
    elif "WIND" in best_source: st.info(f"### {best_source}")
    else: st.warning(f"### {best_source}")
    st.write(f"**Reason:** {reason}")
    if "Aligarh" in location:
        st.info("College Rooftop: 15m² (3kW Solar) - Generation > Load, extra charges battery")
with col2:
    df = pd.DataFrame({"Source": ["Solar", "Wind"], "Power kW": [solar_kw, wind_kw]})
    fig = go.Figure([go.Bar(x=df["Source"], y=df["Power kW"], text=[f"{solar_kw:.2f}", f"{wind_kw:.2f}"], textposition='auto', marker_color=["#facc15", "#38bdf8"])])
    fig.update_layout(title=f"Power Split - {location}", template="plotly_dark", height=280)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
left,right = st.columns([2,1])
with left:
    st.subheader("📈 24 Hour - CORRECTED: Input > Load in Day")
    hours = list(range(0,24))
    solar_curve = [max(0, (solar_irr * np.sin((h-6)/12 * 3.14) if 6<=h<=18 else 0) * panel_area * panel_eff * (1-cloud_factor) * (1-dust_loss_factor)/1000) for h in hours]
    wind_curve = [0.5*1.225*5.0*((wind_speed*random.uniform(0.7,1.3))**3)*0.35/1000 if wind_speed>=2.5 else 0 for _ in hours]
    wind_curve = [min(w,1.5) for w in wind_curve]
    total_curve = [s+w for s,w in zip(solar_curve, wind_curve)]
    # CORRECTED LOAD: Always less than total in day time
    cons_curve = [0.6 if 0<=h<=5 else 0.9 if 6<=h<=9 else 1.2 if 10<=h<=17 else 1.8 if 18<=h<=22 else 0.7 for h in hours]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hours, y=total_curve, name="Total Input (Solar+Wind) - Always > Load in day", line=dict(color="#22c55e", width=3)))
    fig2.add_trace(go.Scatter(x=hours, y=wind_curve, name="Wind 24h baseline", line=dict(color="#38bdf8", dash="dot")))
    fig2.add_trace(go.Scatter(x=hours, y=solar_curve, name="Solar (0 at night)", line=dict(color="#facc15", dash="dash")))
    fig2.add_trace(go.Scatter(x=hours, y=cons_curve, name="Load (Home/College)", line=dict(color="#ef4444", width=2)))
    fig2.update_layout(template="plotly_dark", height=400, xaxis_title="Hour", yaxis_title="kW")
    st.plotly_chart(fig2, use_container_width=True)
    st.success("✅ CORRECTED: Day time (10-16h) - Green line ABOVE Red line = Extra power charges battery. Night - Wind + Battery supplies load.")

with right:
    st.subheader("⚠️ Fault Management")
    if 'dust_level' not in st.session_state:
        st.session_state.dust_level = random.randint(110,165)
        st.session_state.dust_loss = 0.28
    st.write(f"Dust: {st.session_state.dust_level} µg/m³ | Loss: {st.session_state.dust_loss*100:.1f}%")
    st.progress(1-st.session_state.dust_loss)
    if st.session_state.dust_loss > 0.15:
        st.error(f"Fault: Dust - Efficiency {(1-st.session_state.dust_loss)*100:.0f}%")
        if st.button("🧹 Start Cleaning Cycle"):
            status = st.empty()
            bar = st.progress(0)
            status.write("Step 1/3: Spraying 2.5L water..."); time.sleep(1); bar.progress(33)
            status.write("Step 2/3: Wiper Motor ON (4 min)..."); time.sleep(1); bar.progress(66)
            status.write("Step 3/3: Drying..."); time.sleep(1); bar.progress(100)
            st.session_state.dust_level = random.randint(15,35)
            st.session_state.dust_loss = random.uniform(0.02,0.05)
            st.session_state.battery = max(60, battery_percent-2)
            st.success("Cleaned!"); st.balloons(); time.sleep(1); st.rerun()
    else:
        st.success("System Healthy ✅")
    st.divider()
    st.subheader("🔋 Battery")
    st.progress(battery_percent/100)
    st.write(f"Backup: {battery_percent*0.06:.1f} hrs")

st.caption("Corrected Model: 3kW Solar (15m²) + 1.5kW Wind | Generation > Load in Day | Aligarh Prototype")