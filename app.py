import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import math
import requests
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="PA-28 Pre-Flight Dispatch", page_icon="✈️", layout="wide")

# --- DATA: AIRCRAFT FLEETS ---
WARRIOR_FLEET = {
    "N158ND - SFY200": {"W": 1546, "A": 85.23, "M": 131788},
    "N159ND - SFY201": {"W": 1535, "A": 85.09, "M": 130605},
    "N241ND - SFY202": {"W": 1546, "A": 86.23, "M": 133333},
    "N300DC - SFY203": {"W": 1554, "A": 86.27, "M": 134100},
    "N371DC - SFY204": {"W": 1548, "A": 86.16, "M": 133425},
    "N550PU - SFY205": {"W": 1542, "A": 85.82, "M": 132348},
    "N551PU - SFY206": {"W": 1544, "A": 85.21, "M": 131585},
    "N552PU - SFY207": {"W": 1545, "A": 85.13, "M": 131561},
    "N553PU - SFY208": {"W": 1545, "A": 85.42, "M": 132040},
    "N554PU - SFY209": {"W": 1537, "A": 85.89, "M": 132043},
    "N555PU - SFY210": {"W": 1540, "A": 85.99, "M": 132462},
    "N557PU - SFY550": {"W": 1538, "A": 85.89, "M": 132194},
    "N559PU - SFY552": {"W": 1542, "A": 85.92, "M": 132520},
    "N561PU - SFY553": {"W": 1539, "A": 85.61, "M": 131778},
    "N901FC - SFY555": {"W": 1554, "A": 86.25, "M": 134103},
    "N902FC - SFY556": {"W": 1568, "A": 87.33, "M": 136973},
    "N903FC - SFY557": {"W": 1549, "A": 86.74, "M": 134443},
    "N9287E - SFY558": {"W": 1536, "A": 85.94, "M": 132075},
    "N44426 - SFY426": {"W": 1562, "A": 87.02, "M": 135954},
    "N4443Q - SFY427": {"W": 1563, "A": 87.11, "M": 136217},
    "N4445J - SFY428": {"W": 1563, "A": 87.05, "M": 136120},
    "N4445K - SFY429": {"W": 1558, "A": 87.03, "M": 135650},
    "N4445P - SFY430": {"W": 1563, "A": 87.05, "M": 136120},
    "N4445S - SFY431": {"W": 1557, "A": 86.96, "M": 135462},
    "N4445V - SFY432": {"W": 1559, "A": 86.89, "M": 135524},
    "N4445Y - SFY433": {"W": 1560, "A": 87.13, "M": 135981},
    "N8569Q - SFY434": {"W": 1560, "A": 86.93, "M": 135625},
    "N8570R - SFY435": {"W": 1564, "A": 86.76, "M": 135758},
    "N8571Y - SFY436": {"W": 1563, "A": 86.78, "M": 135670},
    "N8572Z - SFY437": {"W": 1564, "A": 87.12, "M": 136326},
    "N8573J - SFY438": {"W": 1562, "A": 87.21, "M": 136279},
    "N8574K - SFY439": {"W": 1561, "A": 86.92, "M": 135743},
    "N8575W - SFY440": {"W": 1560, "A": 87.01, "M": 135808},
    "N8576X - SFY441": {"W": 1557, "A": 86.97, "M": 135479},
    "N8577Y - SFY442": {"W": 1561, "A": 86.93, "M": 135761},
    "N8578Z - SFY443": {"W": 1557, "A": 86.97, "M": 135479},
    "N8580E - SFY444": {"W": 1555, "A": 86.69, "M": 134866},
    "N8581J - SFY445": {"W": 1561, "A": 86.96, "M": 135783}
}

