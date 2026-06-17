import streamlit as st
import numpy as np
import pandas as pd
import math
import requests
import re
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="PA-28 Pre-Flight Dispatch", page_icon="✈️", layout="wide")

# --- CUSTOM CSS TO TIGHTEN SPACING ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1, h2, h3, h4 { margin-bottom: 0.2rem !important; padding-bottom: 0 !important; }
        p { margin-bottom: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- MASTER PATHS ---
base_piper_path = './Piper/' 
paths = {
    "roll_0": os.path.join(base_piper_path, 'Takeoff_Roll_0/'),
    "obs_0": os.path.join(base_piper_path, 'Takeoff_Obstacle_0/'),
    "roll_25": os.path.join(base_piper_path, 'Takeoff_Roll_25/'),
    "obs_25": os.path.join(base_piper_path, 'Takeoff_Obstacle_25/'),
    "land_roll": os.path.join(base_piper_path, 'Landing_Roll/'),        
    "land_obs": os.path.join(base_piper_path, 'Landing_Obstacle_50/')   
}

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def go_home():
    st.session_state.page = 'home'

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=600)
def fetch_metar():
    url = "https://aviationweather.gov/api/data/metar?ids=KVRB&format=raw"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip().split('\n')[0]
    except:
        return None
    return None

def extract_wind_from_metar(metar):
    if not metar: return "00000KT"
    match = re.search(r'\b(\d{3}|VRB)(\d{2,3})(G\d{2,3})?(KT|MPS)\b(?:\s+(\d{3})V(\d{3})\b)?', metar)
    return match.group(0).strip() if match else "00000KT"

def parse_metar_wind(wind_str):
    wind_str = wind_str.upper()
    multiplier = 1.94384 if "MPS" in wind_str else 1.0
    wind_str = wind_str.replace('KT', '').replace('MPS', '')
    
    if 'V' in wind_str and not wind_str.startswith('VRB'):
        wind_str = wind_str.split()[0]
    if 'G' in wind_str:
        wind_str = wind_str.split('G')[0]
    if wind_str.startswith('VRB'):
        return 0, int(int(wind_str[3:]) * multiplier)
    return int(wind_str[:3]), int(int(wind_str[3:]) * multiplier)

def calculate_runway_winds(wind_dir, speed):
    runways = {"12L/R": 120, "30L/R": 300, "04": 40, "22": 220}
    results = []
    
    for rwy, hdg in runways.items():
        if speed == 0:
            hw, xw = 0.0, 0.0
        else:
            angle_rad = math.radians(wind_dir - hdg)
            hw = speed * math.cos(angle_rad)
            xw = abs(speed * math.sin(angle_rad))
            
        results.append({
            "Runway": rwy,
            "Headwind (kts)": round(hw, 1),
            "Crosswind (kts)": round(xw, 1)
        })
    return results

def get_best_runway(runway_winds_list, speed):
    if speed == 0:
        return "12L/R", 0.0, 0.0
    best = max(runway_winds_list, key=lambda x: x["Headwind (kts)"])
    return best["Runway"], best["Headwind (kts)"], best["Crosswind (kts)"]

def extract_temperature_from_metar(metar):
    if not metar: return 20
    match = re.search(r'\b(M?\d{2})/(M?\d{2})\b', metar)
    if match:
        temp_str = match.group(1)
        return -int(temp_str[1:]) if temp_str.startswith('M') else int(temp_str)
    return 20

def cg_is_within_limits(takeoff_weight, cg):
    cg_limits_table = [
        (2000, 83.8, 93), (2050, 84.3, 93), (2100, 84.8, 93),
        (2150, 85.3, 93), (2200, 85.8, 93), (2250, 86.3, 93),
        (2300, 86.8, 93), (2350, 87.3, 93), (2400, 87.8, 93)
    ]
    limits = min(cg_limits_table, key=lambda x: abs(x[0] - takeoff_weight))
    fwd, aft = limits[1], limits[2]
    return fwd, aft, fwd <= cg <= aft

