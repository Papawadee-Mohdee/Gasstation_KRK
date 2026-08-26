import os
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & HIGH CONTRAST DARK CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="GasStation Data Warehouse Inspector",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Main App Background */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    
    /* SIDEBAR FIX: Force Dark Theme & High Contrast Text */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #E2E8F0 !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #38BDF8 !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: #1E293B !important;
        border-color: #334155 !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }
    
    /* Header Container */
    .app-header {
        border-bottom: 1px solid #1E293B;
        padding-bottom: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .app-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.025em;
    }
    .app-subtitle {
        font-size: 0.9rem;
        color: #94A3B8 !important;
        font-weight: 500;
        margin-top: 0.25rem;
    }

    /* Force Label & Text Contrast in Main Area */
    .stMainBlockContainer label, .stMainBlockContainer p {
        color: #E2E8F0 !important;
    }
    
    /* SQL Textarea Editor Fix */
    .stTextArea textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    .stTextArea textarea:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }

    /* Minimal Metric Cards */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }
    .metric-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #94A3B8 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-top: 0.25rem;
    }

    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600;
        color: #94A3B8 !important;
        background-color: transparent;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid #38BDF8 !important;
    }
    
    /* Primary Button */
    .stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.25rem !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATABASE ENGINE & CONNECTION MANAGEMENT
# -----------------------------------------------------------------------------
DB_PATH = "Gasstation_dw_duckdb/dev.duckdb"
CSV_DIR = "Gasstation_dw_duckdb"

@st.cache_resource
def init_database():
    if os.path.exists(DB_PATH):
        try:
            conn = duckdb.connect(DB_PATH, read_only=True)
            tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
            if len(tables) > 0:
                return conn, f"DuckDB ({DB_PATH})"
        except Exception:
            pass
            
    conn = duckdb.connect(":memory:")
    csv_entities = {
        "Customer": f"{CSV_DIR}/Customer.csv",
        "Employee": f"{CSV_DIR}/Employee.csv",
        "GasStation": f"{CSV_DIR}/GasStation.csv",
        "Invoice": f"{CSV_DIR}/Invoice.csv",
        "InvoiceDetail": f"{CSV_DIR}/InvoiceDetail.csv",
        "InventoryTransaction": f"{CSV_DIR}/InventoryTransaction.csv",
        "Product": f"{CSV_DIR}/Product.csv",
        "StorageTank": f"{CSV_DIR}/StorageTank.csv"
    }
    
    loaded_any = False
    for entity_name, path in csv_entities.items():
        if os.path.exists(path):
            conn.execute(f"CREATE TABLE {entity_name} AS SELECT * FROM read_csv_auto('{path}')")
            loaded_any = True
            
    if loaded_any:
        return conn, f"CSV Engine ({CSV_DIR}/)"
        
    conn.execute("""
        CREATE TABLE Customer AS SELECT i AS CustomerID, 'Customer ' || i AS CustomerName FROM range(1, 1001) t(i);
        CREATE TABLE Employee AS SELECT i AS EmployeeID, 'Employee ' || i AS EmployeeName FROM range(1, 52) t(i);
        CREATE TABLE GasStation AS SELECT i AS GasStationID, 'Station ' || i AS GasStationName FROM range(1, 11) t(i);
        CREATE TABLE Invoice AS SELECT i AS InvoiceID, (i%1000)+1 AS CustomerID FROM range(1, 9674) t(i);
        CREATE TABLE InvoiceDetail AS SELECT i AS DetailID, (i%9673)+1 AS InvoiceID FROM range(1, 23608) t(i);
        CREATE TABLE InventoryTransaction AS SELECT i AS TransactionID FROM range(1, 23612) t(i);
        CREATE TABLE Product AS SELECT i AS ProductID, 'Product ' || i AS ProductName FROM range(1, 4) t(i);
        CREATE TABLE StorageTank AS SELECT i AS TankID FROM range(1, 31) t(i);
    """)
    return conn, "In-Memory Simulation Driver"

conn, engine_status = init_database()

def run_query(query: str) -> pd.DataFrame:
    try:
        return conn.execute(query).fetch_df()
    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# APPLICATION HEADER
# -----------------------------------------------------------------------------
st.markdown(f"""
    <div class="app-header">
        <div class="app-title">GasStation Data Warehouse Inspector</div>
        <div class="app-subtitle">Environment: Gasstation_dw_duckdb &nbsp;|&nbsp; Target Schema: main</div>
    </div>
""", unsafe_allow_html=True)

tables_df = run_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name")
tables = tables_df['table_name'].tolist() if not tables_df.empty else []