PILOT_100I_FLEET = {
    "N772VB - SFY112": {"W": 1605, "A": 86.88, "M": 139490},
    "N8581A - SFY113": {"W": 1614, "A": 87.15, "M": 140712},
    "N8582E - SFY114": {"W": 1621, "A": 86.81, "M": 140704},
    "N8583B - SFY115": {"W": 1619, "A": 86.90, "M": 140759},
    "N8584D - SFY116": {"W": 1624, "A": 86.89, "M": 141123},
    "N8585H - SFY117": {"W": 1633, "A": 87.31, "M": 142594},
    "N8586J - SFY118": {"W": 1632, "A": 87.54, "M": 142877},
    "N8587L - SFY119": {"W": 1631, "A": 85.23, "M": 142296},
    "N8588P - SFY120": {"W": 1633, "A": 87.56, "M": 142987},
    "N8589S - SFY121": {"W": 1631, "A": 87.23, "M": 142285},
    "N8590Z - SFY122": {"W": 1625, "A": 87.15, "M": 141626},
    "N8591C - SFY123": {"W": 1625, "A": 87.39, "M": 142019},
    "N8592E - SFY124": {"W": 1626, "A": 87.45, "M": 142207},
    "N8593G - SFY125": {"W": 1631, "A": 87.24, "M": 142295},
    "N8594F - SFY126": {"W": 1630, "A": 87.47, "M": 142579},
    "N8595D - SFY127": {"W": 1627, "A": 87.62, "M": 142565}
}

