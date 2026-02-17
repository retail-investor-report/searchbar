import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RIR Search", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
        /* 1. MAIN BACKGROUND */
        .stApp {
            background-color: #0D1117;
            color: #E6EDF3;
        }

        /* 2. HIDE DEFAULT LABELS (Global) */
        label {display: none !important;}

        /* 3. INPUTS & SELECTS (The "Secret Sauce") */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] {
            background-color: #1E293B !important;
            border-color: #30363d !important;
            color: #E6EDF3 !important;
            border-radius: 6px !important;
            min-height: 40px !important;
        }
        
        input { color: #E6EDF3 !important; font-weight: bold !important; }
        div[data-baseweb="select"] div { color: #E6EDF3 !important; }

        /* 4. DROPDOWN MENUS */
        ul[role="listbox"], div[data-baseweb="menu"] {
            background-color: #1E293B !important;
            border: 1px solid #30363d !important;
        }
        li[role="option"] {
            color: #E6EDF3 !important;
            background-color: #1E293B !important;
        }
        li[role="option"]:hover, li[role="option"][aria-selected="true"] {
            background-color: #8AC7DE !important;
            color: #0D1117 !important;
            font-weight: bold !important;
        }

        /* 5. SLIDER STYLING (The Linear Gauge) */
        /* The Text above the slider */
        .slider-label {
            color: #94A3B8;
            font-size: 14px;
            margin-bottom: -10px; /* Pull slider closer to text */
            font-weight: 400;
        }
        /* The Thumb (Draggable Circle) */
        div[role="slider"] {
            background-color: #8AC7DE !important;
            border-color: #8AC7DE !important;
            box-shadow: 0 0 10px rgba(138, 199, 222, 0.3) !important;
        }
        /* The Track (The Line) */
        div[data-baseweb="slider"] div {
            background-color: #30363d !important;
        }
        /* The Value Text (The number that moves) */
        div[data-testid="stMarkdownContainer"] p {
            color: #E6EDF3;
        }

        /* 6. TAGS & ICONS */
        .stMultiSelect span[data-baseweb="tag"] {
            background-color: #8AC7DE !important; 
            color: #0D1117 !important;
            font-weight: bold;
        }
        .stSelectbox svg, .stMultiSelect svg { fill: #8AC7DE !important; }
        ::placeholder { color: #94A3B8 !important; opacity: 1; }

        /* 7. TABLE STYLING */
        div[data-testid="stDataFrame"] {
            background-color: #0D1117 !important;
            border: 1px solid #30363d;
            border-radius: 5px;
        }
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #1E293B !important;
            color: #8AC7DE !important;
            font-weight: bold;
            border-bottom: 1px solid #30363d;
        }
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            background-color: #0D1117 !important;
            color: #E6EDF3 !important;
            border-bottom: 1px solid #30363d;
        }
        div[data-testid="stDataFrame"] div[role="row"]:hover div[role="gridcell"] {
            background-color: #161B22 !important;
        }

        /* Cleanup */
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

    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Ticker'])
    df = df[df['Ticker'] != 'Ticker']
    
    text_cols = ['Ticker', 'Strategy', 'Company', 'Underlying', 'Payout', 'Category', 'Pay Date', 'Declaration Date', 'Ex-Div Date']
    for col in text_cols:
        if col in df.columns: df[col] = df[col].fillna('-').astype(str)
        else: df[col] = '-'

    for col in ['Dividend', 'Current Price', 'Latest Distribution']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace('%', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

df = load_data()
if df.empty: st.stop()

# --- 4. UI LAYOUT ---
search_input = st.text_input("", placeholder="Search any Ticker, Strategy, Company or Underlying (e.g. NVDY, Bitcoin, 0DTE)...")

col1, col2, col3 = st.columns(3)
with col1:
    all_tags = set()
    if 'Category' in df.columns:
        for tags in df['Category'].str.split(','):
            for tag in tags:
                if tag.strip() and tag.strip() != '-': all_tags.add(tag.strip())
    selected_strategies = st.multiselect("", options=sorted(list(all_tags)), placeholder="Filter by Strategy")

with col2:
    freq_opts = sorted(df['Payout'].unique().tolist())
    selected_freq = st.multiselect("", options=freq_opts, placeholder="Payout Frequency")

with col3:
    # Custom HTML Label to simulate the "Placeholder" look
    st.markdown('<p class="slider-label">Minimum Yield % (Drag to filter)</p>', unsafe_allow_html=True)
    # The Slider (Linear Gauge)
    min_yield = st.slider("", min_value=0, max_value=150, value=0, step=1)

# --- 5. LOGIC & DISPLAY ---
has_search = bool(search_input)
has_strat = bool(selected_strategies)
has_freq = bool(selected_freq)
has_yield = min_yield > 0

if has_search or has_strat or has_freq or has_yield:
    filtered = df.copy()

    if has_search:
        term = search_input.lower()
        filtered = filtered[
            filtered['Ticker'].str.lower().str.contains(term) |
            filtered['Strategy'].str.lower().str.contains(term) |
            filtered['Company'].str.lower().str.contains(term) |
            filtered['Category'].str.lower().str.contains(term) |
            filtered['Underlying'].str.lower().str.contains(term)
        ]

    if has_strat:
        pattern = '|'.join(selected_strategies)
        filtered = filtered[filtered['Category'].str.contains(pattern, case=False, regex=True)]

    if has_freq:
        filtered = filtered[filtered['Payout'].isin(selected_freq)]

    if has_yield and 'Dividend' in filtered.columns:
        filtered = filtered[filtered['Dividend'] >= min_yield]

    if not filtered.empty:
        # Prepare Display
        rename_map = {
            'Current Price': 'Price',
            'Dividend': 'Yield %',
            'Latest Distribution': 'Latest Dist',
            'Declaration Date': 'Declaration Date',
            'Ex-Div Date': 'Ex-Div Date',
            'Pay Date': 'Pay Date'
        }
        
        target_order = [
            'Ticker', 'Strategy', 'Underlying', 'Current Price', 'Payout', 
            'Latest Distribution', 'Dividend', 'Declaration Date', 'Ex-Div Date', 'Pay Date'
        ]
        
        existing_cols = [c for c in target_order if c in filtered.columns]
        display_df = filtered[existing_cols].rename(columns=rename_map)

        # Sort by Yield
        if 'Yield %' in display_df.columns:
            display_df = display_df.sort_values(by='Yield %', ascending=False)

        # Dynamic Height
        num_rows = len(display_df)
        dynamic_height = min((num_rows * 35) + 38, 500)

        st.dataframe(
            display_df.style.format({
                'Yield %': '{:.2f}%',
                'Price': '${:.2f}',
                'Latest Dist': '${:.4f}'
            }),
            height=dynamic_height, 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No funds match your criteria.")
