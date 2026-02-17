import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RIR Search", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
        .stApp {
            background-color: #0D1117;
            color: #E6EDF3;
        }
        
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            max-width: 1400px !important;
        }
        
        header, footer { visibility: hidden !important; }
        
        /* Uniform input heights + crisp white text */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div {
            background-color: #1E293B !important;
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
            min-height: 44px !important;
            height: 44px !important;
            color: #ffffff !important;
            font-size: 15px !important;
            font-weight: 400 !important;  /* normal weight, no bold */
        }
        
        /* Text input inner styling */
        .stTextInput input {
            color: #ffffff !important;
            font-weight: 400 !important;
            font-size: 15px !important;
            height: 44px !important;
            padding: 0 12px !important;
            background: transparent !important;
        }
        
        /* Improve text rendering / reduce blur */
        input, div[data-baseweb="select"] div {
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
        }
        
        ::placeholder {
            color: #94A3B8 !important;
            opacity: 1 !important;
            font-weight: 400 !important;
        }
        
        /* Multiselect tags */
        .stMultiSelect span[data-baseweb="tag"] {
            background-color: #8AC7DE !important;
            color: #0D1117 !important;
            font-weight: 500 !important;
        }
        
        /* Slider */
        div[data-testid="stSlider"] {
            background-color: #1E293B;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px 14px;
            min-height: 44px !important;
        }
        
        div[data-testid="stSlider"] label {
            color: #E6EDF3 !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            margin-bottom: 6px !important;
        }
        
        /* Table */
        div[data-testid="stDataFrame"] {
            border: 1px solid #30363d;
            border-radius: 6px;
            background-color: #0D1117 !important;
        }
        
        /* Reduce vertical gaps */
        .element-container { margin: 0 !important; padding: 0 !important; }
        .row-widget.stTextInput { margin-bottom: 4px !important; }
        .stMultiSelect { margin: 4px 0 !important; }
        .st-emotion-cache-ocqkz7 { gap: 0.6rem !important; }
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

# --- 5. FILTER LOGIC & DISPLAY ---
search_input = st.session_state.get("search_term", "")
has_search = bool(search_input.strip())
has_strat = bool(selected_strategies)
has_freq = bool(selected_freq)
has_yield = yield_range != (0, 150)  # only active if changed from default

if has_search or has_strat or has_freq or has_yield:
    filtered = df.copy()
    
    if has_search:
        term = search_input.lower().strip()
        filtered = filtered[
            filtered['Ticker'].str.lower().str.contains(term, na=False) |
            filtered['Strategy'].str.lower().str.contains(term, na=False) |
            filtered['Company'].str.lower().str.contains(term, na=False) |
            filtered['Category'].str.lower().str.contains(term, na=False) |
            filtered['Underlying'].str.lower().str.contains(term, na=False)
        ]
    
    if has_strat:
        for strat in selected_strategies:
            filtered = filtered[filtered['Category'].str.contains(strat, case=False, na=False)]
    
    if has_freq:
        filtered = filtered[filtered['Payout'].isin(selected_freq)]
    
    if has_yield and 'Dividend' in filtered.columns:
        filtered = filtered[(filtered['Dividend'] >= yield_range[0]) & (filtered['Dividend'] <= yield_range[1])]
    
    if not filtered.empty:
        rename_map = {
            'Current Price': 'Price',
            'Dividend': 'Yield %',
            'Latest Distribution': 'Latest Dist',
        }
        target_order = ['Ticker', 'Strategy', 'Underlying', 'Price', 'Payout', 'Latest Dist', 'Yield %', 'Declaration Date', 'Ex-Div Date', 'Pay Date']
        existing_cols = [c for c in target_order if c in filtered.columns or c in rename_map.values()]
        display_df = filtered.rename(columns=rename_map)[[c for c in target_order if c in filtered.columns or c in rename_map]]
        
        if 'Yield %' in display_df.columns:
            display_df = display_df.sort_values(by='Yield %', ascending=False)
        
        num_rows = len(display_df)
        height = min(num_rows * 36 + 50, 700)
        
        st.dataframe(
            display_df.style.format({
                'Yield %': '{:.2f}%',
                'Price': '${:.2f}',
                'Latest Dist': '${:.4f}'
            }),
            height=height,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No matching results.")
