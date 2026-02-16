import streamlit as st
import pandas as pd

# 1. PAGE CONFIGURATION (Bloomberg Style Title)
st.set_page_config(
    page_title="RIR Master List",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CUSTOM CSS FOR "BLOOMBERG TERMINAL" AESTHETIC
# This makes the app dark, high-contrast, and removes default Streamlit padding for a 'widget' feel.
st.markdown("""
    <style>
        /* Main Background */
        .stApp {
            background-color: #0e1117;
            color: #ff9f1c; /* Retail Investor Report Orange accent */
        }
        /* Dataframe styling */
        .stDataFrame {
            border: 1px solid #333;
        }
        /* Inputs and Text */
        p, .stTextInput label, .stMultiSelect label, .stSlider label {
            color: #e0e0e0 !important;
            font-family: 'Roboto Mono', monospace;
        }
        /* Hide Streamlit Header/Footer for clean embed */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# 3. DATA LOADING & CLEANING FUNCTION
@st.cache_data
def load_data():
    # Load the CSV - Ensure this filename matches your uploaded file in GitHub
    df = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vTKjBzr7QuJk9g7TR6p0-_GdPQDvesG9a1KTny6y5IyK0Z-G0_C98T-AfUyaAdyDB11h3vdpgc_h3Hh/pub?gid=618318322&single=true&output=csv")
    
    # Clean up 'Header' rows that might exist in the middle of the CSV
    df = df.dropna(subset=['Ticker'])
    df = df[df['Ticker'] != 'Ticker'] # Remove repeated headers if any

    # --- Data Cleaning Logic ---
    
    # 1. Clean Percentage Columns (Dividend, Payout, etc.)
    cols_to_clean_pct = ['Dividend', 'Payout', 'Expense Ratio']
    for col in cols_to_clean_pct:
        if col in df.columns:
            # Remove %, convert to float
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 2. Clean Currency/AUM Columns
    # Function to convert "$3.95M" or "$8.63B" to actual numbers
    def parse_aum(x):
        x = str(x).upper().replace('$', '').replace(',', '')
        if 'M' in x:
            return float(x.replace('M', '')) * 1_000_000
        elif 'B' in x:
            return float(x.replace('B', '')) * 1_000_000_000
        try:
            return float(x)
        except:
            return 0

    if 'AUM' in df.columns:
        df['AUM_Numeric'] = df['AUM'].apply(parse_aum)

    return df

df = load_data()

# 4. SEARCH & FILTER BAR (Layout)
# We use columns to create a single horizontal "Bar" feel
col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1.5])

with col1:
    # Universal Search Bar
    search_query = st.text_input("🔍 Search Ticker or Name", placeholder="e.g. NVDY, YieldMax...")

with col2:
    # Filter by Underlying (SPY, QQQ, BTC, etc.)
    underlying_options = sorted(df['Underlying'].dropna().unique().tolist())
    selected_underlying = st.multiselect("Underlying Asset", underlying_options)

with col3:
    # Filter by Company (Issuer)
    company_options = sorted(df['Company'].dropna().unique().tolist())
    selected_company = st.multiselect("Issuer", company_options)

with col4:
    # Filter by Yield %
    min_yield = st.number_input("Min Yield %", min_value=0.0, max_value=200.0, value=10.0, step=5.0)

# 5. FILTERING LOGIC
filtered_df = df.copy()

# Apply Text Search
if search_query:
    filtered_df = filtered_df[
        filtered_df['Ticker'].str.contains(search_query, case=False, na=False) |
        filtered_df['Strategy'].str.contains(search_query, case=False, na=False)
    ]

# Apply Underlying Filter
if selected_underlying:
    filtered_df = filtered_df[filtered_df['Underlying'].isin(selected_underlying)]

# Apply Company Filter
if selected_company:
    filtered_df = filtered_df[filtered_df['Company'].isin(selected_company)]

# Apply Yield Filter
if 'Dividend' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Dividend'] >= min_yield]

# 6. DISPLAY DATA
# Customize which columns to show in the final table
display_cols = [
    'Ticker', 'Current Price', 'Dividend', 'Pay Date', 
    'AUM', 'Company', 'Underlying', 'Strategy'
]

# Formatting for display (Add % back visually, but keep data numeric for sorting)
st.dataframe(
    filtered_df[display_cols].style.format({
        'Dividend': '{:.2f}%',
        'Current Price': '${:.2f}',
    }),
    hide_index=True,
    use_container_width=True,
    height=500 # Fixed height for scrollable area
)
