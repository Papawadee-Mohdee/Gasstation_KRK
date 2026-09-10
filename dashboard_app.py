from datetime import datetime
import os
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & MODERN SAAS LIGHT UI CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Executive Operations Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Sarabun:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Sarabun', -apple-system, sans-serif !important;
    }
    
    .stApp {
        background-color: #F3F4F6;
        color: #1F2937;
    }
    
    /* SIDEBAR STYLING LIKE IMAGE */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB !important;
        padding-top: 1rem;
    }
    
    /* PROFILE AVATAR CONTAINER */
    .profile-container {
        text-align: center;
        padding: 1rem 0 1.5rem 0;
    }
    
    .profile-avatar {
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        color: #FFFFFF;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        position: relative;
    }

    .profile-badge {
        position: absolute;
        top: 2px;
        right: 2px;
        width: 14px;
        height: 14px;
        background-color: #10B981;
        border: 2px solid #FFFFFF;
        border-radius: 50%;
    }

    .profile-name {
        font-size: 0.95rem;
        font-weight: 700;
        color: #111827;
        margin-top: 0.6rem;
    }

    .profile-role {
        font-size: 0.75rem;
        color: #6B7280;
    }

    /* CUSTOM NAVIGATION RADIO BUTTONS */
    div[data-testid="stSidebarUserContent"] .stRadio > label {
        display: none;
    }
    
    div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] {
        gap: 6px;
    }

    div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] label {
        background-color: transparent !important;
        border-radius: 12px !important;
        padding: 0.6rem 1rem !important;
        color: #4B5563 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        border: none !important;
        transition: all 0.2s ease;
    }

    div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] label[data-checked="true"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }

    /* CARD DESIGN */
    .dashboard-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        margin-bottom: 1rem;
    }

    .card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #2563EB;
        margin-bottom: 0.5rem;
    }

    .metric-card-light {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 1.25rem;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }

    .metric-label-light {
        font-size: 0.75rem;
        font-weight: 700;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-value-light {
        font-size: 1.6rem;
        font-weight: 800;
        color: #111827;
        margin-top: 0.25rem;
    }

    .insight-pill {
        background-color: #EFF6FF;
        border-left: 4px solid #2563EB;
        border-radius: 0 8px 8px 0;
        padding: 0.5rem 0.75rem;
        font-size: 0.83rem;
        color: #1E40AF;
        margin-bottom: 1rem;
        font-weight: 500;
    }

    /* TABS STYLING */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #E5E7EB;
        padding-bottom: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 10px;
        font-size: 0.875rem;
        font-weight: 600;
        color: #6B7280 !important;
        background-color: transparent;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    /* LOGOUT BUTTON */
    .logout-btn {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E5E7EB;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# DATABASE ENGINE & CONNECTION MANAGEMENT
# -----------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent if CURRENT_DIR.name == "pages" else CURRENT_DIR

candidate_db_paths = [
    PROJECT_ROOT / "Gasstation_dw_duckdb" / "dev.duckdb",
    PROJECT_ROOT / "dev.duckdb",
    Path.cwd() / "Gasstation_dw_duckdb" / "dev.duckdb",
    Path.cwd() / "dev.duckdb",
]

DB_PATH = None
for candidate in candidate_db_paths:
    if candidate.exists():
        DB_PATH = candidate
        break

@st.cache_resource
def get_db_connection():
    if DB_PATH and os.path.exists(DB_PATH):
        try:
            conn = duckdb.connect(str(DB_PATH), read_only=True)
            tbls = [r[0] for r in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()]
            if "fact_sales" in tbls or "dim_date" in tbls:
                return conn, "khorakhung engine"
        except Exception:
            pass

    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE dim_date AS SELECT cast(strftime(d, '%Y%m%d') as int) as date_key, d as full_date, year(d) as year, month(d) as month, strftime(d, '%B') as month_name, dayname(d) as day_name FROM range(date '2024-01-01', date '2024-12-31', interval 1 day) t(d);
        CREATE TABLE dim_time AS SELECT h as time_key, h as hour_24, case when h between 5 and 10 then 'Morning (05-10)' when h between 11 and 13 then 'Midday (11-13)' when h between 14 and 17 then 'Afternoon (14-17)' when h between 18 and 21 then 'Evening (18-21)' else 'Night (22-04)' end as day_part FROM range(0, 24) t(h);
        CREATE TABLE dim_gasstation AS SELECT i as gasstation_key, i as gasstation_id, 'Station ' || i as gasstation_name, 'Region ' || ((i%3)+1) as address FROM range(1, 11) t(i);
        CREATE TABLE dim_product AS SELECT i as product_key, i as product_id, case when i=1 then 'RON95' when i=2 then 'E5 RON92' else 'Diesel' end as product_name FROM range(1, 4) t(i);
        CREATE TABLE dim_customer AS SELECT i as customer_key, i as customer_id, 'Customer ' || i as customer_name, case when i%2=0 then 'Sedan' else 'SUV' end as vehicle_type FROM range(1, 101) t(i);
        CREATE TABLE dim_employee AS SELECT i as employee_key, i as employee_id, 'Employee ' || i as employee_name FROM range(1, 21) t(i);
        CREATE TABLE dim_paymentmethod AS SELECT 1 as paymentmethod_key, 'Cash' as payment_method UNION SELECT 2, 'Credit Card' UNION SELECT 3, 'QR PromptPay';
        CREATE TABLE dim_tank AS SELECT i as tank_key, i as tank_id, (i%10)+1 as gasstation_id, 'Tank ' || i as tank_name, 20000 as capacity_liters FROM range(1, 31) t(i);
        CREATE TABLE fact_sales AS SELECT 20240101 + (i%30) as date_key, (i%24) as time_key, (i%100)+1 as customer_key, (i%20)+1 as employee_key, (i%10)+1 as gasstation_key, (i%3)+1 as product_key, (i%3)+1 as paymentmethod_key, i as invoice_id, i as invoice_detail_id, 40.0 as quantity_sold, 35000.0 as selling_price, 1400000.0 as total_price FROM range(1, 1000) t(i);
        CREATE TABLE fact_inventory AS SELECT 20240101 + (i%30) as date_key, (i%24) as time_key, (i%30)+1 as tank_key, (i%10)+1 as gasstation_key, i as transaction_id, case when i%5=0 then 5000.0 else 0.0 end as quantity_in, 50.0 as quantity_out, (15000 - (i%1000)) as remaining_quantity FROM range(1, 1000) t(i);
    """)
    return conn, "khorakhung engine (Simulation)"

conn, engine_info = get_db_connection()

@st.cache_data(ttl=600)
def fetch_sales_data():
    try:
        query = """
            SELECT 
                fs.invoice_id, d.full_date, d.year, d.month_name, t.time_key as hour_24, t.day_part,
                g.gasstation_name, g.address as station_address, p.product_name,
                c.customer_name, c.vehicle_type, e.employee_name, pm.payment_method,
                fs.quantity_sold, fs.selling_price, fs.total_price
            FROM fact_sales fs
            LEFT JOIN dim_date d ON fs.date_key = d.date_key
            LEFT JOIN dim_time t ON fs.time_key = t.time_key
            LEFT JOIN dim_gasstation g ON fs.gasstation_key = g.gasstation_key
            LEFT JOIN dim_product p ON fs.product_key = p.product_key
            LEFT JOIN dim_customer c ON fs.customer_key = c.customer_key
            LEFT JOIN dim_employee e ON fs.employee_key = e.employee_key
            LEFT JOIN dim_paymentmethod pm ON fs.paymentmethod_key = pm.paymentmethod_key
        """
        df = conn.execute(query).fetch_df()
        if not df.empty:
            df["full_date"] = pd.to_datetime(df["full_date"])
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def fetch_inventory_data():
    try:
        query = """
            SELECT 
                fi.transaction_id, d.full_date, g.gasstation_name, tk.tank_name,
                tk.capacity_liters, fi.quantity_in, fi.quantity_out, fi.remaining_quantity
            FROM fact_inventory fi
            LEFT JOIN dim_date d ON fi.date_key = d.date_key
            LEFT JOIN dim_gasstation g ON fi.gasstation_key = g.gasstation_key
            LEFT JOIN dim_tank tk ON fi.tank_key = tk.tank_key
        """
        df = conn.execute(query).fetch_df()
        if not df.empty:
            df["full_date"] = pd.to_datetime(df["full_date"])
        return df
    except Exception:
        return pd.DataFrame()

df_sales = fetch_sales_data()
df_inv = fetch_inventory_data()

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & USER PROFILE
# -----------------------------------------------------------------------------
with st.sidebar:
    # 1. Profile Avatar Header
    st.markdown("""
        <div class="profile-container">
            <div class="profile-avatar">
                👤
                <div class="profile-badge"></div>
            </div>
            <div class="profile-name">Executive Admin</div>
            <div class="profile-role">GasStation Management</div>
        </div>
    """, unsafe_allow_html=True)

    # 2. Sidebar Navigation Menu
    nav_option = st.radio(
        "Navigation",
        options=["🏠 Home", "📊 Dashboard", "👤 Admin", "💬 Messages", "⚙️ Settings"],
        index=1
    )

    st.markdown("---")

    # 3. Dynamic Controls Filter (When on Dashboard)
    if "Dashboard" in nav_option:
        st.markdown("#### Filter Controls")
        if not df_sales.empty and "full_date" in df_sales.columns and df_sales["full_date"].notna().any():
            min_date = df_sales["full_date"].min().date()
            max_date = df_sales["full_date"].max().date()
            date_range = st.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
            
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_date, end_date = date_range
                df_sales = df_sales[(df_sales["full_date"].dt.date >= start_date) & (df_sales["full_date"].dt.date <= end_date)]
                if not df_inv.empty:
                    df_inv = df_inv[(df_inv["full_date"].dt.date >= start_date) & (df_inv["full_date"].dt.date <= end_date)]

        stations = sorted(df_sales["gasstation_name"].dropna().unique()) if not df_sales.empty else []
        sel_stations = st.multiselect("Branch Filter", stations, default=stations)
        if sel_stations:
            df_sales = df_sales[df_sales["gasstation_name"].isin(sel_stations)]
            if not df_inv.empty:
                df_inv = df_inv[df_inv["gasstation_name"].isin(sel_stations)]

        st.markdown("---")

    # 4. Footer & Logout
    st.caption(f"Engine: {engine_info}")
    st.caption(f"Status: Online ({datetime.now().strftime('%H:%M:%S')})")
    
    st.markdown('<div class="logout-btn"></div>', unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.toast("Logging out...", icon="🔒")

# -----------------------------------------------------------------------------
# MAIN CONTENT ROUTING
# -----------------------------------------------------------------------------
def apply_corporate_layout(fig):
    fig.update_layout(
        height=310,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#4B5563", family="Plus Jakarta Sans"),
        xaxis=dict(gridcolor="#F3F4F6", zerolinecolor="#E5E7EB"),
        yaxis=dict(gridcolor="#F3F4F6", zerolinecolor="#E5E7EB"),
        margin=dict(l=15, r=15, t=15, b=15)
    )
    return fig

# -----------------------------------------------------------------------------
# VIEW 1: HOME PANEL
# -----------------------------------------------------------------------------
if "Home" in nav_option:
    st.title("🏠 Overview Portal")
    st.subheader("Welcome to GasStation Enterprise Analytics")
    
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown("""
            <div class="dashboard-card">
                <div class="card-title">System Architecture & Status</div>
                <p style="color: #4B5563; line-height: 1.6;">
                    ระบบบริหารจัดการและวิเคราะห์คลังน้ำมันเชิงพาณิชย์ พัฒนาด้วยเทคโนโลยี Data Warehouse สถาปัตยกรรม Star Schema ร่วมกับฐานข้อมูล High-Performance DuckDB Engine 
                </p>
                <hr style="border:0; border-top: 1px solid #F3F4F6; margin: 1rem 0;">
                <div style="display: flex; gap: 20px;">
                    <div><b>Target DW:</b> Gasstation_dw_duckdb</div>
                    <div><b>Schema:</b> main</div>
                    <div><b>Status:</b> Active</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col_h2:
        st.markdown("""
            <div class="dashboard-card">
                <div class="card-title">Quick Actions</div>
                <p>เลือกเมนู <b>📊 Dashboard</b> ทางซ้ายมือเพื่อดูรายงานและวิเคราะห์ข้อมูลเชิงลึก</p>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW 2: DASHBOARD PANEL (OLAP ANALYTICS)
# -----------------------------------------------------------------------------
elif "Dashboard" in nav_option:
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <h1 style="font-size: 1.8rem; font-weight: 800; color: #111827; margin:0;">Dashboard Analytics</h1>
                <p style="color: #6B7280; margin:0; font-size:0.9rem;">Executive Analytics & OLAP Data Warehouse Overview</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Sales & Revenue (Q1-Q5)",
        "Inventory Operations (Q6-Q10)",
        "Staff & Customers (Q11-Q15)",
        "Ad-Hoc OLAP Explorer"
    ])

    # --- TAB 1: SALES & REVENUE ---
    with tab1:
        tot_rev = df_sales["total_price"].sum() if not df_sales.empty else 0
        tot_qty = df_sales["quantity_sold"].sum() if not df_sales.empty else 0
        tot_orders = df_sales["invoice_id"].nunique() if not df_sales.empty else 0
        avg_ticket = tot_rev / tot_orders if tot_orders > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="metric-card-light"><div class="metric-label-light">Total Revenue</div><div class="metric-value-light">{tot_rev:,.0f} ₫</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="metric-card-light"><div class="metric-label-light">Volume Sold</div><div class="metric-value-light">{tot_qty:,.1f} L</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="metric-card-light"><div class="metric-label-light">Invoices Count</div><div class="metric-value-light">{tot_orders:,}</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="metric-card-light"><div class="metric-label-light">Avg Ticket Size</div><div class="metric-value-light">{avg_ticket:,.0f} ₫</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("""
                <div class="dashboard-card">
                    <div class="card-title">คำถามที่ 1: ยอดขายรวมและรายได้สุทธิของแต่ละสาขาเป็นอย่างไร?</div>
                </div>
            """, unsafe_allow_html=True)
            rev_branch = df_sales.groupby("gasstation_name")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
            if not rev_branch.empty:
                top_b = rev_branch.sort_values(by="total_price", ascending=False).iloc[0]
                st.markdown(f'<div class="insight-pill">Executive Summary: สาขาที่มีรายได้สูงสุดคือ <b>{top_b["gasstation_name"]}</b> (<b>{top_b["total_price"]:,.0f} ₫</b>)</div>', unsafe_allow_html=True)
                
                fig_q1 = px.bar(rev_branch, x="gasstation_name", y="total_price", text_auto=".2s", labels={"gasstation_name": "Branch", "total_price": "Revenue (VND)"})
                fig_q1.update_traces(marker_color='#2563EB', hovertemplate="Branch: %{x}<br>Revenue: %{y:,.0f} ₫")
                fig_q1 = apply_corporate_layout(fig_q1)
                st.plotly_chart(fig_q1, use_container_width=True)

        with c2:
            st.markdown("""
                <div class="dashboard-card">
                    <div class="card-title">คำถามที่ 2: สินค้าประเภทน้ำมันชนิดใดทำรายได้สูงสุด?</div>
                </div>
            """, unsafe_allow_html=True)
            rev_prod = df_sales.groupby("product_name")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
            if not rev_prod.empty:
                top_p = rev_prod.sort_values(by="total_price", ascending=False).iloc[0]
                st.markdown(f'<div class="insight-pill">Executive Summary: ผลิตภัณฑ์หลักทำรายได้คือ <b>{top_p["product_name"]}</b></div>', unsafe_allow_html=True)
                
                fig_q2 = px.pie(rev_prod, names="product_name", values="total_price", hole=0.5, color_discrete_sequence=['#2563EB', '#3B82F6', '#60A5FA', '#93C5FD'])
                fig_q2.update_traces(hovertemplate="Product: %{label}<br>Revenue: %{value:,.0f} ₫<br>Share: %{percent}")
                fig_q2 = apply_corporate_layout(fig_q2)
                st.plotly_chart(fig_q2, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("""
                <div class="dashboard-card">
                    <div class="card-title">คำถามที่ 3: ช่วงเวลา Peak Hours ของการใช้บริการ?</div>
                </div>
            """, unsafe_allow_html=True)
            rev_hour = df_sales.groupby("hour_24")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
            if not rev_hour.empty:
                peak_h = rev_hour.sort_values(by="total_price", ascending=False).iloc[0]
                st.markdown(f'<div class="insight-pill">Executive Summary: Peak Hour อยู่ในช่วงเวลา <b>{int(peak_h["hour_24"]):02d}:00 น.</b></div>', unsafe_allow_html=True)
                
                fig_q3 = px.line(rev_hour, x="hour_24", y="total_price", markers=True, labels={"hour_24": "Hour", "total_price": "Revenue (VND)"})
                fig_q3.update_traces(line_color='#2563EB', hovertemplate="Hour: %{x}:00<br>Revenue: %{y:,.0f} ₫")
                fig_q3 = apply_corporate_layout(fig_q3)
                st.plotly_chart(fig_q3, use_container_width=True)

        with c4:
            st.markdown("""
                <div class="dashboard-card">
                    <div class="card-title">คำถามที่ 4: สัดส่วนช่องทางการชำระเงิน?</div>
                </div>
            """, unsafe_allow_html=True)
            rev_pm = df_sales.groupby("payment_method")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
            if not rev_pm.empty:
                top_pm = rev_pm.sort_values(by="total_price", ascending=False).iloc[0]
                st.markdown(f'<div class="insight-pill">Executive Summary: ช่องทางยอดนิยมคือ <b>{top_pm["payment_method"]}</b></div>', unsafe_allow_html=True)
                
                fig_q4 = px.bar(rev_pm, x="total_price", y="payment_method", orientation="h", text_auto=".2s", labels={"total_price": "Revenue (VND)", "payment_method": "Method"})
                fig_q4.update_traces(marker_color='#3B82F6', hovertemplate="Method: %{y}<br>Revenue: %{x:,.0f} ₫")
                fig_q4 = apply_corporate_layout(fig_q4)
                st.plotly_chart(fig_q4, use_container_width=True)

    # --- TAB 2: INVENTORY OPERATIONS ---
    with tab2:
        if not df_inv.empty:
            i1, i2, i3 = st.columns(3)
            i1.markdown(f'<div class="metric-card-light"><div class="metric-label-light">Refill Inflow</div><div class="metric-value-light">{df_inv["quantity_in"].sum():,.0f} L</div></div>', unsafe_allow_html=True)
            i2.markdown(f'<div class="metric-card-light"><div class="metric-label-light">Dispensed Outflow</div><div class="metric-value-light">{df_inv["quantity_out"].sum():,.0f} L</div></div>', unsafe_allow_html=True)
            i3.markdown(f'<div class="metric-card-light"><div class="metric-label-light">Current Stock Tank</div><div class="metric-value-light">{df_inv.groupby("tank_name")["remaining_quantity"].last().sum():,.0f} L</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_inv1, col_inv2 = st.columns(2)

            with col_inv1:
                st.markdown("""
                    <div class="dashboard-card">
                        <div class="card-title">คำถามที่ 6 & 8: ปริมาณน้ำมันคงเหลือในถังจัดเก็บแต่ละถัง?</div>
                    </div>
                """, unsafe_allow_html=True)
                tank_status = df_inv.groupby(["gasstation_name", "tank_name"])["remaining_quantity"].last().reset_index()
                fig_q6 = px.bar(tank_status, x="tank_name", y="remaining_quantity", color="gasstation_name", color_discrete_sequence=['#2563EB', '#3B82F6', '#60A5FA'])
                fig_q6 = apply_corporate_layout(fig_q6)
                st.plotly_chart(fig_q6, use_container_width=True)

            with col_inv2:
                st.markdown("""
                    <div class="dashboard-card">
                        <div class="card-title">คำถามที่ 7, 9 & 10: สัดส่วนการรับน้ำมันเข้า (Inflow) รายสาขา?</div>
                    </div>
                """, unsafe_allow_html=True)
                refill_branch = df_inv.groupby("gasstation_name")["quantity_in"].sum().reset_index()
                fig_q9 = px.pie(refill_branch, names="gasstation_name", values="quantity_in", hole=0.4, color_discrete_sequence=['#2563EB', '#3B82F6', '#60A5FA', '#93C5FD'])
                fig_q9 = apply_corporate_layout(fig_q9)
                st.plotly_chart(fig_q9, use_container_width=True)

    # --- TAB 3: STAFF & CUSTOMERS ---
    with tab3:
        e1, e2 = st.columns(2)

        with e1:
            st.markdown("""
                <div class="dashboard-card">
                    <div class="card-title">คำถามที่ 11 & 12: พนักงานที่ทำยอดขายสูงสุด?</div>
                </div>
            """, unsafe_allow_html=True)
            emp_rev = df_sales.groupby(["employee_name", "gasstation_name"])["total_price"].sum().reset_index().sort_values(by="total_price", ascending=False).head(10) if not df_sales.empty else pd.DataFrame()
            if not emp_rev.empty:
                fig_q11 = px.bar(emp_rev, x="total_price", y="employee_name", color="gasstation_name", orientation="h", text_auto=".2s", color_discrete_sequence=['#2563EB', '#3B82F6'])
                fig_q11 = apply_corporate_layout(fig_q11)
                st.plotly_chart(fig_q11, use_container_width=True)

        with e2:
            st.markdown("""
                <div class="dashboard-card">
                    <div class="card-title">คำถามที่ 13: ประเภทยานพาหนะของลูกค้าที่ใช้บริการมากที่สุด?</div>
                </div>
            """, unsafe_allow_html=True)
            veh_dist = df_sales.groupby("vehicle_type")["invoice_id"].nunique().reset_index() if not df_sales.empty else pd.DataFrame()
            if not veh_dist.empty:
                fig_q13 = px.bar(veh_dist, x="vehicle_type", y="invoice_id", text_auto="d")
                fig_q13.update_traces(marker_color='#2563EB')
                fig_q13 = apply_corporate_layout(fig_q13)
                st.plotly_chart(fig_q13, use_container_width=True)

    # --- TAB 4: AD-HOC OLAP EXPLORER ---
    with tab4:
        st.markdown("### Ad-Hoc Multi-Dimensional OLAP Cube Explorer")
        st.caption("เครื่องมือสไลซ์และวิเคราะห์มิติข้อมูลอิสระสำหรับการตัดสินใจเชิงบริหาร")

        if not df_sales.empty:
            o_col1, o_col2, o_col3, o_col4 = st.columns(4)
            dim_options = ["gasstation_name", "product_name", "payment_method", "vehicle_type", "employee_name", "day_part"]

            with o_col1:
                x_dim = st.selectbox("Primary X-Axis", dim_options, index=0)
            with o_col2:
                legend_dim = st.selectbox("Sub-Group Dimension", ["None"] + dim_options, index=1)
            with o_col3:
                metric_choice = st.selectbox("Metric", ["Revenue (total_price)", "Volume Sold (quantity_sold)"], index=0)
            with o_col4:
                chart_style = st.selectbox("Chart Style", ["Bar Chart", "Line Chart", "Treemap"], index=0)

            y_col = "total_price" if "Revenue" in metric_choice else "quantity_sold"
            group_cols = [x_dim] if (legend_dim == "None" or legend_dim == x_dim) else [x_dim, legend_dim]
            color_arg = None if (legend_dim == "None" or legend_dim == x_dim) else legend_dim
            
            df_olap = df_sales.groupby(group_cols, as_index=False)[y_col].sum()
            
            if chart_style == "Bar Chart":
                fig_custom = px.bar(df_olap, x=x_dim, y=y_col, color=color_arg, barmode="group", text_auto=".2s", color_discrete_sequence=['#2563EB', '#3B82F6', '#60A5FA'])
            elif chart_style == "Line Chart":
                fig_custom = px.line(df_olap, x=x_dim, y=y_col, color=color_arg, markers=True, color_discrete_sequence=['#2563EB', '#3B82F6', '#60A5FA'])
            else:
                fig_custom = px.treemap(df_olap, path=group_cols, values=y_col)

            fig_custom = apply_corporate_layout(fig_custom)
            st.plotly_chart(fig_custom, use_container_width=True)
            
            st.dataframe(df_olap, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# VIEW 3: ADMIN PANEL
# -----------------------------------------------------------------------------
elif "Admin" in nav_option:
    st.title("👤 Administrator Control Center")
    st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">User & Permission Management</div>
            <p>จัดการสิทธิ์การเข้าถึงข้อมูลของผู้ใช้งานและจัดการการเชื่อมต่อ DuckDB Database Engine</p>
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW 4: MESSAGES PANEL
# -----------------------------------------------------------------------------
elif "Messages" in nav_option:
    st.title("💬 System Messages & Notifications")
    st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">Recent System Alerts</div>
            <ul>
                <li><b>System:</b> Data Warehouse refreshed successfully at 08:00 AM</li>
                <li><b>Alert:</b> Station 3 stock level reached refill threshold</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW 5: SETTINGS PANEL
# -----------------------------------------------------------------------------
elif "Settings" in nav_option:
    st.title("⚙️ System Configuration")
    st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">Preferences</div>
            <p>ตั้งค่าสภาพแวดล้อมระบบและการเชื่อมต่อฐานข้อมูล Data Warehouse</p>
        </div>
    """, unsafe_allow_html=True)