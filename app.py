import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="RIR Master List", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp {background-color: #0e1117; color: #e0e0e0;}
        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            padding: 15px;
            border-radius: 6px;
        }
        div[data-testid="stMetricLabel"] {color: #ff9f1c !important; font-weight: bold;}
        div[data-testid="stMetricValue"] {color: #ffffff !important;}
        .stTextInput input, .stMultiSelect, .stSlider {color: #e0e0e0;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE (FIXED) ---
@st.cache_data
def load_data():
    # LINK TO YOUR LIVE GOOGLE SHEET CSV (Paste your link here if using live sync)
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTKjBzr7QuJk9g7TR6p0-_GdPQDvesG9a1KTny6y5IyK0Z-G0_C98T-AfUyaAdyDB11h3vdpgc_h3Hh/pubhtml?gid=618318322&single=true" 
    
    try:
        df = pd.read_csv(csv_url)
    except:
        # Fallback if file not found locally
        return pd.DataFrame()

    # A. Basic Cleanup
    df = df.dropna(subset=['Ticker'])
    df = df[df['Ticker'] != 'Ticker']
    
    # B. Clean Percentage Columns (Remove % and convert to float)
    cols_to_clean = ['Dividend', 'Expense Ratio', 'Yield']
    for col in cols_to_clean:
        if col in df.columns:
            # Remove '%' and convert to number
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # C. FIX: Clean "Current Price" (Remove $ and convert to float)
    if 'Current Price' in df.columns:
        df['Current Price'] = df['Current Price'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['Current Price'] = pd.to_numeric(df['Current Price'], errors='coerce').fillna(0)

    # D. Clean AUM (Handle B and M)
    def parse_aum(x):
        x = str(x).upper().replace('$', '').replace(',', '')
        if 'M' in x: return float(x.replace('M', '')) * 1_000_000
        if 'B' in x: return float(x.replace('B', '')) * 1_000_000_000
        try: return float(x)
        except: return 0
    
    if 'AUM' in df.columns:
        df['AUM_Numeric'] = df['AUM'].apply(parse_aum)
    
    # E. Ensure Category Exists
    if 'Category' not in df.columns and len(df.columns) >= 16:
        df.rename(columns={df.columns[15]: 'Category'}, inplace=True)
    df['Category'] = df['Category'].fillna('Other').astype(str)
    
    return df

try:
    df = load_data()
    if df.empty:
        st.error("Could not load data. Please check your CSV file.")
        st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- 3. SIDEBAR / FILTER BAR ---
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_input = st.text_input("🔍 Search Ticker, Name, or Strategy", placeholder="e.g. YieldMax, Bitcoin, MSTY...")

with col2:
    all_tags = set()
    for tags in df['Category'].str.split(','):
        for tag in tags:
            clean_tag = tag.strip()
            if clean_tag: all_tags.add(clean_tag)
    selected_strategies = st.multiselect("Filter by Strategy", sorted(list(all_tags)))

with col3:
    if 'Payout' in df.columns:
        freq_options = df['Payout'].dropna().unique().tolist()
        selected_freq = st.multiselect("Payout Frequency", sorted(freq_options))
    else:
        selected_freq = []

col4, col5 = st.columns([1, 1])
with col4:
    min_yield = st.slider("Minimum Yield %", 0, 150, 0, 5)
with col5:
    if 'Company' in df.columns:
        all_issuers = sorted(df['Company'].dropna().unique().tolist())
        selected_issuer = st.multiselect("Issuer / Company", all_issuers)
    else:
        selected_issuer = []

# --- 4. FILTERING ---
filtered = df.copy()

if search_input:
    filtered = filtered[
        filtered['Ticker'].str.contains(search_input, case=False, na=False) |
        filtered['Strategy'].str.contains(search_input, case=False, na=False) |
        filtered['Category'].str.contains(search_input, case=False, na=False)
    ]

if selected_strategies:
    pattern = '|'.join(selected_strategies)
    filtered = filtered[filtered['Category'].str.contains(pattern, case=False, regex=True)]

if selected_freq:
    filtered = filtered[filtered['Payout'].isin(selected_freq)]

if selected_issuer:
    filtered = filtered[filtered['Company'].isin(selected_issuer)]

if 'Dividend' in df.columns:
    filtered = filtered[filtered['Dividend'] >= min_yield]

# --- 5. DISPLAY RESULTS ---
st.divider()

# A. DRILL DOWN
if not filtered.empty:
    fund_list = ["Select a Fund..."] + sorted(filtered['Ticker'].unique().tolist())
    selected_fund = st.selectbox("Inspect a specific fund (View Details):", fund_list)

    if selected_fund != "Select a Fund...":
        row = filtered[filtered['Ticker'] == selected_fund].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Price", f"${row.get('Current Price', 0):.2f}")
        c2.metric("Yield", f"{row.get('Dividend', 0)}%")
        c3.metric("Freq", row.get('Payout', '-'))
        c4.metric("Fee", f"{row.get('Expense Ratio', 0)}%")
        
        st.info(f"**Strategy:** {row.get('Strategy', 'No description')}")
        st.caption(f"**Category Tags:** {row.get('Category')}")
        st.divider()

# B. MAIN TABLE
cols_to_show = ['Ticker', 'Current Price', 'Dividend', 'Payout', 'Pay Date', 'Company', 'Category']
final_cols = [c for c in cols_to_show if c in filtered.columns]

st.markdown(f"**Showing {len(filtered)} Funds**")

# SAFE DISPLAY (Prevents Formatting Errors)
if not filtered.empty:
    st.dataframe(
        filtered[final_cols].style.format({
            'Dividend': '{:.2f}%',
            'Current Price': '${:.2f}'
        }),
        height=500,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No funds match your search.")
