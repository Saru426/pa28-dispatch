# PA-28 Pre-Flight Dispatch
A Streamlit web app that automates pre-flight dispatch calculations for Piper PA-28 aircraft — weight & balance, takeoff/landing performance, and runway selection — using live METAR data.
**Live app:** [pa28-dispatch.streamlit.app](https://pa28-dispatch.streamlit.app)
Built for flight training operations at Vero Beach Regional Airport (KVRB), where students are required to complete W&B and performance calculations from Piper POH graphs before every flight. This tool replaces that manual chart work with equation-based calculations and generates a printable dispatch sheet.
## Features
- **Fleet presets** — Basic empty weight, arm, and moment pre-loaded for every Skyborne PA-28 tail number (Warrior III and Pilot 100i), so there's no manual data entry or transcription error.
- **Instructor database** — Selecting an instructor automatically adds their weight and flight bag to the front-seat and baggage stations.
- **Live METAR** — Fetches the current KVRB METAR from the NOAA Aviation Weather API and parses wind, temperature, and the raw report.
- **Runway selection** — Decomposes the wind vector into headwind/crosswind components for each KVRB runway and recommends the runway with the best headwind component.
- **Performance calculations** — Takeoff ground roll and 50-ft obstacle distance (0° and 25° flaps), landing ground roll and obstacle distance, computed from digitized POH performance charts.
- **CG envelope validation** — Checks takeoff and landing CG against the POH forward/aft limits and flags any out-of-envelope condition.
- **Runway length check** — Compares the worst-case calculated distance against the selected runway's available length.
- **Printable dispatch sheet** — Renders all results onto a formatted W&B template and exports a one-click PDF.
## How the math works
Instead of reading values off POH charts, the performance charts were digitized into continuous multivariable polynomial regression equations — one engine per aircraft variant (Warrior III at 2,400 lbs max gross, Pilot 100i at 2,550 lbs):
1. **Base chart calculation** — Ground roll and obstacle distances as a function of surface temperature at sea level.
2. **Weight ratio scaling** — An empirical quadratic multiplier adjusts the baseline for actual takeoff/landing weight.
3. **Wind correction** — A linear slope reduces distance based on the headwind component.
Weight & balance follows the standard moment method: `CG = Total Moment / Total Weight`, computed at ramp, takeoff (after taxi burn), and landing (after fuel burn for the planned flight duration).
## Aircraft
| Variant | Type | Max Gross |
|---|---|---|
| Warrior III | PA-28-161 | 2,400 lbs |
| Pilot 100i | PA-28-181 | 2,550 lbs |
## Run locally
```bash
pip install streamlit numpy pandas requests pillow
streamlit run app.py
```
Requires `wb_template.jpg` (dispatch sheet template) and `Roboto-VariableFont_wdth,wght.ttf` in the same directory.
## Tech
Python · Streamlit · Pillow · NumPy · Pandas · NOAA Aviation Weather API
## Disclaimer
This is a student-built training aid. Always verify results against the official Pilot's Operating Handbook and your flight school's dispatch procedures before flight. Performance figures are derived from digitized charts and are approximations, not POH replacements.
