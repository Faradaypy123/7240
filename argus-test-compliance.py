import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# --- SYSTEM CONFIG (Hardcoded Paths Maintained) ---
DB_PATH = 'c:/Users/lenovo/Downloads/cleaned_compliance_data.csv'

st.set_page_config(page_title="StandardOS | Elite Production", layout="wide")

# Institutional Styling for Stability & Beauty
st.markdown("""
    <style>
    /* Prevent layout shifting & jumpy filters */
    .stMultiSelect div[data-baseweb="tag"] { transition: none !important; animation: none !important; }
    
    /* Clean UI Blocks */
    .main-container { background: #ffffff; }
    .status-bar { 
        background: #f8fafc; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0; 
        margin-bottom: 20px;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }
    .status-item { text-align: center; }
    .status-item b { font-size: 1.2rem; color: #1e293b; }
    
    .stButton>button { border-radius: 6px; transition: all 0.1s; border: 1px solid #e2e8f0; }
    .header-style { font-weight: 700; color: #64748b; font-size: 0.75rem; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- REFRESH-STABLE DATA ENGINE ---
if 'df' not in st.session_state:
    try:
        st.session_state.df = pd.read_csv(DB_PATH)
    except:
        st.session_state.df = pd.DataFrame(columns=['IS Code', 'Test', 'Status'])

# Tracking selected items for multi-delete
if 'selected_indices' not in st.session_state:
    st.session_state.selected_indices = set()

def commit_changes():
    st.session_state.df.to_csv(DB_PATH, index=False)

# --- GLOBAL FILTERS (Fixed Jumpy Logic) ---
all_codes = sorted(st.session_state.df['IS Code'].unique().tolist())
all_statuses = ["Feasible", "Awaited", "Unfeasible"]

# Use keys to ensure Streamlit tracks the widget state across reruns without "jumping"
st.sidebar.title("StandardOS v10")
mode = st.sidebar.radio("Navigation", ["Active Controller", "Intelligence Map"])

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
        st.session_state.clear() # Hard reset session to kill jumpy tiles
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# --- FILTER APPLICATION ---
filtered_df = st.session_state.df.copy()
filtered_df = filtered_df[filtered_df['IS Code'].isin(f_std) & filtered_df['Status'].isin(f_stat)]

if f_common and len(f_std) > 1:
    sets = [set(st.session_state.df[st.session_state.df['IS Code'] == s]['Test']) for s in f_std]
    common = set.intersection(*sets) if sets else set()
    filtered_df = filtered_df[filtered_df['Test'].isin(common)]

# --- MODULE 1: ACTIVE CONTROLLER ---
if mode == "Active Controller":
    st.header("⚙️ Active Controller")

    # TOP DASHBOARD: COUNTER & BULK ACTIONS
    c_m1, c_m2, c_m3 = st.columns([2, 2, 2])
    c_m1.markdown(f"<div class='status-item'><small>VIEWING</small><br><b>{len(filtered_df)}</b> Tests</div>", unsafe_allow_html=True)
    
    with c_m2:
        if st.button(f"🗑️ Delete All {len(filtered_df)} Filtered", type="secondary"):
            st.session_state.df = st.session_state.df.drop(filtered_df.index).reset_index(drop=True)
            commit_changes(); st.rerun()

    with c_m3:
        # Multi-Select Delete Feature
        num_sel = len(st.session_state.selected_indices)
        if st.button(f"🗑️ Delete Selected ({num_sel})", type="primary" if num_sel > 0 else "secondary", disabled=num_sel==0):
            st.session_state.df = st.session_state.df.drop(list(st.session_state.selected_indices)).reset_index(drop=True)
            st.session_state.selected_indices = set()
            commit_changes(); st.rerun()

    # SMART ADDER
    with st.expander("➕ Add New Standard / Bulk Tests"):
        a1, a2 = st.columns([1, 2])
        with a1:
            add_is = st.selectbox("IS Standard", all_codes + ["+ New"])
            if add_is == "+ New": add_is = st.text_input("Enter Code")
        with a2:
            add_tests = st.text_area("List tests (one per line)")
            if st.button("Inject Records"):
                if add_is and add_tests:
                    new = pd.DataFrame([{"IS Code": add_is, "Test": t.strip(), "Status": "Awaited"} for t in add_tests.split('\n') if t.strip()])
                    st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True).drop_duplicates()
                    commit_changes(); st.rerun()

    st.divider()

    # HEADER
    h = st.columns([0.5, 1.5, 3.5, 3.5, 0.5])
    h[0].write("SEL")
    h[1].markdown("<div class='header-style'>IS Standard</div>", unsafe_allow_html=True)
    h[2].markdown("<div class='header-style'>Test Description</div>", unsafe_allow_html=True)
    h[3].markdown("<div class='header-style'>Status Control</div>", unsafe_allow_html=True)

    # DATA ROWS
    for idx, row in filtered_df.iterrows():
        cols = st.columns([0.5, 1.5, 3.5, 3.5, 0.5])
        
        # Checkbox for multi-select
        is_checked = cols[0].checkbox(" ", key=f"check_{idx}", value=idx in st.session_state.selected_indices)
        if is_checked: st.session_state.selected_indices.add(idx)
        else: st.session_state.selected_indices.discard(idx)

        cols[1].info(f"**{row['IS Code']}**")
        cols[2].write(row['Test'])
        
        b = cols[3].columns(3)
        if b[0].button("Feasible", key=f"f{idx}", type="primary" if row['Status']=="Feasible" else "secondary"):
            st.session_state.df.at[idx, 'Status'] = "Feasible"; commit_changes(); st.rerun()
        if b[1].button("Awaited", key=f"a{idx}", type="primary" if row['Status']=="Awaited" else "secondary"):
            st.session_state.df.at[idx, 'Status'] = "Awaited"; commit_changes(); st.rerun()
        if b[2].button("Unfeasible", key=f"u{idx}", type="primary" if row['Status']=="Unfeasible" else "secondary"):
            st.session_state.df.at[idx, 'Status'] = "Unfeasible"; commit_changes(); st.rerun()
        
        if cols[4].button("🗑️", key=f"del{idx}"):
            st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True); commit_changes(); st.rerun()

# --- MODULE 2: INTELLIGENCE MAP ---
elif mode == "Intelligence Map":
    st.header("🎨 Visual Intelligence Suite")
    
    # Export Section
    e1, e2 = st.columns(2)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    e1.download_button("📥 Download CSV", data=csv, file_name="StandardOS_Report.csv", use_container_width=True)
    
    if not filtered_df.empty:
        is_codes = filtered_df['IS Code'].unique()
        ids = ["Root"] + list(is_codes) + list(filtered_df['IS Code'] + " - " + filtered_df['Test'])
        labels = ["STANDARDS"] + list(is_codes) + list(filtered_df['Test'])
        parents = [""] + ["Root"]*len(is_codes) + list(filtered_df['IS Code'])
        
        scheme = {'Feasible': '#22c55e', 'Unfeasible': '#ef4444', 'Awaited': '#eab308', 'Root': '#ffffff'}
        colors = [scheme['Root']]
        
        for code in is_codes:
            sub = filtered_df[filtered_df['IS Code'] == code]
            score = len(sub[sub['Status'] == 'Feasible']) / len(sub) if len(sub) > 0 else 0
            colors.append('#dcfce7' if score > 0.8 else '#fef9c3' if score > 0.4 else '#fee2e2')
        
        for status in filtered_df['Status']:
            colors.append(scheme.get(status, '#f1f5f9'))

        fig = go.Figure(go.Sunburst(
            ids=ids, labels=labels, parents=parents,
            marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
            branchvalues="total", insidetextorientation='radial'
        ))
        
        fig.update_layout(height=850, margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='white', font=dict(size=14))
        st.plotly_chart(fig, use_container_width=True)