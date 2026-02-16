import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="RIR Master List", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for "Bloomberg Terminal" Dark Theme
st.markdown("""
    <style>
        /* General App Background */
        .stApp {background-color: #0e1117; color: #e0e0e0;}
        
        /* Metric Cards (Top Detail View) */
        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            padding: 15px;
            border-radius: 6px;
        }
        div[data-testid="stMetricLabel"] {color: #ff9f1c !important; font-weight: bold;}
        div[data-testid="stMetricValue"] {color: #ffffff !important;}
        
        /* Inputs & Widgets */
        .stTextInput input {color: #ff9f1c; background-color: #0d1117; border: 1px solid #30363d;}
        .stMultiSelect, .stSlider {color: #e0e0e0;}
        
        /* Hide Default Streamlit Branding */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE (LIVE SYNC) ---
@st.cache_data(ttl=600) # Cache clears every 10 mins so data stays fresh
def load_data():
    # YOUR LIVE GOOGLE SHEET CSV LINK
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTKjBzr7QuJk9g7TR6p0-_GdPQDvesG9a1KTny6y5IyK0Z-G0_C98T-AfUyaAdyDB11h3vdpgc_h3Hh/pub?gid=618318322&single=true&output=csv"
    
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"⚠️ Connection Error: Could not fetch data from Google Sheets. ({e})")
        return pd.DataFrame()

    # --- DATA CLEANING & TYPE SAFETY ---
    
    # 1. Remove Empty Rows
    df = df.dropna(subset=['Ticker'])
    df = df[df['Ticker'] != 'Ticker'] # Remove header repeats if any
    
    # 2. Text Normalization (Fill NaNs)
    text_cols = ['Ticker', 'Strategy', 'Company', 'Underlying', 'Payout', 'Category', 'Pay Date']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)
        else:
            df[col] = '' # Create column if missing to prevent crash

    # 3. Numeric Conversion (Handle %, $, M, B)
    # Clean Dividends/Yields
    for col in ['Dividend', 'Expense Ratio', 'Yield']:
        if col in df.columns:
            # Remove % sign, convert to float
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Clean Price (Remove $ sign)
    if 'Current Price' in df.columns:
        df['Current Price'] = df['Current Price'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['Current Price'] = pd.to_numeric(df['Current Price'], errors='coerce').fillna(0)

    # Clean AUM (Convert 1.5B to 1,500,000,000)
    def parse_aum(x):
        x = str(x).upper().replace('$', '').replace(',', '')
        if 'M' in x: return float(x.replace('M', '')) * 1_000_000
        if 'B' in x: return float(x.replace('B', '')) * 1_000_000_000
        try: return float(x)
        except: return 0
    
    if 'AUM' in df.columns:
        df['AUM_Numeric'] = df['AUM'].apply(parse_aum)
    
    return df

# Load Data
df = load_data()

# Stop if data failed to load
if df.empty:
    st.stop()

# --- 3. FILTER BAR (SEARCH & CONTROLS) ---
# Layout: Top Row = Search + Strategy + Freq. Bottom Row = Yield + Issuer
col1, col2, col3 = st.columns([2, 1.5, 1])

with col1:
    # Universal Search Bar
    search_input = st.text_input("🔍 Search (Ticker, Strategy, or Company)", placeholder="Type anything... (e.g. 'NVDY' or 'Bitcoin')")

with col2:
    # Strategy Filter (Sorted Alphabetically)
    # We split the comma-separated tags to create a clean dropdown list
    all_tags = set()
    for tags in df['Category'].str.split(','):
        for tag in tags:
            clean = tag.strip()
            if clean: all_tags.add(clean)
    
    selected_strategies = st.multiselect("Filter by Strategy", sorted(list(all_tags)))

with col3:
    # Frequency Filter
    freq_opts = sorted(df['Payout'].unique().tolist())
    selected_freq = st.multiselect("Payout Freq.", freq_opts)

# Second Row of Filters
col4, col5 = st.columns([1, 2])
with col4:
    # Minimum Yield Slider (Default 0 means "Off")
    min_yield = st.number_input("Min Yield % (Optional)", min_value=0.0, max_value=200.0, value=0.0, step=5.0)

with col5:
    # Issuer Filter
    issuer_opts = sorted(df['Company'].unique().tolist())
    selected_issuer = st.multiselect("Filter by Issuer / Company", issuer_opts)

# --- 4. FILTERING LOGIC ---
filtered = df.copy()

# A. Universal Search
if search_input:
    # Checks Ticker, Strategy, Company, Category, AND Underlying for matches
    search_term = search_input.lower()
    filtered = filtered[
        filtered['Ticker'].str.lower().str.contains(search_term) |
        filtered['Strategy'].str.lower().str.contains(search_term) |
        filtered['Company'].str.lower().str.contains(search_term) |
        filtered['Category'].str.lower().str.contains(search_term) |
        filtered['Underlying'].str.lower().str.contains(search_term)
    ]

# B. Apply Strategy Filter (OR Logic)
if selected_strategies:
    # If user selects "Bitcoin" and "0DTE", it shows funds that match EITHER
    pattern = '|'.join(selected_strategies)
    filtered = filtered[filtered['Category'].str.contains(pattern, case=False, regex=True)]

# C. Apply Frequency Filter
if selected_freq:
    filtered = filtered[filtered['Payout'].isin(selected_freq)]

# D. Apply Issuer Filter
if selected_issuer:
    filtered = filtered[filtered['Company'].isin(selected_issuer)]

# E. Apply Yield Filter (Only if user set it > 0)
if min_yield > 0 and 'Dividend' in filtered.columns:
    filtered = filtered[filtered['Dividend'] >= min_yield]

# --- 5. DISPLAY RESULTS ---
st.divider()

# A. INSPECT FUND (Detail View)
# Dropdown allows "Drill Down" into specific fund details
fund_options = ["Select a Fund..."] + sorted(filtered['Ticker'].unique().tolist())
selected_fund = st.selectbox("Inspect Specific Fund Details:", fund_options)

if selected_fund != "Select a Fund...":
    # Get the single row for the selected fund
    row = filtered[filtered['Ticker'] == selected_fund].iloc[0]
    
    # Display 4 Key Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Price", f"${row.get('Current Price', 0):.2f}")
    m2.metric("Annual Yield", f"{row.get('Dividend', 0)}%")
    m3.metric("Payout Freq", row.get('Payout', '-'))
    m4.metric("Expense Ratio", f"{row.get('Expense Ratio', 0)}%")
    
    # Display Strategy Text & Tags
    st.info(f"**Strategy:** {row.get('Strategy', 'No description available.')}")
    st.caption(f"**Categories:** {row.get('Category')}")
    st.caption(f"**Next Pay Date:** {row.get('Pay Date', '-')}")
    st.divider()

# B. MAIN DATA TABLE
st.subheader(f"Results ({len(filtered)})")

# columns to display in the main list
display_cols = ['Ticker', 'Current Price', 'Dividend', 'Payout', 'Pay Date', 'Company', 'Category']
# Ensure columns exist
final_cols = [c for c in display_cols if c in filtered.columns]

if not filtered.empty:
    st.dataframe(
        filtered[final_cols].style.format({
            'Dividend': '{:.2f}%',
            'Current Price': '${:.2f}'
        }),
        height=600,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No funds found matching your criteria.")