# --- INSTRUCTOR DATA (Alphabetical First Last) ---
INSTRUCTORS = {
    "Abbigail Snyder": {"wt": 210, "bag": 15}, "Abel Simorangkir": {"wt": 170, "bag": 10},
    "Abraham Barkett": {"wt": 180, "bag": 10}, "Alan Haaland": {"wt": 165, "bag": 5},
    "Albert Moe": {"wt": 220, "bag": 5}, "Alexander Balsitis": {"wt": 140, "bag": 10},
    "Allison Coyle": {"wt": 130, "bag": 10}, "Andrew James": {"wt": 200, "bag": 10},
    "Austin Haight": {"wt": 160, "bag": 10}, "Ava Jevizian": {"wt": 135, "bag": 10},
    "Bailey Youngman": {"wt": 180, "bag": 10}, "Benjamin Nist": {"wt": 165, "bag": 10},
    "Brandon Balnoschan": {"wt": 170, "bag": 10}, "Brandon Gerwel": {"wt": 230, "bag": 10},
    "Caleb Cope": {"wt": 135, "bag": 10}, "Caleb Deer": {"wt": 175, "bag": 10},
    "Charlye Howerton": {"wt": 145, "bag": 10}, "Christopher Bailey": {"wt": 185, "bag": 10},
    "Christopher Koszeghy": {"wt": 185, "bag": 15}, "Christopher Marcinik": {"wt": 135, "bag": 10},
    "Christopher Waters": {"wt": 190, "bag": 15}, "Claire Nolan": {"wt": 125, "bag": 15},
    "Cody Howard": {"wt": 185, "bag": 10}, "Collin Eberle": {"wt": 195, "bag": 10},
    "Connor Field": {"wt": 190, "bag": 10}, "Corey Glass": {"wt": 165, "bag": 10},
    "Courtney Brown": {"wt": 140, "bag": 10}, "Courtney Lewis": {"wt": 155, "bag": 15},
    "Daniel Gage": {"wt": 180, "bag": 10}, "David Avirama": {"wt": 175, "bag": 10},
    "David Escobar": {"wt": 210, "bag": 5}, "Devin Dames": {"wt": 210, "bag": 5},
    "Elijah Caldwell": {"wt": 170, "bag": 10}, "Emanuele More": {"wt": 190, "bag": 5},
    "Emerson Swaney": {"wt": 155, "bag": 10}, "Emily Roche": {"wt": 95, "bag": 10},
    "Frank Larson": {"wt": 215, "bag": 10}, "Giuseppe Ruggeri": {"wt": 110, "bag": 10},
    "Harrison Reeb": {"wt": 145, "bag": 10}, "Isaac Morales": {"wt": 170, "bag": 15},
    "Jack O'Brien": {"wt": 160, "bag": 10}, "Jacob Burns": {"wt": 165, "bag": 15},
    "Jacob Pownall": {"wt": 145, "bag": 10}, "Jaheem Richards": {"wt": 145, "bag": 10},
    "Jerrod Scheid": {"wt": 185, "bag": 10}, "Jesse Pruitt": {"wt": 172, "bag": 10},
    "John Campuzano": {"wt": 160, "bag": 10}, "John Curtas": {"wt": 135, "bag": 10},
    "John Korfant": {"wt": 190, "bag": 10}, "John Pinero": {"wt": 200, "bag": 0},
    "John Potochak": {"wt": 185, "bag": 10}, "Kailey Renn": {"wt": 140, "bag": 15},
    "Kathleen Norton": {"wt": 170, "bag": 15}, "Kelsey Farber": {"wt": 130, "bag": 10},
    "Kyle Wood": {"wt": 185, "bag": 15}, "Larry Hearold": {"wt": 210, "bag": 10},
    "Lauren Laborde": {"wt": 110, "bag": 15}, "Liam McGrath": {"wt": 185, "bag": 10},
    "Luis Echavarria": {"wt": 240, "bag": 5}, "Maddisen Franco": {"wt": 150, "bag": 20},
    "Marissa Avery": {"wt": 145, "bag": 15}, "Matthew Galiano": {"wt": 195, "bag": 10},
    "Matthew Love": {"wt": 130, "bag": 10}, "Matthew Mulholland": {"wt": 180, "bag": 10},
    "Michael DiFederico": {"wt": 220, "bag": 10}, "Michael McGraw": {"wt": 195, "bag": 10},
    "Natalia Enciso": {"wt": 165, "bag": 10}, "Natalie Roberts": {"wt": 120, "bag": 10},
    "Nathaniel Carpio": {"wt": 175, "bag": 10}, "Natlie Hanks": {"wt": 160, "bag": 10},
    "Nicholas Pagliusi": {"wt": 135, "bag": 15}, "Nick Yerxa": {"wt": 175, "bag": 10},
    "Niklas Eberly": {"wt": 210, "bag": 20}, "Orlando Olivero": {"wt": 245, "bag": 5},
    "Oscar Talero": {"wt": 190, "bag": 10}, "Patrick Seigh": {"wt": 225, "bag": 10},
    "Paul Bardwell": {"wt": 205, "bag": 10}, "Philip Bregsguard": {"wt": 205, "bag": 10},
    "Raymond Cluadio": {"wt": 190, "bag": 10}, "Roka Wolgamott": {"wt": 215, "bag": 20},
    "Rona Escano": {"wt": 165, "bag": 15}, "Ryan Finney": {"wt": 150, "bag": 10},
    "Ryan Goonen": {"wt": 215, "bag": 10}, "Ryan Kilby": {"wt": 170, "bag": 15},
    "Samuel Howerton": {"wt": 200, "bag": 15}, "Samuel Leonard": {"wt": 240, "bag": 10},
    "Scott Hauser": {"wt": 190, "bag": 10}, "Shane Reynolds": {"wt": 239, "bag": 10},
    "Tancredi Dami": {"wt": 170, "bag": 10}, "Tayshaun Tramel": {"wt": 162, "bag": 15},
    "Thomas Copley": {"wt": 185, "bag": 10}, "Trevor Schubert": {"wt": 185, "bag": 10},
    "Tristan French": {"wt": 180, "bag": 20}, "Veronika Wojciechowski": {"wt": 150, "bag": 10},
    "Zachery Allen": {"wt": 215, "bag": 10}, "Zachery Love": {"wt": 185, "bag": 10},
    "Zander Barnard": {"wt": 200, "bag": 10}
}

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1, h2, h3, h4 { margin-bottom: 0.2rem !important; padding-bottom: 0 !important; }
        p, li { margin-bottom: 0.5rem !important; font-size: 18px !important; }
        .stNumberInput label p, .stSelectbox label p { font-size: 18px !important; font-weight: 600 !important; }
        .stNumberInput div, .stSelectbox div { font-size: 18px !important; }
        .stButton button p { font-size: 20px !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# --- KEEP AWAKE SCRIPT ---
def keep_awake():
    js = '''<script>setInterval(() => fetch(window.location.href), 300000);</script>'''
    components.html(js, height=0)

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def go_home():
    st.session_state.page = 'home'

def scroll_to_top():
    js = '''<script>
        var body = window.parent.document.querySelector(".main");
        if (body) { body.scrollTop = 0; }
        window.parent.scrollTo(0, 0);
    </script>'''
    components.html(js, height=0)

# --- WEATHER & RUNWAY FUNCTIONS ---
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
        results.append({"Runway": rwy, "Headwind (kts)": round(hw, 1), "Crosswind (kts)": round(xw, 1)})
    return results

def get_best_runway(runway_winds_list, speed):
    if speed == 0: return "12L/R", 0.0, 0.0
    best = max(runway_winds_list, key=lambda x: x["Headwind (kts)"])
    return best["Runway"], best["Headwind (kts)"], best["Crosswind (kts)"]

def extract_temperature_from_metar(metar):
    if not metar: return 20
    match = re.search(r'\b(M?\d{2})/(M?\d{2})\b', metar)
    if match:
        temp_str = match.group(1)
        return -int(temp_str[1:]) if temp_str.startswith('M') else int(temp_str)
    return 20

def cg_is_within_limits(takeoff_weight, cg, ac_type):
    if ac_type == "Warrior III":
        cg_limits_table = [
            (2000, 83.8, 93), (2050, 84.3, 93), (2100, 84.8, 93),
            (2150, 85.3, 93), (2200, 85.8, 93), (2250, 86.3, 93),
            (2300, 86.8, 93), (2350, 87.3, 93), (2400, 87.8, 93)
        ]
        limits = min(cg_limits_table, key=lambda x: abs(x[0] - takeoff_weight))
        fwd, aft = limits[1], limits[2]
        return fwd, aft, fwd <= cg <= aft
    else:
        aft_limit = 93.0
        if takeoff_weight <= 2050:
            fwd_limit = 82.0
        else:
            fwd_limit = 82.0 + ((takeoff_weight - 2050) / 90.0)
        is_within = fwd_limit <= cg <= aft_limit and takeoff_weight <= 2558
        return round(fwd_limit, 2), aft_limit, is_within

# --- EMPIRICAL PERFORMANCE ENGINES (Warrior III) ---
def calc_flaps_0_ground_roll_warrior(weight, temp, headwind):
    base_2400 = (0.0205 * (temp ** 2)) + (18.8268 * temp) + 782.8214
    weight_ratio = (0.0000004932 * (weight ** 2)) - (0.001232 * weight) + 1.1184
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0135 * base_dist) - 2.1047
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_25_ground_roll_warrior(weight, temp, headwind):
    base_2400 = (0.0080 * (temp ** 2)) + (13.7589 * temp) + 799.4643
    weight_ratio = (0.0000002787 * (weight ** 2)) - (0.0004820 * weight) + 0.5508
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0107 * base_dist) - 5.0694
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_0_obstacle_warrior(weight, temp, headwind):
    base_2400 = (0.0018 * (temp ** 2)) + (24.3607 * temp) + 1569.5000
    weight_ratio = (0.0000002759 * (weight ** 2)) - (0.0002545 * weight) + 0.0235
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0107 * base_dist) - 5.3652
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_25_obstacle_warrior(weight, temp, headwind):
    base_2400 = (-0.0500 * (temp ** 2)) + (25.4000 * temp) + 1254.0000
    weight_ratio = (0.0000001896 * (weight ** 2)) - (0.00007642 * weight) + 0.0883
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0109 * base_dist) - 4.7111
    return max(0, base_dist + (headwind * wind_slope))

