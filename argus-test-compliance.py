import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# --- SYSTEM CONFIG (Hardcoded Paths Maintained) ---
DB_PATH = 'Complete_Ordered_ISO7240_Test_List (1).csv'

st.set_page_config(page_title="StandardOS | Elite Production", layout="wide")

# Institutional Styling
st.markdown("""
    <style>
    .stMultiSelect div[data-baseweb="tag"] { transition: none !important; animation: none !important; }
    .status-bar { 
        background: #ffffff; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #f1f5f9; 
        margin-bottom: 20px;
        display: flex;
        justify-content: space-around;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .status-item { text-align: center; color: #64748b; }
    .status-item b { font-size: 1.3rem; color: #1e293b; }
    .stButton>button { border-radius: 6px; transition: all 0.1s; border: 1px solid #e2e8f0; }
    .header-style { font-weight: 700; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; }
    .product-card {
        border: 1px solid #f1f5f9;
        border-radius: 15px;
        padding: 15px;
        background: #000000;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- REFRESH-STABLE DATA ENGINE ---
if 'df' not in st.session_state:
    try:
        raw_df = None
        for enc in ['utf-8-sig', 'latin-1', 'cp1252']:
            try:
                raw_df = pd.read_csv(DB_PATH, encoding=enc)
                break
            except: continue
        
        if raw_df is not None:
            rename_map = {'Standard Number': 'IS Code', 'Test Name': 'Test'}
            raw_df.rename(columns=rename_map, inplace=True)
            if not raw_df['IS Code'].astype(str).str.contains('IS').any():
                raw_df['IS Code'] = 'IS/ISO7240-' + raw_df['IS Code'].astype(str)
            stat_map = {'available': 'Feasible', 'unavailable': 'Unfeasible'}
            raw_df['Status'] = raw_df['Status'].astype(str).str.lower().str.strip().map(stat_map).fillna('Awaited')
            st.session_state.df = raw_df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        st.session_state.df = pd.DataFrame(columns=['IS Code', 'Test', 'Status'])

if 'selected_indices' not in st.session_state:
    st.session_state.selected_indices = set()

def commit_changes():
    try:
        st.session_state.df.to_csv(DB_PATH, index=False, encoding='utf-8-sig')
    except PermissionError:
        st.error("🚨 Permission Error: Please close the CSV file in Excel/other apps and try again.")
        st.stop()

PRODUCT_LIST = [
    {"name": "Hybrid Wireless Optical Smoke Sensor", "standards": ["IS/ISO7240-7", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Optical Heat Sensor", "standards": ["IS/ISO7240-5", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Optical Multi Sensor", "standards": ["IS/ISO7240-15", "IS/ISO7240-25"]},
    {"name": "Heat Detector with sounder", "standards": ["IS/ISO7240-5", "IS/ISO7240-3", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Optical Smoke Sensor with Voice & VAD", "standards": ["IS/ISO7240-7", "IS/ISO7240-3", "IS/ISO7240-23", "IS/ISO7240-25"]},
    {"name": "Beam Detector", "standards": ["IS/ISO7240-12", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Translator Module", "standards": ["IS/ISO7240-17", "IS/ISO7240-18", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Expander Module", "standards": ["IS/ISO7240-18", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Single Input Module", "standards": ["IS/ISO7240-18", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Single Output Module", "standards": ["IS/ISO7240-18", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Sounder", "standards": ["IS/ISO7240-18", "IS/ISO7240-25"]},
    {"name": "Hybrid Wireless Manual Call Point", "standards": ["IS/ISO7240-11", "IS/ISO7240-25"]}
]

# --- NAVIGATION ---
mode = st.sidebar.radio("Navigation", ["Active Controller", "Intelligence Map", "Product Portfolio"])

all_codes = sorted(st.session_state.df['IS Code'].unique().tolist())
all_statuses = ["Feasible", "Awaited", "Unfeasible"]

st.markdown("<div class='status-bar'>", unsafe_allow_html=True)
f1, f2, f3, f4 = st.columns([3, 2, 1, 1])

with f1:
    f_std = st.multiselect("Standards", options=all_codes, default=all_codes, key="filter_std")
with f2:
    f_stat = st.multiselect("Status", options=all_statuses, default=all_statuses, key="filter_stat")
with f3:
    f_common = st.checkbox("Common Only", key="filter_common")
with f4:
    if st.button("Clear Filters", use_container_width=True):
        st.session_state.selected_indices = set()
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

mask = (st.session_state.df['IS Code'].isin(f_std)) & (st.session_state.df['Status'].isin(f_stat))
filtered_df = st.session_state.df[mask].copy()

if f_common and len(f_std) > 1:
    sets = [set(st.session_state.df[st.session_state.df['IS Code'] == s]['Test']) for s in f_std]
    common = set.intersection(*sets) if sets else set()
    filtered_df = filtered_df[filtered_df['Test'].isin(common)]

# --- MODULE 1: ACTIVE CONTROLLER ---
if mode == "Active Controller":
    st.header("⚙️ Active Controller")
    c_m1, c_m2, c_m3 = st.columns([2, 2, 2])
    c_m1.markdown(f"<div class='status-item'><small>MATCHES</small><br><b>{len(filtered_df)}</b> Tests</div>", unsafe_allow_html=True)
    
    with c_m2:
        if st.button(f"🗑️ Delete All {len(filtered_df)} Filtered", type="secondary"):
            st.session_state.df = st.session_state.df.drop(filtered_df.index).reset_index(drop=True)
            commit_changes(); st.rerun()

    with c_m3:
        num_sel = len(st.session_state.selected_indices)
        if st.button(f"🗑️ Delete Selected ({num_sel})", type="primary" if num_sel > 0 else "secondary", disabled=num_sel==0):
            st.session_state.df = st.session_state.df.drop(list(st.session_state.selected_indices)).reset_index(drop=True)
            st.session_state.selected_indices = set()
            commit_changes(); st.rerun()

    with st.expander("➕ Add Records"):
        a1, a2 = st.columns([1, 2])
        with a1:
            add_is = st.selectbox("Standard", all_codes + ["+ New"])
            if add_is == "+ New": add_is = st.text_input("Enter Code")
        with a2:
            add_tests = st.text_area("Tests (one per line)")
            if st.button("Inject"):
                if add_is and add_tests:
                    new = pd.DataFrame([{"IS Code": add_is, "Test": t.strip(), "Status": "Awaited"} for t in add_tests.split('\n') if t.strip()])
                    st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True).drop_duplicates()
                    commit_changes(); st.rerun()

    st.divider()
    h = st.columns([0.5, 1.5, 3.5, 3.5, 0.5])
    h[0].write("SEL")
    h[1].markdown("<div class='header-style'>Standard</div>", unsafe_allow_html=True)
    h[2].markdown("<div class='header-style'>Description</div>", unsafe_allow_html=True)
    h[3].markdown("<div class='header-style'>Status Toggle</div>", unsafe_allow_html=True)

    for idx, row in filtered_df.iterrows():
        cols = st.columns([0.5, 1.5, 3.5, 3.5, 0.5])
        if cols[0].checkbox(" ", key=f"ch_{idx}", value=idx in st.session_state.selected_indices):
            st.session_state.selected_indices.add(idx)
        else: st.session_state.selected_indices.discard(idx)

        cols[1].info(f"**{row['IS Code']}**")
        cols[2].write(row['Test'])
        
        b = cols[3].columns(3)
        for i, s in enumerate(all_statuses):
            if b[i].button(s, key=f"{s[0]}_{idx}", type="primary" if row['Status']==s else "secondary"):
                st.session_state.df.at[idx, 'Status'] = s; commit_changes(); st.rerun()
        
        if cols[4].button("🗑️", key=f"del_{idx}"):
            st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
            commit_changes(); st.rerun()

# --- MODULE 2: INTELLIGENCE MAP ---
elif mode == "Intelligence Map":
    st.header("🎨 Visual Intelligence Suite")
    if not filtered_df.empty:
        is_codes = filtered_df['IS Code'].unique()
        ids = ["Root"] + list(is_codes) + list(filtered_df['IS Code'] + " - " + filtered_df['Test'])
        labels = ["STANDARDS"] + list(is_codes) + list(filtered_df['Test'])
        parents = [""] + ["Root"]*len(is_codes) + list(filtered_df['IS Code'])
        
        scheme = {'Feasible': '#000080', 'Unfeasible': '#808080', 'Awaited': '#808080', 'Root': '#000000'}
        colors = [scheme['Root']]
        for code in is_codes:
            sub = filtered_df[filtered_df['IS Code'] == code]
            score = len(sub[sub['Status'] == 'Feasible']) / len(sub) if len(sub) > 0 else 0
            colors.append('#1a1a4d' if score > 0.8 else '#333333' if score > 0.4 else '#4d4d4d')
        for status in filtered_df['Status']: colors.append(scheme.get(status, '#808080'))
        
        fig = go.Figure(go.Sunburst(ids=ids, labels=labels, parents=parents, marker=dict(colors=colors, line=dict(color='#ffffff', width=2)), branchvalues="total", insidetextorientation='radial'))
        # UPDATE: SET TEXT COLOR TO WHITE
        fig.update_layout(height=850, margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='white', font=dict(size=14, color="#FFFFFF"))
        st.plotly_chart(fig, use_container_width=True)

# --- MODULE 3: PRODUCT PORTFOLIO ---
elif mode == "Product Portfolio":
    st.header("📦 Product Portfolio Gallery")
    st.caption("Individual compliance charts for your specific product lineup.")
    
    cols = st.columns(2)
    for i, product in enumerate(PRODUCT_LIST):
        with cols[i % 2]:
            st.markdown(f"<div class='product-card'><b>{product['name']}</b>", unsafe_allow_html=True)
            prod_df = st.session_state.df[st.session_state.df['IS Code'].isin(product["standards"])]
            
            if not prod_df.empty:
                p_ids = [product["name"]] + list(prod_df['IS Code'].unique()) + list(prod_df['IS Code'] + " - " + prod_df['Test'])
                p_labels = [product["name"]] + list(prod_df['IS Code'].unique()) + list(prod_df['Test'])
                p_parents = [""] + [product["name"]] * len(prod_df['IS Code'].unique()) + list(prod_df['IS Code'])
                
                scheme = {'Feasible': '#000080', 'Unfeasible': '#808080', 'Awaited': '#808080', 'Root': '#000000'}
                p_colors = [scheme['Root']]
                for code in prod_df['IS Code'].unique():
                    sub = prod_df[prod_df['IS Code'] == code]
                    score = len(sub[sub['Status'] == 'Feasible']) / len(sub)
                    p_colors.append('#1a1a4d' if score > 0.8 else '#333333' if score > 0.4 else '#4d4d4d')
                for status in prod_df['Status']: p_colors.append(scheme.get(status, '#808080'))
                
                p_fig = go.Figure(go.Sunburst(ids=p_ids, labels=p_labels, parents=p_parents, marker=dict(colors=p_colors, line=dict(color='#ffffff', width=1)), branchvalues="total"))
                # UPDATE: SET TEXT COLOR TO WHITE
                p_fig.update_layout(
                    height=450, 
                    margin=dict(t=0, l=0, r=0, b=0), 
                    font=dict(color="#000000"), # visible text on dark backgrounds
                    annotations=[dict(text='', x=0.5, y=0.5, showarrow=False, font_size=30)]
                )
                st.plotly_chart(p_fig, use_container_width=True, key=f"prod_{i}")
            else:
                st.info("No data found for this product.")
            st.markdown("</div>", unsafe_allow_html=True)
