import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RIR Search", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS (YOUR COLOR SCHEME) ---
st.markdown("""
    <style>
        /* 1. MAIN BACKGROUND (Core) */
        .stApp {
            background-color: #0D1117;
        }

        /* 2. HIDE DEFAULT LABELS (The text above the bars) */
        label {
            display: none !important;
        }

        /* 3. INPUT BOX STYLING (Tertiary BG, Primary Text) */
        .stTextInput input, .stMultiSelect, div[data-baseweb="select"] > div {
            background-color: #1E293B !important;
            color: #E6EDF3 !important;
            border: 1px solid #30363d;
            border-radius: 8px;
        }
        
        /* 4. TEXT COLORS & ACCENTS */
        p, .stMarkdown {
            color: #E6EDF3; 
        }
        /* The Placeholder Text (Secondary Color) */
        ::placeholder {
            color: #FFFFFF !important;
            opacity: 0.7;
        }
        /* Dropdown Options Text */
        li {
            color: #0D1117 !important; /* Dark text on white dropdown standard */
        }
        
        /* 5. METRICS & DATAFRAME */
        div[data-testid="stMetric"] {
            background-color: #1E293B;
            border: 1px solid #30363d;
            border-radius: 6px;
        }
        div[data-testid="stMetricLabel"] {color: #8AC7DE !important;} /* Accent */
        div[data-testid="stMetricValue"] {color: #FFFFFF !important;}

        /* Hide Header/Footer for clean embed */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            max-width: 1200px;
        }
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

# --- 4. COMPACT SEARCH UI ---

# ROW 1: Main Search (Takes full width visually)
# We use an empty label "" because CSS hides it anyway
search_input = st.text_input("", placeholder="🔍 Search Ticker, Strategy, Company (e.g. NVDY, Bitcoin)...")

# ROW 2: The 3 Optional Filters side-by-side
col1, col2, col3 = st.columns(3)

with col1:
    # Strategy Filter
    all_tags = set()
    for tags in df['Category'].str.split(','):
        for tag in tags:
            if tag.strip(): all_tags.add(tag.strip())
    
    selected_strategies = st.multiselect("", options=sorted(list(all_tags)), placeholder="Filter by Strategy (Optional)")

with col2:
    # Frequency Filter
    freq_opts = sorted(df['Payout'].unique().tolist())
    selected_freq = st.multiselect("", options=freq_opts, placeholder="Payout Freq. (Optional)")

with col3:
    # Min Yield Filter (Using Text Input to act like a search box for clean look)
    # User types "10" or "50"
    yield_input = st.text_input("", placeholder="Min Yield % (e.g. 20)")


# --- 5. FILTER LOGIC & RESULTS ---

# Check if user has interacted with anything
has_search = bool(search_input)
has_strat = bool(selected_strategies)
has_freq = bool(selected_freq)
has_yield = bool(yield_input)

# Only run filter logic if at least one input is active
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

    # 4. Yield (Convert text input to number safely)
    if has_yield:
        try:
            min_val = float(yield_input.replace('%', ''))
            if 'Dividend' in filtered.columns:
                filtered = filtered[filtered['Dividend'] >= min_val]
        except:
            pass # Ignore invalid text input

    # --- DISPLAY RESULTS ---
    if not filtered.empty:
        st.markdown(f"**Found {len(filtered)} Funds**")
        
        # Define Columns to Show
        cols = ['Ticker', 'Current Price', 'Dividend', 'Payout', 'Pay Date', 'Strategy', 'Category']
        final_cols = [c for c in cols if c in filtered.columns]

        # Styled Dataframe
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
        st.info("No funds match your criteria.")

else:
    # State when app loads (Empty / Waiting)
    st.caption("Start typing or select a filter to see results.")
