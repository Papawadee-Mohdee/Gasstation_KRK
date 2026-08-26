import os
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & ENTERPRISE DESIGN SYSTEM (NO EMOJIS)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="GasStation Executive Analytics Studio",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B !important;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #E2E8F0 !important;
        font-weight: 500 !important;
    }

    .app-header {
        border-bottom: 1px solid #1E293B;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .app-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.025em;
    }
    
    .app-subtitle {
        font-size: 0.875rem;
        color: #94A3B8;
        margin-top: 0.2rem;
    }

    .question-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    
    .question-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #38BDF8;
        margin-bottom: 0.5rem;
        letter-spacing: -0.01em;
    }

    .metric-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }
    
    .metric-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #FFFFFF;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 0.25rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 6px;
        font-size: 0.875rem;
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
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# DATABASE ENGINE & CONNECTION MANAGEMENT
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "Gasstation_dw_duckdb" / "dev.duckdb"

@st.cache_resource
def get_db_connection():
    if os.path.exists(DB_PATH):
        try:
            conn = duckdb.connect(str(DB_PATH), read_only=True)
            tbls = [r[0] for r in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()]
            if "fact_sales" in tbls:
                return conn, f"DuckDB Engine ({DB_PATH.name})"
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
        CREATE TABLE fact_sales AS SELECT 20240101 + (i%30) as date_key, (i%24) as time_key, (i%100)+1 as customer_key, (i%20)+1 as employee_key, (i%10)+1 as gasstation_key, (i%3)+1 as product_key, (i%3)+1 as paymentmethod_key, i as invoice_id, i as invoice_detail_id, 40.0 as quantity_sold, 35.0 as selling_price, 1400.0 as total_price FROM range(1, 1000) t(i);
        CREATE TABLE fact_inventory AS SELECT 20240101 + (i%30) as date_key, (i%24) as time_key, (i%30)+1 as tank_key, (i%10)+1 as gasstation_key, i as transaction_id, case when i%5=0 then 5000.0 else 0.0 end as quantity_in, 50.0 as quantity_out, (15000 - (i%1000)) as remaining_quantity FROM range(1, 1000) t(i);
    """)
    return conn, "In-Memory Driver"

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
# APPLICATION HEADER
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="app-header">
        <div class="app-title">GasStation OLAP Analytics Dashboard</div>
        <div class="app-subtitle">Data Warehouse: Gasstation_dw_duckdb &nbsp;|&nbsp; Target Schema: main</div>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Controls")
    
    if not df_sales.empty and "full_date" in df_sales.columns and df_sales["full_date"].notna().any():
        min_date = df_sales["full_date"].min().date()
        max_date = df_sales["full_date"].max().date()
        date_range = st.date_input("Date Range Filter", [min_date, max_date], min_value=min_date, max_value=max_date)
        
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range
            df_sales = df_sales[(df_sales["full_date"].dt.date >= start_date) & (df_sales["full_date"].dt.date <= end_date)]
            if not df_inv.empty:
                df_inv = df_inv[(df_inv["full_date"].dt.date >= start_date) & (df_inv["full_date"].dt.date <= end_date)]

    stations = sorted(df_sales["gasstation_name"].dropna().unique()) if not df_sales.empty else []
    sel_stations = st.multiselect("Gas Station Branch Filter", stations, default=stations)
    if sel_stations:
        df_sales = df_sales[df_sales["gasstation_name"].isin(sel_stations)]
        if not df_inv.empty:
            df_inv = df_inv[df_inv["gasstation_name"].isin(sel_stations)]

    st.markdown("---")
    st.caption(f"Engine: {engine_info}")

# -----------------------------------------------------------------------------
# MAIN DASHBOARD TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Sales & Revenue Analytics (Q1-Q5)",
    "Inventory Operations (Q6-Q10)",
    "Staff & Customer Intelligence (Q11-Q15)",
    "Ad-Hoc OLAP Explorer"
])

# -----------------------------------------------------------------------------
# TAB 1: SALES & REVENUE (QUESTIONS 1 - 5)
# -----------------------------------------------------------------------------
with tab1:
    tot_rev = df_sales["total_price"].sum() if not df_sales.empty else 0
    tot_qty = df_sales["quantity_sold"].sum() if not df_sales.empty else 0
    tot_orders = df_sales["invoice_id"].nunique() if not df_sales.empty else 0
    avg_ticket = tot_rev / tot_orders if tot_orders > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="metric-box"><div class="metric-label">Total Revenue</div><div class="metric-value">฿{tot_rev:,.2f}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="metric-box"><div class="metric-label">Volume Sold</div><div class="metric-value">{tot_qty:,.1f} L</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="metric-box"><div class="metric-label">Invoices Count</div><div class="metric-value">{tot_orders:,}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="metric-box"><div class="metric-label">Avg Ticket Size</div><div class="metric-value">฿{avg_ticket:,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 1: ยอดขายรวมและรายได้สุทธิของแต่ละสาขาเป็นอย่างไรในแต่ละช่วงเวลา?</div>
            </div>
        """, unsafe_allow_html=True)
        rev_branch = df_sales.groupby("gasstation_name")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
        if not rev_branch.empty:
            fig_q1 = px.bar(rev_branch, x="gasstation_name", y="total_price", text_auto=".2s", labels={"gasstation_name": "Branch", "total_price": "Revenue (THB)"})
            fig_q1.update_traces(marker_color='#38BDF8')
            fig_q1.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q1, use_container_width=True)

    with c2:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 2: สินค้าประเภทน้ำมันชนิดใดทำรายได้สูงสุด?</div>
            </div>
        """, unsafe_allow_html=True)
        rev_prod = df_sales.groupby("product_name")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
        if not rev_prod.empty:
            fig_q2 = px.pie(rev_prod, names="product_name", values="total_price", hole=0.4, color_discrete_sequence=['#38BDF8', '#818CF8', '#34D399'])
            fig_q2.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 3: ช่วงเวลาใดของวันที่ลูกค้าเข้าใช้บริการมากที่สุด (Peak Hours)?</div>
            </div>
        """, unsafe_allow_html=True)
        rev_hour = df_sales.groupby("hour_24")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
        if not rev_hour.empty:
            fig_q3 = px.line(rev_hour, x="hour_24", y="total_price", markers=True, labels={"hour_24": "Hour (0-23)", "total_price": "Revenue (THB)"})
            fig_q3.update_traces(line_color='#38BDF8')
            fig_q3.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q3, use_container_width=True)

    with c4:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 4: ยอดขายจำแนกตามช่องทางการชำระเงินมีสัดส่วนอย่างไร?</div>
            </div>
        """, unsafe_allow_html=True)
        rev_pm = df_sales.groupby("payment_method")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
        if not rev_pm.empty:
            fig_q4 = px.bar(rev_pm, x="total_price", y="payment_method", orientation="h", text_auto=".2s", labels={"total_price": "Revenue (THB)", "payment_method": "Method"})
            fig_q4.update_traces(marker_color='#818CF8')
            fig_q4.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q4, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: INVENTORY OPERATIONS (QUESTIONS 6 - 10)
# -----------------------------------------------------------------------------
with tab2:
    if not df_inv.empty:
        i1, i2, i3 = st.columns(3)
        i1.markdown(f'<div class="metric-box"><div class="metric-label">Total Refill Inflow</div><div class="metric-value">{df_inv["quantity_in"].sum():,.0f} L</div></div>', unsafe_allow_html=True)
        i2.markdown(f'<div class="metric-box"><div class="metric-label">Total Dispensed Outflow</div><div class="metric-value">{df_inv["quantity_out"].sum():,.0f} L</div></div>', unsafe_allow_html=True)
        i3.markdown(f'<div class="metric-box"><div class="metric-label">Current Tank Inventory</div><div class="metric-value">{df_inv.groupby("tank_name")["remaining_quantity"].last().sum():,.0f} L</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_inv1, col_inv2 = st.columns(2)

        with col_inv1:
            st.markdown("""
                <div class="question-card">
                    <div class="question-title">คำถามที่ 6 & 8: ปริมาณน้ำมันคงเหลือในถังจัดเก็บแต่ละถัง ณ ปัจจุบัน และอัตราหมุนเวียน?</div>
                </div>
            """, unsafe_allow_html=True)
            tank_status = df_inv.groupby(["gasstation_name", "tank_name"])["remaining_quantity"].last().reset_index()
            fig_q6 = px.bar(tank_status, x="tank_name", y="remaining_quantity", color="gasstation_name", labels={"remaining_quantity": "Remaining Stock (L)", "tank_name": "Tank"})
            fig_q6.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q6, use_container_width=True)

        with col_inv2:
            st.markdown("""
                <div class="question-card">
                    <div class="question-title">คำถามที่ 7, 9 & 10: สัดส่วนการรับน้ำมันเข้า (Inflow) และจ่ายออก (Outflow) แต่ละสาขา?</div>
                </div>
            """, unsafe_allow_html=True)
            refill_branch = df_inv.groupby("gasstation_name")["quantity_in"].sum().reset_index()
            fig_q9 = px.pie(refill_branch, names="gasstation_name", values="quantity_in", hole=0.3)
            fig_q9.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q9, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: STAFF & CUSTOMER INTELLIGENCE (QUESTIONS 11 - 15)
# -----------------------------------------------------------------------------
with tab3:
    e1, e2 = st.columns(2)

    with e1:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 11 & 12: พนักงานคนใดทำยอดขายรวมได้สูงสุด และยอดขายเฉลี่ยรายสาขา?</div>
            </div>
        """, unsafe_allow_html=True)
        emp_rev = df_sales.groupby(["employee_name", "gasstation_name"])["total_price"].sum().reset_index().sort_values(by="total_price", ascending=False).head(10) if not df_sales.empty else pd.DataFrame()
        if not emp_rev.empty:
            fig_q11 = px.bar(emp_rev, x="total_price", y="employee_name", color="gasstation_name", orientation="h", text_auto=".2s", labels={"total_price": "Revenue (THB)", "employee_name": "Employee"})
            fig_q11.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q11, use_container_width=True)

    with e2:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 13: กลุ่มประเภทยานพาหนะของลูกค้ากลุ่มใดเข้ามาใช้บริการมากที่สุด?</div>
            </div>
        """, unsafe_allow_html=True)
        veh_dist = df_sales.groupby("vehicle_type")["invoice_id"].nunique().reset_index() if not df_sales.empty else pd.DataFrame()
        if not veh_dist.empty:
            fig_q13 = px.bar(veh_dist, x="vehicle_type", y="invoice_id", text_auto="d", labels={"invoice_id": "Visits", "vehicle_type": "Vehicle Type"})
            fig_q13.update_traces(marker_color='#38BDF8')
            fig_q13.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q13, use_container_width=True)

    e3, e4 = st.columns(2)
    with e3:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 14: ลูกค้าประจำสร้างสัดส่วนรายได้คิดเป็นกี่เปอร์เซ็นต์ (Top Customer Spend)?</div>
            </div>
        """, unsafe_allow_html=True)
        cust_rev = df_sales.groupby("customer_name")["total_price"].sum().reset_index().sort_values(by="total_price", ascending=False).head(10) if not df_sales.empty else pd.DataFrame()
        if not cust_rev.empty:
            fig_q14 = px.bar(cust_rev, x="customer_name", y="total_price", text_auto=".2s", labels={"customer_name": "Customer", "total_price": "Revenue (THB)"})
            fig_q14.update_traces(marker_color='#818CF8')
            fig_q14.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q14, use_container_width=True)

    with e4:
        st.markdown("""
            <div class="question-card">
                <div class="question-title">คำถามที่ 15: การกระจายตัวของลูกค้าในแต่ละภูมิภาคสร้างยอดขายแตกต่างกันอย่างไร?</div>
            </div>
        """, unsafe_allow_html=True)
        geo_rev = df_sales.groupby("station_address")["total_price"].sum().reset_index() if not df_sales.empty else pd.DataFrame()
        if not geo_rev.empty:
            fig_q15 = px.pie(geo_rev, names="station_address", values="total_price", hole=0.3)
            fig_q15.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
            st.plotly_chart(fig_q15, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: AD-HOC OLAP EXPLORER
# -----------------------------------------------------------------------------
with tab4:
    st.markdown("### Ad-Hoc Multi-Dimensional OLAP Cube Builder")
    st.caption("Slice-and-Dice across custom dimensions for ad-hoc business exploration beyond predefined questions.")

    if not df_sales.empty:
        o_col1, o_col2, o_col3, o_col4 = st.columns(4)
        dim_options = ["gasstation_name", "product_name", "payment_method", "vehicle_type", "employee_name", "day_part"]

        with o_col1:
            x_dim = st.selectbox("Primary X-Axis Dimension", dim_options, index=0)
        with o_col2:
            legend_dim = st.selectbox("Sub-Group Dimension", ["None"] + dim_options, index=1)
        with o_col3:
            metric_choice = st.selectbox("Aggregation Metric", ["Revenue (total_price)", "Volume Sold (quantity_sold)"], index=0)
        with o_col4:
            chart_style = st.selectbox("Chart Style", ["Bar Chart", "Line Chart", "Treemap"], index=0)

        y_col = "total_price" if "Revenue" in metric_choice else "quantity_sold"
        
        # Duplicate GroupBy Column Protection
        if legend_dim == "None" or legend_dim == x_dim:
            group_cols = [x_dim]
            color_arg = None
        else:
            group_cols = [x_dim, legend_dim]
            color_arg = legend_dim
        
        df_olap = df_sales.groupby(group_cols, as_index=False)[y_col].sum()
        
        if chart_style == "Bar Chart":
            fig_custom = px.bar(df_olap, x=x_dim, y=y_col, color=color_arg, barmode="group", text_auto=".2s")
        elif chart_style == "Line Chart":
            fig_custom = px.line(df_olap, x=x_dim, y=y_col, color=color_arg, markers=True)
        else:
            fig_custom = px.treemap(df_olap, path=group_cols, values=y_col)

        fig_custom.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
        st.plotly_chart(fig_custom, use_container_width=True)
        
        with st.expander("View Data Matrix Table"):
            st.dataframe(df_olap, use_container_width=True, hide_index=True)