def calculate_performance_metric(folder_path, takeoff_weight, temp, headwind):
    base_dir = folder_path.rstrip('/')
    nearest_weight = min([2000, 2050, 2100, 2150, 2200, 2250, 2300, 2350, 2400], key=lambda x: abs(x - takeoff_weight))
    weight_csv = os.path.join(base_dir, f"{nearest_weight} lbs.csv")
    wind_csv = os.path.join(base_dir, "Winds.csv")
    
    if not os.path.exists(weight_csv) or not os.path.exists(wind_csv):
        raise FileNotFoundError(f"Missing data in {base_dir}")

    df_weight = pd.read_csv(weight_csv, header=None)
    df_weight = df_weight.sort_values(by=0)
    base_dist = np.interp(temp, df_weight.iloc[:, 0].values, df_weight.iloc[:, 1].values)
    
    df_wind = pd.read_csv(wind_csv)
    ref_rolls = df_wind.iloc[:, 0].astype(float).values
    slopes = df_wind.iloc[:, 2].astype(float).values
    this_metric_slope = np.interp(base_dist, ref_rolls, slopes)
    
    return base_dist + (headwind * this_metric_slope)

# --- UI: MAIN PAGE LOGIC ---

if st.session_state.page == 'home':
    st.title("✈️ Welcome to the PA-28 Dispatch Tool")
    
    st.markdown("""
    ### Features included in your dispatch sheet:
    * **Weight & Balance:** Calculates Takeoff and Landing W&B against CG limits.
    * **Live Weather:** Pulls the current METAR for KVRB to determine temperature and winds.
    * **Runway Selection:** Automatically calculates the best runway, headwind, and crosswind.
    * **Performance Interpolation:** Dynamically computes takeoff and landing distances.
    """)
    st.error("**DISCLAIMER:** Please use for Weight and Balance calculation of PA-28-161 at sea level only and assume original values greater than these.")
    
    st.markdown("---")
    st.subheader("⚖️ Enter Flight Parameters")
    
    with st.form("dispatch_form"):
        col1, col2 = st.columns(2)
        with col1:
            empty_weight = st.number_input("Aircraft empty weight (lbs):", min_value=1000.0, max_value=2000.0, value=1500.0, step=10.0)
            pilot_weight = st.number_input("Pilot weight (lbs):", min_value=50.0, max_value=400.0, value=180.0, step=5.0)
            instructor_weight = st.number_input("Instructor weight (lbs):", min_value=0.0, max_value=400.0, value=180.0, step=5.0)
        with col2:
            baggage_weight = st.number_input("Baggage weight (lbs) [0 if none]:", min_value=0.0, max_value=200.0, value=10.0, step=5.0)
            lesson_hours = st.number_input("Est. flight duration (hours):", min_value=0.5, max_value=6.0, value=1.5, step=0.1)
        
        submit_button = st.form_submit_button("Calculate Dispatch", type="primary")
        
        if submit_button:
            # Save variables to session state so they persist on the next page
            st.session_state.ew = empty_weight
            st.session_state.pw = pilot_weight
            st.session_state.iw = instructor_weight
            st.session_state.bw = baggage_weight
            st.session_state.lh = lesson_hours
            st.session_state.page = 'results'
            st.rerun()

