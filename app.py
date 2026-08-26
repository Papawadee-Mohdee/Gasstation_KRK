import os
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. SYSTEM CONFIG & CUSTOM ENTERPRISE CSS
# ==========================================
st.set_page_config(
    page_title="GasStation Data Warehouse Studio",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #090D16;
        color: #F1F5F9;
    }
    
    /* Hero Header Banner */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #0369A1 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 2rem;
        box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.6);
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(to right, #FFFFFF, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    .hero-sub {
        color: #94A3B8;
        font-size: 1.0rem;
        font-weight: 400;
    }
    .hero-tag {
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }

    /* KPI Cards Styling */
    .kpi-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.25s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.15);
    }
    .kpi-title {
        color: #64748B;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .kpi-value {
        color: #F8FAFC;
        font-size: 2.0rem;
        font-weight: 800;
        margin-top: 0.3rem;
        line-height: 1.2;
    }
    
    /* Streamlit Custom UI Elements Overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        border-radius: 10px;
        font-weight: 600;
        color: #94A3B8;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. AUTO DATA ENGINE & DUCKDB CONNECTION
# ==========================================
DB_PATHS = [
    "Gasstation_dw_duckdb/dev.duckdb",
    "Gasstation_dw_duckdb.duckdb",
    "dev.duckdb"
]

@st.cache_resource
def init_database():
    # 1. เช็กว่ามีไฟล์ DuckDB อยู่จริงหรือไม่
    for path in DB_PATHS:
        if os.path.exists(path):
            return duckdb.connect(path, read_only=True), f"DuckDB ({path})"
            
    # 2. เช็กว่ามีไฟล์ CSV ตระกูล _4.csv ในโฟลเดอร์หรือไม่
    conn = duckdb.connect(":memory:")
    csv_files = {
        "Customer": "Customer_4.csv",
        "Employee": "Employee_4.csv",
        "GasStation": "GasStation_4.csv",
        "Invoice": "Invoice_4.csv",
        "InvoiceDetail": "InvoiceDetail_4.csv",
        "InventoryTransaction": "InventoryTransaction_4.csv",
        "Product": "Product_4.csv",
        "StorageTank": "StorageTank_4.csv"
    }
    
    found_any = False
    for tbl_name, csv_path in csv_files.items():
        if os.path.exists(csv_path):
            conn.execute(f"CREATE TABLE {tbl_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
            found_any = True
            
    if found_any:
        return conn, "Local CSV Engine (_4.csv)"
        
    # 3. สร้าง Mock Engine สำหรับทดสอบทันทีระหว่างรอข้อมูล
    conn.execute("""
        CREATE TABLE Customer AS SELECT i AS CustomerID, 'Customer ' || i AS CustomerName, 'Bangkok' AS Address FROM range(1, 1001) t(i);
        CREATE TABLE Employee AS SELECT i AS EmployeeID, 'Employee ' || i AS EmployeeName, 'Gas Station Attendant' AS Position, (i%10)+1 AS GasStationID FROM range(1, 52) t(i);
        CREATE TABLE GasStation AS SELECT i AS GasStationID, 'GasStation Branch ' || i AS GasStationName FROM range(1, 11) t(i);
        CREATE TABLE StorageTank AS SELECT i AS TankID, (i%10)+1 AS GasStationID, 20000 AS Capacity FROM range(1, 31) t(i);
        CREATE TABLE Product AS SELECT i AS ProductID, case when i=1 then 'RON95-III' when i=2 then 'E5 RON92-II' else 'Diesel' end AS ProductName, 23830.00 AS UnitPrice FROM range(1, 4) t(i);
        CREATE TABLE Invoice AS SELECT i AS InvoiceID, (i%1000)+1 AS CustomerID, (i%51)+1 AS EmployeeID, (i%10)+1 AS GasStationID, CURRENT_TIMESTAMP - INTERVAL (i) MINUTE AS IssueDate, 180000.00 AS TotalAmount FROM range(1, 9674) t(i);
        CREATE TABLE InvoiceDetail AS SELECT i AS InvoiceDetailID, (i%9673)+1 AS InvoiceID, (i%3)+1 AS ProductID, 50.00 AS QuantitySold, 118673.40 AS TotalPrice FROM range(1, 23608) t(i);
        CREATE TABLE InventoryTransaction AS SELECT i AS TransactionID, (i%30)+1 AS TankID, 0.00 AS QuantityIn, 5.00 AS QuantityOut, 15000.00 AS RemainingQuantity FROM range(1, 23612) t(i);
    """)
    return conn, "Simulation Engine (Mock Data)"

conn, engine_status = init_database()

def run_query(query):
    try:
        return conn.execute(query).fetch_df()
    except Exception as e:
        st.error(f"SQL Exception: {e}")
        return pd.DataFrame()

# ==========================================
# 3. HEADER & METRICS SUMMARY
# ==========================================
st.markdown("""
    <div class="hero-container">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div class="hero-title">GasStation Data Warehouse</div>
                <div class="hero-sub">Analytics & Enterprise Staging Environment Explorer</div>
            </div>
            <div>
                <span class="hero-tag">dbt Core: Gasstation_dw_duckdb</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Fetch Metadata
tables_df = run_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name")
tables = tables_df['table_name'].tolist() if not tables_df.empty else []

stats_list = []
for t in tables:
    r_cnt = run_query(f"SELECT COUNT(*) as cnt FROM main.{t}")['cnt'].iloc[0]
    c_cnt = len(run_query(f"PRAGMA table_info('main.{t}')"))
    stats_list.append({"table_name": t, "row_count": r_cnt, "column_count": c_cnt})

stats_df = pd.DataFrame(stats_list)
total_records = stats_df['row_count'].sum() if not stats_df.empty else 0

# Sidebar Control
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/96/gas-station.png", width=55)
    st.title("DW Explorer Panel")
    
    selected_table = st.selectbox("🎯 Select Staging Table", tables if tables else ["None"])
    st.markdown("---")
    
    st.caption("⚡ Engine Status")
    st.info(engine_status)
    
    st.markdown("---")
    preview_limit = st.select_slider("Row Preview Limit", options=[25, 50, 100, 250, 500, 1000], value=100)

# ==========================================
# 4. TAB DASHBOARD
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Executive Analytics", "🔍 Deep Schema & Data Inspector", "⚡ Live SQL Workspace"])

# ------------------------------------------
# TAB 1: EXECUTIVE ANALYTICS
# ------------------------------------------
with tab1:
    st.markdown("### 📌 Warehouse Health & Distribution")
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Entities</div><div class="kpi-value">{len(tables)}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Staged Records</div><div class="kpi-value">{total_records:,}</div></div>', unsafe_allow_html=True)
    with k3:
        top_tbl = stats_df.loc[stats_df['row_count'].idxmax()]['table_name'] if not stats_df.empty else "-"
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Largest Table</div><div class="kpi-value" style="font-size:1.3rem; color:#38BDF8;">{top_tbl}</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Target Schema</div><div class="kpi-value" style="font-size:1.3rem; color:#818CF8;">main</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart, col_side = st.columns([1.5, 1])
    
    with col_chart:
        st.markdown("#### 📈 Record Volume across Staging Tables")
        fig = px.bar(
            stats_df.sort_values(by="row_count", ascending=True),
            x="row_count",
            y="table_name",
            orientation="h",
            text="row_count",
            color="row_count",
            color_continuous_scale="Purples",
            labels={"row_count": "Records Count", "table_name": "Table Name"}
        )
        fig.update_layout(
            height=380,
            margin=dict(l=0, r=20, t=10, b=0),
            showlegend=False,
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8")
        )
        fig.update_traces(texttemplate='%{text:,}', textposition='outside', marker_line_color='rgba(255,255,255,0.1)', marker_line_width=1)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_side:
        st.markdown("#### 📋 Staging Summary Inventory")
        st.dataframe(
            stats_df.rename(columns={"table_name": "Table Name", "row_count": "Row Count", "column_count": "Columns"}),
            use_container_width=True,
            hide_index=True,
            height=380
        )

# ------------------------------------------
# TAB 2: DATA INSPECTOR
# ------------------------------------------
with tab2:
    if selected_table != "None":
        st.markdown(f"### 🔍 Table Profiling: `{selected_table}`")
        
        schema_df = run_query(f"PRAGMA table_info('main.{selected_table}')")
        preview_df = run_query(f"SELECT * FROM main.{selected_table} LIMIT {preview_limit}")
        
        col_main, col_info = st.columns([2.8, 1.2])
        
        with col_main:
            st.markdown(f"#### 📄 Data Preview (Showing top {len(preview_df)} records)")
            
            # Interactive Filter
            search_query = st.text_input("🔎 Filter results in preview:", "")
            if search_query and not preview_df.empty:
                filter_mask = preview_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                preview_df = preview_df[filter_mask]
                
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            
            # CSV Download
            csv_data = preview_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download `{selected_table}` Data (CSV)",
                data=csv_data,
                file_name=f"{selected_table}_export.csv",
                mime="text/csv"
            )
            
        with col_info:
            st.markdown("#### 🛠️ Field Meta & Data Types")
            st.dataframe(
                schema_df[['name', 'type', 'notnull']].rename(columns={"name": "Column Name", "type": "Type", "notnull": "Not Null"}),
                use_container_width=True,
                hide_index=True,
                height=420
            )

# ------------------------------------------
# TAB 3: SQL WORKSPACE
# ------------------------------------------
with tab3:
    st.markdown("### 💻 Custom SQL Query Console")
    st.caption("Write and test DuckDB SQL queries directly against your Data Warehouse staging tables.")
    
    default_sql = f"SELECT * FROM main.{selected_table} LIMIT 20;" if selected_table != "None" else "SELECT 1;"
    user_sql = st.text_area("SQL Editor:", value=default_sql, height=130)
    
    if st.button("🚀 Execute Query", type="primary"):
        if user_sql.strip():
            with st.spinner("Processing query..."):
                query_res = run_query(user_sql)
            if not query_res.empty:
                st.success(f"Execution successful! Fetched {len(query_res):,} records.")
                st.dataframe(query_res, use_container_width=True, hide_index=True)
            else:
                st.info("Query executed cleanly with 0 rows returned.")