def calc_landing_ground_roll_warrior(weight, temp, headwind):
    base_2400 = (0.0046 * (temp ** 2)) + (1.8721 * temp) + 583.1857
    weight_ratio = (0.0000000176 * (weight ** 2)) + (0.0003462 * weight) + 0.0668
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0129 * base_dist) - 3.5358
    return max(0, base_dist + (headwind * wind_slope))

def calc_landing_obstacle_warrior(weight, temp, headwind):
    base_2400 = (2.8714 * temp) + 1094.4286
    weight_ratio = (-0.0000000392 * (weight ** 2)) + (0.0005736 * weight) - 0.1512
    base_dist = base_2400 * weight_ratio
    wind_slope = (-0.0047 * base_dist) - 11.6423
    return max(0, base_dist + (headwind * wind_slope))


# --- EMPIRICAL PERFORMANCE ENGINES (Pilot 100i) ---
def calc_flaps_0_ground_roll_100i(weight, temp, headwind):
    base_2550 = (0.0375 * (temp ** 2)) + (9.5 * temp) + 915.0
    weight_ratio = (0.0000000067 * (weight ** 2)) + (0.0007405 * weight) - 0.9320
    base_dist = base_2550 * weight_ratio
    wind_slope = -0.0143 * base_dist
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_25_ground_roll_100i(weight, temp, headwind):
    base_2550 = (0.0375 * (temp ** 2)) + (10.25 * temp) + 975.0
    weight_ratio = (0.000000638 * (weight ** 2)) - (0.002054 * weight) + 2.089
    base_dist = base_2550 * weight_ratio
    wind_slope = -0.0150 * base_dist
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_0_obstacle_100i(weight, temp, headwind):
    base_2550 = (0.075 * (temp ** 2)) + (17.0 * temp) + 1730.0
    weight_ratio = (0.00000038 * (weight ** 2)) - (0.00094 * weight) + 1.15
    base_dist = base_2550 * weight_ratio
    wind_slope = -0.0105 * base_dist
    return max(0, base_dist + (headwind * wind_slope))

