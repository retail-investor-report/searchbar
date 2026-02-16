import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RIR Search", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS (FIXED USING YOUR REFERENCE CODE) ---
st.markdown("""
    <style>
        /* 1. MAIN BACKGROUND */
        .stApp {
            background-color: #0D1117;
            color: #E6EDF3;
        }

        /* 2. HIDE LABELS & SPINNERS */
        label {display: none !important;}
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }

        /* 3. INPUTS & SELECTS - GLOBAL FIX FROM YOUR REFERENCE CODE */
        /* This targets the container of the dropdowns and inputs */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] {
            background-color: #1E293B !important;
            border-color: #30363d !important;
            color: #E6EDF3 !important; /* <--- THE FIX */
            border-radius: 6px !important;
            min-height: 40px !important;
        }

        /* Force text color inside inputs and selects deeper in the structure */
        input { color: #E6EDF3 !important; font-weight: bold !important; }
        div[data-baseweb="select"] div { color: #E6EDF3 !important; } /* <--- THE "SECRET SAUCE" FIX */
        
        /* 4. DROPDOWN MENU (THE POPUP LIST) */
        ul[role="listbox"], div[data-baseweb="menu"] {
            background-color: #1E293B !important;
            border: 1px solid #30363d !important;
        }
        
        /* The options inside the list */
        li[role="option"] {
            color: #E6EDF3 !important;
            background-color: #1E293B !important;
        }
        
        /* Hover / Selected state */
        li[role="option"]:hover, li[role="option"][aria-selected="true"] {
            background-color: #8AC7DE !important;
            color: #0D1117 !important;
            font-weight: bold !important;
        }

        /* 5. MULTI-SELECT TAGS (The Blue Bubbles) */
        .stMultiSelect span[data-baseweb="tag"] {
            background-color: #8AC7DE !important; 
            color: #0D1117 !important;
            font-weight: bold;
        }
        
        /* 6. ICONS (Arrow down etc) */
        .stSelectbox svg, .stMultiSelect svg { fill: #8AC7DE !important; }

        /* 7. PLACEHOLDERS */
        ::placeholder { color: #94A3B8 !important; opacity: 1; }

        /* 8. TABLE STYLING */
        div[data-testid="stDataFrame"] {
            background-color: #0D1117;
            border: none;
        }
        thead tr th {
            background-color: #1E293B !important;
            color: #8AC7DE !important;
            border-bottom: 1px solid #30363d !important;
        }
        tbody tr td {
            background-color: #0D1117 !important;
            color: #E6EDF3 !important;
            border-bottom: 1px solid #30363d !important;
        }
        tbody tr:hover td {
            background-color: #161B22 !important;
        }

        /* 9. CLEANUP & TEXT COLORS */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 0rem; max-width: 1200px;}
        p, .stMarkdown {color: #E6EDF3;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOADING ---
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTKjBzr7QuJk9g7TR6p0-_GdPQDvesG9a1KTny6y5IyK0Z-G0_C98T-AfUyaAdyDB11h3vdpgc_h3Hh/pub?gid=618318322&single=true&output=csv"
    try:
        df = pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

    # Cleaning
    df = df.dropna(subset=['Ticker'])
    df = df[df['Ticker'] != 'Ticker']
    
    # Text Handling
    text_cols = ['Ticker', 'Strategy', 'Company', 'Underlying', 'Payout', 'Category', 'Pay Date']
    for col in text_cols:
        if col in df.columns: df[col] = df[col].fillna('').astype(str)
        else: df[col] = ''

    # Numeric Handling
    for col in ['Dividend', 'Expense Ratio', 'Yield']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'Current Price' in df.columns:
        df['Current Price'] = df['Current Price'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['Current Price'] = pd.to_numeric(df['Current Price'], errors='coerce').fillna(0)
    
    return df

df = load_data()
if df.empty: st.stop()

# --- 4. UI LAYOUT ---

# ROW 1: Main Search
search_input = st.text_input("", placeholder="Search any Ticker, Strategy, Company or Underlying (e.g. NVDY, Bitcoin, 0DTE)...")

# ROW 2: Filters
col1, col2, col3 = st.columns(3)

with col1:
    # Strategy Filter
    all_tags = set()
    for tags in df['Category'].str.split(','):
        for tag in tags:
            if tag.strip(): all_tags.add(tag.strip())
    
    selected_strategies = st.multiselect("", options=sorted(list(all_tags)), placeholder="Filter by Strategy")

with col2:
    # Frequency Filter
    freq_opts = sorted(df['Payout'].unique().tolist())
    selected_freq = st.multiselect("", options=freq_opts, placeholder="Payout Frequency")

with col3:
    # Min Yield Filter (Number Input disguised as Text Box)
    min_yield = st.number_input("", min_value=0.0, max_value=200.0, step=1.0, format="%.0f", placeholder="Min Yield % (Type a number)")


# --- 5. LOGIC & DISPLAY ---

# Trigger Logic: Only show if user does something
has_search = bool(search_input)
has_strat = bool(selected_strategies)
has_freq = bool(selected_freq)
has_yield = min_yield > 0

if has_search or has_strat or has_freq or has_yield:
    
    filtered = df.copy()

    # 1. Search
    if has_search:
        term = search_input.lower()
        filtered = filtered[
            filtered['Ticker'].str.lower().str.contains(term) |
            filtered['Strategy'].str.lower().str.contains(term) |
            filtered['Company'].str.lower().str.contains(term) |
            filtered['Category'].str.lower().str.contains(term) |
            filtered['Underlying'].str.lower().str.contains(term)
        ]

    # 2. Strategy
    if has_strat:
        pattern = '|'.join(selected_strategies)
        filtered = filtered[filtered['Category'].str.contains(pattern, case=False, regex=True)]

    # 3. Frequency
    if has_freq:
        filtered = filtered[filtered['Payout'].isin(selected_freq)]

    # 4. Yield
    if has_yield and 'Dividend' in filtered.columns:
        filtered = filtered[filtered['Dividend'] >= min_yield]

    # --- DISPLAY TABLE ---
    if not filtered.empty:
        # Define Columns
        cols = ['Ticker', 'Current Price', 'Dividend', 'Payout', 'Pay Date', 'Strategy', 'Category']
        final_cols = [c for c in cols if c in filtered.columns]

        # Calculate Height dynamically (35px per row + 38px buffer)
        # If > 10 rows, cap it at 500px to allow scrolling
        num_rows = len(filtered)
        dynamic_height = min((num_rows * 35) + 38, 500)

        # Render Table
        st.dataframe(
            filtered[final_cols].style.format({
                'Dividend': '{:.2f}%',
                'Current Price': '${:.2f}'
            }),
            height=dynamic_height, 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No funds match your criteria.")
