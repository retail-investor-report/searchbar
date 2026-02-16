import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RIR Search", layout="wide", initial_sidebar_state="collapsed")

# --- 2. AGGRESSIVE CUSTOM CSS (THE FIX) ---
st.markdown("""
    <style>
        /* 1. MAIN BACKGROUND */
        .stApp {
            background-color: #0D1117;
        }

        /* 2. FORCE TEXT COLOR IN ALL INPUTS (The Nuclear Fix) */
        /* Targets the actual input box text and placeholder text */
        input, .stTextInput input, .stNumberInput input {
            color: #E6EDF3 !important;
            -webkit-text-fill-color: #E6EDF3 !important;
            caret-color: #E6EDF3 !important; /* The typing cursor */
        }

        /* 3. MULTI-SELECT & DROPDOWN CONTAINERS */
        /* This background color applies to the box you click on */
        .stMultiSelect div[data-baseweb="select"] > div {
            background-color: #1E293B !important;
            border-color: #30363d !important;
            color: #E6EDF3 !important;
        }
        
        /* 4. TEXT INSIDE DROPDOWNS (The "Filter by..." text) */
        /* Forces the text span inside the box to be light */
        .stMultiSelect div[data-baseweb="select"] span {
            color: #E6EDF3 !important;
            -webkit-text-fill-color: #E6EDF3 !important;
            opacity: 1 !important;
        }
        
        /* 5. PLACEHOLDERS (Universal Override) */
        /* This catches any text that is a "placeholder" */
        ::placeholder {
            color: #E6EDF3 !important;
            opacity: 1 !important;
            -webkit-text-fill-color: #E6EDF3 !important;
        }
        
        /* 6. DROPDOWN MENU ITEMS (The pop-up list) */
        ul[data-testid="stSelectboxVirtualDropdown"] {
            background-color: #1E293B !important;
        }
        ul[data-testid="stSelectboxVirtualDropdown"] li {
            background-color: #1E293B !important;
            color: #E6EDF3 !important;
        }
        /* Highlight color when hovering over an option */
        li[role="option"]:hover {
            background-color: #8AC7DE !important;
            color: #0D1117 !important;
        }
        
        /* 7. SELECTED TAGS (The blue bubbles) */
        .stMultiSelect span[data-baseweb="tag"] {
            background-color: #8AC7DE !important; 
            color: #0D1117 !important;
        }
        
        /* 8. TABLE STYLING */
        div[data-testid="stDataFrame"] {background-color: #0D1117; border: none;}
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

        /* CLEANUP: Hide Labels & Spinners */
        label {display: none !important;}
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 0rem; max-width: 1200px;}
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
search_input = st.text_input("Search", placeholder="Search any Ticker, Strategy, Company or Underlying (e.g. NVDY, Bitcoin, 0DTE)...")

# ROW 2: Filters
col1, col2, col3 = st.columns(3)

with col1:
    all_tags = set()
    for tags in df['Category'].str.split(','):
        for tag in tags:
            if tag.strip(): all_tags.add(tag.strip())
    selected_strategies = st.multiselect("Strat", options=sorted(list(all_tags)), placeholder="Filter by Strategy")

with col2:
    freq_opts = sorted(df['Payout'].unique().tolist())
    selected_freq = st.multiselect("Freq", options=freq_opts, placeholder="Payout Frequency")

with col3:
    # We use Number Input but style it like text (no spinners)
    min_yield = st.number_input("Yield", min_value=0.0, max_value=200.0, step=1.0, format="%.0f", placeholder="Min Yield % (Type a number)")


# --- 5. LOGIC & DISPLAY ---

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
        cols = ['Ticker', 'Current Price', 'Dividend', 'Payout', 'Pay Date', 'Strategy', 'Category']
        final_cols = [c for c in cols if c in filtered.columns]

        # Dynamic Height
        num_rows = len(filtered)
        dynamic_height = min((num_rows * 35) + 38, 500)

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
