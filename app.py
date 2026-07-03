import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import math
import requests
import re

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

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def go_home():
    st.session_state.page = 'home'

# --- HELPER FUNCTIONS ---
def scroll_to_top():
    js = '''
    <script>
        var body = window.parent.document.querySelector(".main");
        if (body) {
            body.scrollTop = 0;
        }
        window.parent.scrollTo(0, 0);
    </script>
    '''
    components.html(js, height=0)

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


# =============================================================================
# PIPER PA-28 EMPIRICAL PERFORMANCE ENGINES
# =============================================================================

def calc_flaps_0_ground_roll(weight, temp, headwind):
    base_2400 = (0.0205 * (temp ** 2)) + (18.8268 * temp) + 782.8214
    weight_ratio = (0.0000004932 * (weight ** 2)) - (0.001232 * weight) + 1.1184
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0135 * base_dist) - 2.1047
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_25_ground_roll(weight, temp, headwind):
    base_2400 = (0.0080 * (temp ** 2)) + (13.7589 * temp) + 799.4643
    weight_ratio = (0.0000002787 * (weight ** 2)) - (0.0004820 * weight) + 0.5508
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0107 * base_dist) - 5.0694
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_0_obstacle(weight, temp, headwind):
    base_2400 = (0.0018 * (temp ** 2)) + (24.3607 * temp) + 1569.5000
    weight_ratio = (0.0000002759 * (weight ** 2)) - (0.0002545 * weight) + 0.0235
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0107 * base_dist) - 5.3652
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_25_obstacle(weight, temp, headwind):
    base_2400 = (-0.0500 * (temp ** 2)) + (25.4000 * temp) + 1254.0000
    weight_ratio = (0.0000001896 * (weight ** 2)) - (0.00007642 * weight) + 0.0883
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0109 * base_dist) - 4.7111
    return max(0, base_dist + (headwind * wind_slope))

def calc_landing_ground_roll(weight, temp, headwind):
    base_2400 = (0.0046 * (temp ** 2)) + (1.8721 * temp) + 583.1857
    weight_ratio = (0.0000000176 * (weight ** 2)) + (0.0003462 * weight) + 0.0668
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0129 * base_dist) - 3.5358
    return max(0, base_dist + (headwind * wind_slope))

def calc_landing_obstacle(weight, temp, headwind):
    base_2400 = (2.8714 * temp) + 1094.4286
    weight_ratio = (-0.0000000392 * (weight ** 2)) + (0.0005736 * weight) - 0.1512
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0047 * base_dist) - 11.6423
    return max(0, base_dist + (headwind * wind_slope))


# --- UI: MAIN PAGE LOGIC ---

if st.session_state.page == 'home':
    scroll_to_top()
    st.title("✈️ Weight & Balance")
    
    st.markdown("""
    ### Features included in your dispatch sheet:
    * **Weight & Balance:** Calculates Takeoff and Landing W&B against CG limits.
    * **Live Weather:** Pulls the current METAR for KVRB to determine temperature and winds.
    * **Runway Selection:** Automatically calculates the best runway, headwind, and crosswind.
    * **Performance Engines:** Dynamically computes takeoff and landing distances using empirical flight test polynomials.
    """)
    st.error("**DISCLAIMER:** Please use only for Weight and Balance calculation of PA-28-161 at sea level only and assume original values greater than these.")
    
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
            st.session_state.ew = empty_weight
            st.session_state.pw = pilot_weight
            st.session_state.iw = instructor_weight
            st.session_state.bw = baggage_weight
            st.session_state.lh = lesson_hours
            st.session_state.page = 'results'
            st.rerun()

elif st.session_state.page == 'results':
    scroll_to_top()
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
            # Calling the new empirical math engines instead of parsing CSVs
            perf_roll_0 = calc_flaps_0_ground_roll(takeoff_weight, temp, best_hw)
            perf_obs_0 = calc_flaps_0_obstacle(takeoff_weight, temp, best_hw)
            
            perf_roll_25 = calc_flaps_25_ground_roll(takeoff_weight, temp, best_hw)
            perf_obs_25 = calc_flaps_25_obstacle(takeoff_weight, temp, best_hw)
            
            perf_land_roll = calc_landing_ground_roll(landing_weight, temp, best_hw)
            perf_land_obs = calc_landing_obstacle(landing_weight, temp, best_hw)
            
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

        except Exception as e:
            st.error(f"⚠️ Performance calculation error: {e}")

    st.markdown("---") 
    st.button("🔙 Back to Home Page", on_click=go_home, type="primary")