def calc_flaps_25_obstacle_100i(weight, temp, headwind):
    base_2550 = (0.05 * (temp ** 2)) + (14.0 * temp) + 1390.0
    weight_ratio = (0.00000002 * (weight ** 2)) + (0.00071 * weight) - 0.94
    base_dist = base_2550 * weight_ratio
    wind_slope = -0.0126 * base_dist
    return max(0, base_dist + (headwind * wind_slope))

def calc_landing_ground_roll_100i(weight, temp, headwind):
    base_2550 = (3.375 * temp) + 865.0
    weight_ratio = (0.00037 * weight) + 0.057
    base_dist = base_2550 * weight_ratio
    wind_slope = -0.0161 * base_dist
    return max(0, base_dist + (headwind * wind_slope))

def calc_landing_obstacle_100i(weight, temp, headwind):
    base_2550 = (3.25 * temp) + 1352.5
    weight_ratio = (0.000199 * weight) + 0.4925
    base_dist = base_2550 * weight_ratio
    wind_slope = -0.0134 * base_dist
    return max(0, base_dist + (headwind * wind_slope))


# --- FONT LOADER ---
def get_font(size):
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try: 
        return ImageFont.truetype(font_path, size=size)
    except Exception:
        return ImageFont.load_default()

# --- IMAGE GENERATOR ---
def generate_dispatch_sheet(wb_data, perf_data, env_data):
    try:
        img = Image.open("wb_template.jpg").convert("RGB")
    except FileNotFoundError:
        return None

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("Arial.ttf", size=65)
    except IOError:
        font = ImageFont.load_default()

    color = (0, 0, 0)
    
    # Columns X coords
    x_wt = 950
    x_arm = 1425
    x_mom = 1910

    def write(x, y, value, fmt="", align="mm"):
        if value is not None:
            text = f"{value:{fmt}}" if fmt else str(value)
            draw.text((x, y), text, fill=color, font=font, anchor=align)

    # SECTION 1: W&B 
    write(566, 488, env_data['ac_reg'], align="mm") # Prints Aircraft N-Number
    
    write(x_wt, 585, wb_data['bew_wt'], ".1f")
    write(x_arm, 585, wb_data['bew_arm'], ".2f")
    write(x_mom, 585, wb_data['bew_mom'], ".0f")

    write(x_wt, 664, wb_data['pilot_wt'], ".1f")
    write(x_arm, 664, wb_data['pilot_arm'], ".1f")
    write(x_mom, 664, wb_data['pilot_mom'], ".0f")

    write(x_wt, 743, wb_data['pax_wt'], ".1f")
    write(x_arm, 743, wb_data['pax_arm'], ".1f")
    write(x_mom, 743, wb_data['pax_mom'], ".0f")

    write(x_wt, 822, wb_data['bag_wt'], ".1f")
    write(x_arm, 822, wb_data['bag_arm'], ".2f")
    write(x_mom, 822, wb_data['bag_mom'], ".0f")

    write(x_wt, 901, wb_data['fuel_wt'], ".1f")
    write(x_arm, 901, wb_data['fuel_arm'], ".2f")
    write(x_mom, 901, wb_data['fuel_mom'], ".0f")

    write(x_wt, 980, wb_data['ramp_wt'], ".1f")
    write(x_arm, 980, wb_data['ramp_cg'], ".2f")
    write(x_mom, 980, wb_data['ramp_mom'], ".0f")

    write(x_wt, 1059, wb_data['taxi_wt'], ".1f")
    write(x_arm, 1059, wb_data['taxi_arm'], ".2f")
    write(x_mom, 1059, wb_data['taxi_mom'], ".0f")

    write(x_wt, 1206, wb_data['to_wt'], ".1f")
    write(x_arm, 1206, wb_data['to_cg'], ".2f")
    write(x_mom, 1206, wb_data['to_mom'], ".0f")

    write(x_wt, 1292, wb_data['burn_wt'], ".1f")
    write(x_arm, 1292, wb_data['burn_arm'], ".2f")
    write(x_mom, 1292, wb_data['burn_mom'], ".0f")

    write(x_wt, 1444, wb_data['ld_wt'], ".1f")
    write(x_arm, 1444, wb_data['ld_cg'], ".2f")
    write(x_mom, 1444, wb_data['ld_mom'], ".0f")

    # SECTION 2: PERFORMANCE
    write(981, 2382, perf_data['roll_0'], ".0f")
    write(1249, 2382, perf_data['roll_25'], ".0f")
    write(1761, 2382, perf_data['obs_0'], ".0f")
    write(1980, 2382, perf_data['obs_25'], ".0f")
    
    write(1127, 2486, perf_data['Vy'], ".0f")

    write(1127, 2790, perf_data['land_roll'], ".0f")
    write(1876, 2790, perf_data['land_obs'], ".0f")

    # SECTION 3: WEATHER, RUNWAY & LIMITS NOTES
    rwy_str = env_data['rwy']
    rwy_len_int = 7314 if "12" in rwy_str or "30" in rwy_str else 4974
    rwy_text = f"{rwy_str} - {rwy_len_int}'"
    
    draw.text((1541, 3077), rwy_text, fill=color, font=font, anchor="mm")
    
    base_x = 2300
    current_y = 530
    
    draw.text((base_x, current_y), "Current METAR:", fill=color, font=font, anchor="lm")
    current_y += 80
    
    wrapped_metar = textwrap.wrap(env_data['metar'], width=26)
    
    box_x0 = base_x - 30
    box_x1 = base_x + 950 
    box_y0 = current_y - 40
    box_y1 = current_y + (len(wrapped_metar) * 80) + 10
    
    draw.rectangle([box_x0, box_y0, box_x1, box_y1], outline=color, width=5)
    
    for line in wrapped_metar:
        draw.text((base_x, current_y), line, fill=color, font=font, anchor="lm")
        current_y += 80
        
    current_y = box_y1 + 80
    
    wind_comp_text = f"HW: {env_data['hw']:.1f} kts   |   XW: {env_data['xw']:.1f} kts at {rwy_str}"
    draw.text((base_x, current_y), wind_comp_text, fill=color, font=font, anchor="lm")
    current_y += 80
    
    _, _, to_ok = cg_is_within_limits(wb_data['to_wt'], wb_data['to_cg'], env_data['ac_type'])
    _, _, ld_ok = cg_is_within_limits(wb_data['ld_wt'], wb_data['ld_cg'], env_data['ac_type'])
    
    if to_ok and ld_ok:
        draw.text((base_x, current_y), "T/O & LND CG: WITHIN LIMITS", fill=color, font=font, anchor="lm")
    else:
        draw.text((base_x, current_y), "WARNING: CG OUT OF LIMITS", fill=color, font=font, anchor="lm")
    current_y += 80
    
    max_dist = max([
        perf_data['roll_0'], perf_data['obs_0'], 
        perf_data['roll_25'], perf_data['obs_25'], 
        perf_data['land_roll'], perf_data['land_obs']
    ])
    
    if max_dist < rwy_len_int:
        dist_status = f"All Distances < {rwy_len_int}' RWY (Clear)"
    else:
        dist_status = f"WARNING: Exceeds {rwy_len_int}' RWY"
        
    draw.text((base_x, current_y), dist_status, fill=color, font=font, anchor="lm")

    return img