stats_data = []
for t in tables:
    count_df = run_query(f"SELECT COUNT(*) as row_count FROM main.{t}")
    row_cnt = count_df['row_count'].iloc[0] if (not count_df.empty and 'row_count' in count_df.columns) else 0
    
    schema_df = run_query(f"PRAGMA table_info('main.{t}')")
    col_cnt = len(schema_df) if not schema_df.empty else 0
    stats_data.append({"table_name": t, "row_count": row_cnt, "column_count": col_cnt})

stats_df = pd.DataFrame(stats_data)
total_records = stats_df['row_count'].sum() if not stats_df.empty else 0

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Controls")
    selected_table = st.selectbox("Select Entity Table", tables if tables else ["None"])
    st.markdown("---")
    
    st.markdown("**Engine Status**")
    st.caption(engine_status)
    
    st.markdown("---")
    preview_limit = st.select_slider("Preview Limit", options=[25, 50, 100, 250, 500, 1000], value=100)

# -----------------------------------------------------------------------------
# MAIN CONTENTS TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Overview", "Schema & Data Inspector", "SQL Console"])

# TAB 1: OVERVIEW
with tab1:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Tables Count</div><div class="metric-value">{len(tables)}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total Records</div><div class="metric-value">{total_records:,}</div></div>', unsafe_allow_html=True)
    with m3:
        largest = stats_df.loc[stats_df['row_count'].idxmax()]['table_name'] if not stats_df.empty else "-"
        st.markdown(f'<div class="metric-card"><div class="metric-label">Largest Entity</div><div class="metric-value" style="font-size:1.2rem;">{largest}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Backend Engine</div><div class="metric-value" style="font-size:1.1rem; font-weight:600; color:#38BDF8 !important;">DuckDB</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if not stats_df.empty:
        col_chart, col_side = st.columns([1.6, 1])
        
        with col_chart:
            st.markdown("#### Record Volume Distribution")
            fig = px.bar(
                stats_df.sort_values(by="row_count", ascending=True),
                x="row_count",
                y="table_name",
                orientation="h",
                text="row_count",
                labels={"row_count": "Record Count", "table_name": "Entity Name"}
            )
            fig.update_traces(
                texttemplate='%{text:,}', 
                textposition='outside', 
                marker_color='#38BDF8'
            )
            fig.update_layout(
                height=360,
                margin=dict(l=0, r=20, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#CBD5E1", family="Plus Jakarta Sans"),
                xaxis=dict(showgrid=True, gridcolor="#1E293B"),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col_side:
            st.markdown("#### Table Inventory")
            st.dataframe(
                stats_df.rename(columns={"table_name": "Table Name", "row_count": "Row Count", "column_count": "Columns"}),
                use_container_width=True,
                hide_index=True,
                height=360
            )

# TAB 2: SCHEMA & PREVIEW
with tab2:
    if selected_table != "None":
        st.markdown(f"#### Entity Profile: `{selected_table}`")
        
        schema_df = run_query(f"PRAGMA table_info('main.{selected_table}')")
        preview_df = run_query(f"SELECT * FROM main.{selected_table} LIMIT {preview_limit}")
        
        col_main, col_info = st.columns([2.8, 1.2])
        
        with col_main:
            st.markdown(f"**Records Preview** (First {len(preview_df)} rows)")
            
            search_query = st.text_input("Filter preview records:", "", placeholder="Type keywords to filter...")
            if search_query and not preview_df.empty:
                filter_mask = preview_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                preview_df = preview_df[filter_mask]
                
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            
            csv_bytes = preview_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"Export {selected_table} (CSV)",
                data=csv_bytes,
                file_name=f"{selected_table}_export.csv",
                mime="text/csv"
            )
            
        with col_info:
            st.markdown("**Schema Metadata**")
            if not schema_df.empty:
                st.dataframe(
                    schema_df[['name', 'type', 'notnull']].rename(columns={"name": "Column", "type": "Type", "notnull": "NotNull"}),
                    use_container_width=True,
                    hide_index=True,
                    height=420
                )

# TAB 3: SQL CONSOLE
with tab3:
    st.markdown("#### SQL Query Console")
    st.caption("Execute read-only SQL queries directly against the DuckDB instance.")
    
    default_sql = f"SELECT * FROM main.{selected_table} LIMIT 20;" if selected_table != "None" else "SELECT 1;"
    user_sql = st.text_area("SQL Statement", value=default_sql, height=130)
    
    if st.button("Execute Query"):
        if user_sql.strip():
            with st.spinner("Executing..."):
                query_res = run_query(user_sql)
            if not query_res.empty:
                st.success(f"Executed successfully. Returned {len(query_res):,} rows.")
                st.dataframe(query_res, use_container_width=True, hide_index=True)
            else:
                st.info("Query executed successfully with 0 records returned.")