elif st.session_state.page == 'results':
    st.title("✈️ Pre-Flight Dispatch: Piper PA-28")

    # ---- ARM LOCATIONS & MATH ----
    empty_arm, pilot_arm, instructor_arm = 86.28, 80.5, 80.5
    baggage_arm, fuel_arm = 142.8, 95.0

    fuel_burn = st.session_state.lh * (11.4 * 6)
    fuel_weight = 48 * 6

    takeoff_weight = (st.session_state.ew + st.session_state.pw + st.session_state.iw + st.session_state.bw + fuel_weight) - 8
    takeoff_fuel = fuel_weight - 8
    landing_weight = takeoff_weight - fuel_burn
    landing_fuel = takeoff_fuel - fuel_burn

    def get_cg(w_fuel, w_total):
        return ((st.session_state.ew * empty_arm) + (st.session_state.pw * pilot_arm) + 
                (st.session_state.iw * instructor_arm) + (st.session_state.bw * baggage_arm) + 
                (w_fuel * fuel_arm)) / w_total

    cg_to = get_cg(takeoff_fuel, takeoff_weight)
    cg_ld = get_cg(landing_fuel, landing_weight)

    # ---- WEATHER & RUNWAY ----
    with st.spinner("Fetching METAR and calculating performance..."):
        metar = fetch_metar()
        if metar:
            wind_str = extract_wind_from_metar(metar)
            wind_dir, wind_speed = parse_metar_wind(wind_str)
            temp = extract_temperature_from_metar(metar)
            
            all_rwy_winds = calculate_runway_winds(wind_dir, wind_speed)
            best_rwy, best_hw, best_xw = get_best_runway(all_rwy_winds, wind_speed)
        else:
            st.error("Failed to fetch METAR data for KVRB.")
            st.button("🔙 Back to Home Page", on_click=go_home)
            st.stop()

        # --- SECTION 1: WEATHER & RUNWAY ---
        st.subheader("🌤️ 1. Weather & Runway (KVRB)")
        st.info(f"**METAR:** {metar}")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Temperature", f"{temp}°C")
        col2.metric("Wind", f"{wind_str.upper()}")
        col3.metric("Best Runway", f"{best_rwy} (Calm)" if wind_speed == 0 else best_rwy)
        col4.metric("Headwind", f"{best_hw:.1f} kts")
        col5.metric("Crosswind", f"{best_xw:.1f} kts")

        st.markdown("**Wind Components by Runway:**")
        st.dataframe(pd.DataFrame(all_rwy_winds), use_container_width=True, hide_index=True)
        st.markdown("---")

        # --- SECTION 2: WEIGHT & BALANCE ---
        st.subheader("⚖️ 2. Weight & Balance")
        col_wb1, col_wb2 = st.columns(2)
        fwd, aft, ok = cg_is_within_limits(takeoff_weight, cg_to)

        with col_wb1:
            st.markdown(f"""
            **Takeoff Parameters**
            - **Weight:** {takeoff_weight:.1f} lbs
            - **CG:** {cg_to:.2f} in
            """)
            if ok:
                st.success(f"✅ WITHIN LIMITS ({fwd}\" - {aft}\")")
            else:
                st.error(f"❌ OUT OF LIMITS ({fwd}\" - {aft}\")")

        with col_wb2:
            st.markdown(f"""
            **Landing Parameters**
            - **Weight:** {landing_weight:.1f} lbs
            - **CG:** {cg_ld:.2f} in
            """)

        st.markdown("---")

        # --- SECTION 3: PERFORMANCE ---
        st.subheader("🚀 3. Performance Data")
        
        try:
            perf_roll_0 = calculate_performance_metric(paths["roll_0"], takeoff_weight, temp, best_hw)
            perf_obs_0 = calculate_performance_metric(paths["obs_0"], takeoff_weight, temp, best_hw)
            perf_roll_25 = calculate_performance_metric(paths["roll_25"], takeoff_weight, temp, best_hw)
            perf_obs_25 = calculate_performance_metric(paths["obs_25"], takeoff_weight, temp, best_hw)
            perf_land_roll = calculate_performance_metric(paths["land_roll"], landing_weight, temp, best_hw)
            perf_land_obs = calculate_performance_metric(paths["land_obs"], landing_weight, temp, best_hw)
            
            perf_col1, perf_col2 = st.columns(2)
            
            with perf_col1:
                st.markdown(f"""
                #### 🛫 Takeoff
                **NORMAL (0° Flaps)**
                - Ground Roll: **{perf_roll_0:.0f} ft**
                - Over 50ft Obs: **{perf_obs_0:.0f} ft**

                **SHORT (25° Flaps)**
                - Ground Roll: **{perf_roll_25:.0f} ft**
                - Over 50ft Obs: **{perf_obs_25:.0f} ft**
                """)

            with perf_col2:
                st.markdown(f"""
                #### 🛬 Landing
                **NORMAL (40° Flaps)**
                - Ground Roll: **{perf_land_roll:.0f} ft**
                - Over 50ft Obs: **{perf_land_obs:.0f} ft**
                """)

        except FileNotFoundError as e:
            st.warning("⚠️ Performance data missing. Please ensure your CSV files are mapped correctly.")
        except Exception as e:
            st.error(f"⚠️ Performance calculation error: {e}")

    st.markdown("---") 
    
    # Navigation button back to Home Page
    st.button("🔙 Back to Home Page", on_click=go_home, type="primary")
