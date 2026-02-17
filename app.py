import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RIR Search", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
        /* MAIN BACKGROUND */
        .stApp {
            background-color: #0D1117;
            color: #E6EDF3;
        }
        
        /* Reduce global padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        header {visibility: hidden !important; height: 0 !important;}
        footer {visibility: hidden !important;}
        
        /* INPUTS & DROPDOWNS - uniform height and styling */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] {
            background-color: #1E293B !important;
            border-color: #30363d !important;
            color: #ffffff !important;           /* Pure white text */
            border-radius: 6px !important;
            min-height: 48px !important;          /* Same height for all */
            height: 48px !important;
            font-size: 16px !important;
            font-weight: normal !important;       /* Not bold */
            line-height: 1.5 !important;
            padding: 0 12px !important;
        }
        
        /* Make sure text input matches exactly */
        .stTextInput > div > div > input {
            height: 48px !important;
            min-height: 48px !important;
            color: #ffffff !important;
            font-weight: normal !important;
            font-size: 16px !important;
            background-color: transparent !important;
        }
        
        /* Fix blurry text - better contrast + crisp rendering */
        input, div[data-baseweb="select"] div, .stTextInput input {
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
            text-rendering: optimizeLegibility !important;
        }
        
        /* Placeholder styling */
        ::placeholder {
            color: #94A3B8 !important;
            opacity: 1 !important;
            font-weight: normal !important;
        }
        
        /* Dropdown menu items */
        ul[role="listbox"] li, div[data-baseweb="menu"] li {
            font-size: 16px !important;
            color: #E6EDF3 !important;
        }
        
        /* Slider styling */
        div[data-testid="stSlider"] {
            background-color: #1E293B;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 12px;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        div[data-testid="stSlider"] label {
            display: block !important;
            color: #E6EDF3 !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            margin-bottom: 6px !important;
        }
        
        /* Table styling */
        div[data-testid="stDataFrame"] {
            background-color: #0D1117 !important;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow: hidden;
        }
        
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #1E293B !important;
            color: #8AC7DE !important;
            font-weight: bold;
            border-bottom: 1px solid #30363d;
            padding: 12px !important;
        }
        
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            background-color: #0D1117 !important;
            color: #E6EDF3 !important;
            border-bottom: 1px solid #30363d;
            padding: 10px !important;
        }
        
        /* Reduce gaps */
        .row-widget.stTextInput { margin-bottom: -8px !important; }
        .stMultiSelect { margin-top: 0 !important; margin-bottom: 0 !important; }
        .element-container { margin: 0 !important; padding: 0 !important; }
        .stHorizontalBlock > div { margin-top: 0 !important; padding-top: 0 !important; }
        
        /* Tighter layout overall */
        .st-emotion-cache-ocqkz7 { gap: 0.5rem !important; }
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

# --- 4. LAYOUT ---
left_col, right_col = st.columns([2, 1])

with left_col:
    st.text_input("", placeholder="🔍 Search any Ticker, Strategy, Company or Underlying...", key="search_term")
   
    c1, c2 = st.columns(2)
    with c1:
        all_tags = set()
        if 'Category' in df.columns:
            for tags in df['Category'].str.split(','):
                for tag in tags:
                    if tag.strip() and tag.strip() != '-': all_tags.add(tag.strip())
        selected_strategies = st.multiselect("", options=sorted(list(all_tags)), placeholder="📊 Filter by Strategy")
    with c2:
        freq_opts = sorted(df['Payout'].unique().tolist())
        selected_freq = st.multiselect("", options=freq_opts, placeholder="⏰ Payout Frequency")

with right_col:
    yield_range = st.slider("💰 Search by Annualized Yield %", 0, 150, (0, 150))

# --- 5. LOGIC & DISPLAY ---
search_input = st.session_state.get("search_term", "")
has_search = bool(search_input.strip())
has_strat = bool(selected_strategies)
has_freq = bool(selected_freq)
has_yield = yield_range[0] > 0 or yield_range[1] < 150

# Only show table if at least one filter/search is active
if has_search or has_strat or has_freq or has_yield:
    filtered = df.copy()
    
    if has_search:
        term = search_input.lower().strip()
        filtered = filtered[
            filtered['Ticker'].str.lower().str.contains(term) |
            filtered['Strategy'].str.lower().str.contains(term) |
            filtered['Company'].str.lower().str.contains(term) |
            filtered['Category'].str.lower().str.contains(term) |
            filtered['Underlying'].str.lower().str.contains(term)
        ]
    
    if has_strat:
        for strat in selected_strategies:
            filtered = filtered[filtered['Category'].str.contains(strat, case=False)]
    
    if has_freq:
        filtered = filtered[filtered['Payout'].isin(selected_freq)]
    
    if has_yield and 'Dividend' in filtered.columns:
        filtered = filtered[(filtered['Dividend'] >= yield_range[0]) & (filtered['Dividend'] <= yield_range[1])]
    
    if not filtered.empty:
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
       
        if 'Yield %' in display_df.columns:
            display_df = display_df.sort_values(by='Yield %', ascending=False)
       
        num_rows = len(display_df)
        dynamic_height = min((num_rows * 36) + 50, 700)
        
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