# --- UI: MAIN PAGE LOGIC ---
keep_awake()

if st.session_state.page == 'home':
    scroll_to_top()
    st.title("Print your Weight and Balance sheet using current METAR")
    st.markdown("---")
    
    # Step 1: Initial Selection (Warrior III or Pilot 100i)
    ac_type_choice = st.radio("Select Aircraft Type:", ["Warrior III", "Pilot 100i"], horizontal=True)
    st.markdown("---")
    
    active_fleet = WARRIOR_FLEET if ac_type_choice == "Warrior III" else PILOT_100I_FLEET

    with st.form("dispatch_form"):
        col1, col2 = st.columns(2)
        with col1:
            ac_selected = st.selectbox("Select Aircraft:", list(active_fleet.keys()))
            student_weight = st.number_input("Student/Pilot weight (lbs):", min_value=50.0, max_value=400.0, value=160.0, step=10.0)
            
            ip_list = ["None"] + list(INSTRUCTORS.keys())
            selected_ip = st.selectbox("Instructor (Automatically adds Weight & Baggage):", ip_list)
            
        with col2:
            pax_weight = st.number_input("Aft Passengers weight (lbs) [0 if none]:", min_value=0.0, max_value=400.0, value=0.0, step=10.0)
            
            if ac_type_choice == "Warrior III":
                student_baggage = st.number_input("Student Baggage weight (lbs):", min_value=0.0, max_value=200.0, value=0.0, step=10.0)
            else:
                student_baggage = 0.0
                st.info("ℹ️ Piper 100i has no baggage area; Add your baggage weight to Aft Passenger weight.")
                
            lesson_hours = st.number_input("Est. flight duration (hours):", min_value=0.5, max_value=6.0, value=1.5, step=0.1)
        
        submit_button = st.form_submit_button("Calculate & Generate Sheet", type="primary")
        
        if submit_button:
            st.session_state.ac_type = ac_type_choice
            st.session_state.ew = active_fleet[ac_selected]["W"]
            st.session_state.ea = active_fleet[ac_selected]["A"]
            st.session_state.em = active_fleet[ac_selected]["M"]
            st.session_state.ac_reg = ac_selected.split(" - ")[0]

            if selected_ip != "None":
                ip_wt = float(INSTRUCTORS[selected_ip]["wt"])
                ip_bag = float(INSTRUCTORS[selected_ip]["bag"])
            else:
                ip_wt = 0.0
                ip_bag = 0.0
                
            st.session_state.pw = student_weight + ip_wt
            st.session_state.pax = pax_weight
            
            if ac_type_choice == "Warrior III":
                total_baggage = student_baggage + ip_bag
                st.session_state.bw = min(200.0, total_baggage)
            else:
                # For 100i, instructor bag weight rolls into rear passenger / structural weight handling if needed, or set to 0 per specs
                st.session_state.bw = 0.0
                # If instructor has bag weight in 100i, add it to pax or handle cleanly:
                st.session_state.pax += ip_bag
            
            st.session_state.lh = lesson_hours
            st.session_state.page = 'results'
            st.rerun()

elif st.session_state.page == 'results':
    scroll_to_top()
    st.title("Aircraft Takeoff and Landing Data & Weather Planning")
    st.markdown("---")

    # ---- ARM LOCATIONS & MATH ----
    empty_arm = st.session_state.ea
    pilot_arm = 80.5
    pax_arm = 118.1
    baggage_arm = 142.8 if st.session_state.ac_type == "Warrior III" else 0
    fuel_arm = 95.0

    front_seat_wt = st.session_state.pw 
    fuel_wt = 288.0 
    
    if st.session_state.ac_type == "Warrior III":
        taxi_wt = -7.0
    else:
        taxi_wt = -8.0

    burn_wt = -(st.session_state.lh * 11.4 * 6)

    ew_mom = st.session_state.em
    front_mom = front_seat_wt * pilot_arm
    pax_mom = st.session_state.pax * pax_arm
    bag_mom = st.session_state.bw * baggage_arm
    fuel_mom = fuel_wt * fuel_arm
    
    ramp_wt = st.session_state.ew + front_seat_wt + st.session_state.pax + st.session_state.bw + fuel_wt
    ramp_mom = ew_mom + front_mom + pax_mom + bag_mom + fuel_mom
    ramp_cg = ramp_mom / ramp_wt if ramp_wt > 0 else 0

    taxi_mom = taxi_wt * fuel_arm
    
    to_wt = ramp_wt + taxi_wt
    to_mom = ramp_mom + taxi_mom
    to_cg = to_mom / to_wt if to_wt > 0 else 0

    burn_mom = burn_wt * fuel_arm
    
    ld_wt = to_wt + burn_wt
    ld_mom = to_mom + burn_mom
    ld_cg = ld_mom / ld_wt if ld_wt > 0 else 0

    wb_dict = {
        'bew_wt': st.session_state.ew, 'bew_arm': empty_arm, 'bew_mom': ew_mom,
        'pilot_wt': front_seat_wt, 'pilot_arm': pilot_arm, 'pilot_mom': front_mom,
        'pax_wt': st.session_state.pax, 'pax_arm': pax_arm, 'pax_mom': pax_mom,
        'bag_wt': st.session_state.bw, 'bag_arm': baggage_arm, 'bag_mom': bag_mom,
        'fuel_wt': fuel_wt, 'fuel_arm': fuel_arm, 'fuel_mom': fuel_mom,
        'ramp_wt': ramp_wt, 'ramp_cg': ramp_cg, 'ramp_mom': ramp_mom,
        'taxi_wt': taxi_wt, 'taxi_arm': fuel_arm, 'taxi_mom': taxi_mom,
        'to_wt': to_wt, 'to_cg': to_cg, 'to_mom': to_mom,
        'burn_wt': burn_wt, 'burn_arm': fuel_arm, 'burn_mom': burn_mom,
        'ld_wt': ld_wt, 'ld_cg': ld_cg, 'ld_mom': ld_mom
    }

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
            
        env_dict = {
            'metar': metar,
            'rwy': best_rwy,
            'hw': best_hw,
            'xw': best_xw,
            'ac_reg': st.session_state.ac_reg,
            'ac_type': st.session_state.ac_type
        }

        # --- PERFORMANCE MATH ---
        perf_dict = {}
        try:
            if st.session_state.ac_type == "Warrior III":
                perf_dict['roll_0'] = calc_flaps_0_ground_roll_warrior(to_wt, temp, best_hw)
                perf_dict['obs_0'] = calc_flaps_0_obstacle_warrior(to_wt, temp, best_hw)
                perf_dict['roll_25'] = calc_flaps_25_ground_roll_warrior(to_wt, temp, best_hw)
                perf_dict['obs_25'] = calc_flaps_25_obstacle_warrior(to_wt, temp, best_hw)
                perf_dict['land_roll'] = calc_landing_ground_roll_warrior(ld_wt, temp, best_hw)
                perf_dict['land_obs'] = calc_landing_obstacle_warrior(ld_wt, temp, best_hw)
            else:
                perf_dict['roll_0'] = calc_flaps_0_ground_roll_100i(to_wt, temp, best_hw)
                perf_dict['obs_0'] = calc_flaps_0_obstacle_100i(to_wt, temp, best_hw)
                perf_dict['roll_25'] = calc_flaps_25_ground_roll_100i(to_wt, temp, best_hw)
                perf_dict['obs_25'] = calc_flaps_25_obstacle_100i(to_wt, temp, best_hw)
                perf_dict['land_roll'] = calc_landing_ground_roll_100i(ld_wt, temp, best_hw)
                perf_dict['land_obs'] = calc_landing_obstacle_100i(ld_wt, temp, best_hw)
        except Exception as e:
            st.error(f"⚠️ Performance calculation error: {e}")

        perf_dict['Vy'] = 79 if st.session_state.ac_type == "Warrior III" else 76

        # --- VISUAL RENDERING ---
        col_left, col_mid, col_right = st.columns([1, 4, 1])
        
        with col_mid:
            final_img = generate_dispatch_sheet(wb_data=wb_dict, perf_data=perf_dict, env_data=env_dict)
            
            if final_img:
                st.image(final_img)
                
                buf = io.BytesIO()
                final_img.convert('RGB').save(buf, format="PDF")
                byte_im = buf.getvalue()
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    st.download_button(
                        label="📄 Download Ready Sheet (PDF)",
                        data=byte_im,
                        file_name=f"{st.session_state.ac_type.lower().replace(' ', '_')}_dispatch_sheet.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with btn_col2:
                    st.button("🔙 Adjust Inputs", on_click=go_home, type="primary", use_container_width=True)
            else:
                st.error("Could not generate image. Please ensure 'wb_template.jpg' is in the same folder.")
