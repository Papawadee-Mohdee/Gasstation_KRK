from pathlib import Path

import duckdb
import streamlit as st

# ---------------------------------------------------------
# Path
# app.py อยู่ที่ /workspaces/Gasstation_KRK/
# DuckDB อยู่ที่ /workspaces/Gasstation_KRK/Gasstation_dw_duckdb/dev.duckdb
# ---------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "Gasstation_dw_duckdb" / "dev.duckdb"

# ---------------------------------------------------------
# Import dashboard helpers
# รองรับทั้ง Dashboard.py และ dashboard.py
# ---------------------------------------------------------
if (ROOT / "Dashboard.py").exists():
    from Dashboard import (
        TITLES,
        DIMENSIONS,
        PRODUCT_DIMENSIONS,
        question_query,
        explore_query,
    )
elif (ROOT / "dashboard.py").exists():
    from dashboard import (
        TITLES,
        DIMENSIONS,
        PRODUCT_DIMENSIONS,
        question_query,
        explore_query,
    )
else:
    st.error(
        "ไม่พบไฟล์ Dashboard.py หรือ dashboard.py ในโฟลเดอร์เดียวกับ app.py"
    )
    st.code(str(ROOT), language="text")
    st.stop()


# ---------------------------------------------------------
# Streamlit config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Gas Station Dim Fact",
    layout="wide",
)

st.title("วิเคราะห์สถานีบริการน้ำมันจาก Dim และ Fact")


# ---------------------------------------------------------
# ตรวจสอบฐานข้อมูล
# ---------------------------------------------------------
if not DB_PATH.exists():
    st.error(f"ไม่พบฐานข้อมูล: {DB_PATH}")
    st.info(
        "ให้เข้าโฟลเดอร์ Gasstation_dw_duckdb แล้วรัน `dbt run` "
        "ให้สำเร็จก่อนเปิด Dashboard"
    )
    st.stop()


# ---------------------------------------------------------
# เชื่อมต่อ DuckDB
# ---------------------------------------------------------
with duckdb.connect(str(DB_PATH), read_only=True) as con:

    # -----------------------------------------------------
    # ช่วงวันที่จาก fact_invoices
    # -----------------------------------------------------
    lo, hi = con.execute(
        """
        select
            min(issue_timestamp)::date,
            max(issue_timestamp)::date
        from fact_invoices
        """
    ).fetchone()

    if lo is None or hi is None:
        st.error("ไม่พบข้อมูลวันที่ใน fact_invoices")
        st.stop()

    # -----------------------------------------------------
    # รายชื่อสถานี
    # ชื่อตารางจริงคือ dim_gasstation ไม่ใช่ dim_gasstations
    # -----------------------------------------------------
    stations = con.execute(
        """
        select
            gas_station_id,
            gas_station_name
        from dim_gasstation
        order by gas_station_id
        """
    ).fetchall()

    labels = dict(stations)

    if not labels:
        st.error("ไม่พบข้อมูลสถานีใน dim_gasstation")
        st.stop()

    # -----------------------------------------------------
    # Sidebar filters
    # -----------------------------------------------------
    date_range = st.sidebar.date_input(
        "ช่วงวันที่",
        value=(lo, hi),
        min_value=lo,
        max_value=hi,
    )

    if len(date_range) != 2:
        st.info("เลือกวันเริ่มและวันสิ้นสุด")
        st.stop()

    start, end = date_range

    chosen = st.sidebar.multiselect(
        "สถานี (ว่าง = ทุกสถานี)",
        list(labels),
        format_func=lambda station_id: labels[station_id],
    )

    chosen = chosen or list(labels)

    mode = st.sidebar.radio(
        "รูปแบบการวิเคราะห์",
        [
            "เลือกมิติและตัวชี้วัดเอง",
            "มุมมองสำหรับ Business Questions",
        ],
    )

    st.caption(
        f"{start} ถึง {end} • "
        f"{len(chosen)} สถานี • "
        "หน่วยเงินตามต้นทาง"
    )

    # =====================================================
    # MODE 1 : Explore Dim / Fact
    # =====================================================
    if mode == "เลือกมิติและตัวชี้วัดเอง":

        grain = st.selectbox(
            "ระดับข้อมูล",
            ["invoices", "sales"],
            format_func=lambda x: (
                "ใบเสร็จ"
                if x == "invoices"
                else "รายการสินค้า"
            ),
        )

        options = list(DIMENSIONS)

        if grain == "sales":
            options += list(PRODUCT_DIMENSIONS)
        else:
            options += ["วิธีชำระเงิน"]

        dims = st.multiselect(
            "เลือกมิติ 1–2 มิติ",
            options,
            default=["สถานี"],
            max_selections=2,
        )

        metric_options = [
            "ยอดขาย",
            "จำนวนบิล",
        ]

        if grain == "sales":
            metric_options.append("ปริมาณเชื้อเพลิง (ลิตร)")

        metric = st.selectbox(
            "ตัวชี้วัด",
            metric_options,
        )

        if not dims:
            st.info("เลือกอย่างน้อยหนึ่งมิติ")
            st.stop()

        sql, params = explore_query(
            grain,
            dims,
            metric,
            start,
            end,
            chosen,
        )

        df = con.execute(sql, params).fetch_df()

        if metric == "จำนวนบิล" and grain == "sales":
            st.caption(
                "นับบิลไม่ซ้ำภายในแต่ละกลุ่ม "
                "บิลเดียวอาจซื้อหลายสินค้า "
                "จึงห้ามบวกจำนวนบิลข้ามกลุ่มสินค้า"
            )

        if metric == "ปริมาณเชื้อเพลิง (ลิตร)":
            st.caption(
                "นับลิตรเฉพาะ Gasoline และ Diesel "
                "สินค้าประเภทอื่นไม่รวมในตัวชี้วัดนี้"
            )

        if not df.empty:

            plot = df.copy()

            plot["axis_1"] = plot["axis_1"].astype(str)

            if len(dims) == 2:

                plot["axis_2"] = plot["axis_2"].astype(str)

                chart = plot.pivot(
                    index="axis_1",
                    columns="axis_2",
                    values="value",
                ).fillna(0)

            else:

                chart = plot.set_index("axis_1")[["value"]]

            if dims[0] in ["วันที่", "เดือน", "ชั่วโมง"]:
                st.line_chart(chart)
            else:
                st.bar_chart(chart)

        else:
            st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")

        st.caption(
            "เปลี่ยนมิติเพื่อดูยอดตามถนน ชั่วโมง สินค้า "
            "พนักงาน หรือประเภทรถได้ โดยใช้ Fact ชุดเดียวกัน"
        )

    # =====================================================
    # MODE 2 : Business Questions
    # =====================================================
    else:

        n = st.selectbox(
            "คำถาม",
            list(TITLES),
            format_func=lambda i: f"{i}. {TITLES[i]}",
        )

        fee = (
            st.number_input(
                "ค่าธรรมเนียมบัตร (%)",
                min_value=0.0,
                max_value=100.0,
                value=2.0,
            )
            / 100
            if n == 14
            else 0.02
        )

        threshold = (
            st.number_input(
                "เกณฑ์เตือนระดับถัง (%)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
            )
            / 100
            if n == 12
            else 0.20
        )

        sql, params = question_query(
            n,
            start,
            end,
            chosen,
            fee_rate=fee,
            warning_ratio=threshold,
        )

        df = con.execute(sql, params).fetch_df()

        notes = {
            1: (
                "กลุ่ม High / Medium / Low เป็นเกณฑ์ percentile "
                "ที่สมมติขึ้น และคำนวณใหม่ตามช่วงวันและสถานีที่เลือก"
            ),
            5: (
                "เปรียบเทียบค่าเฉลี่ยต่อวันเพราะจำนวนวันไม่เท่ากัน "
                "กราฟนี้ยังไม่ใช่ผลทดสอบนัยสำคัญทางสถิติ"
            ),
            11: (
                "ส่วนต่างเป็นประเด็นให้ตรวจสอบ ไม่ใช่หลักฐานการสูญหาย "
                "สินค้าของถังอนุมานจากชื่อถัง"
            ),
            12: (
                "ใช้ประวัติทั้งหมดถึงวันสิ้นสุดที่เลือก ไม่จำกัดวันเริ่ม "
                "CurrentQuantity เป็น master snapshot ของไฟล์ "
                "ไม่ใช่ยอด ณ วันสิ้นสุดที่เลือก"
            ),
            13: (
                "จำนวนคนจาก master snapshot ไม่เปลี่ยนตามตัวกรองวัน "
                "เพราะไม่มีประวัติกะและการย้ายพนักงาน"
            ),
            15: (
                "จำนวนพนักงานจาก master snapshot "
                "ไม่มีข้อมูลกะหรือเกณฑ์ภาระงาน "
                "จึงยังสรุปความเพียงพอไม่ได้"
            ),
        }

        if n in notes:
            st.info(notes[n])

        axes = {
            1: ("gas_station_name", "avg_daily_sales"),
            2: ("gas_station_name", "sales_amount"),
            3: ("hour_id", "invoice_count"),
            4: ("payment_method", "invoice_count"),
            5: ("day_type", "avg_daily_sales"),
            6: ("employee_name", "invoice_count"),
            7: ("street", "total_sales"),
            8: ("gas_station_name", "gasoline_sales"),
            9: ("date_day", "sales_amount"),
            10: ("weekday_name", "avg_daily_sales"),
            11: ("gas_station_name", "difference_liters"),
            12: ("tank_id", "remaining_pct"),
            13: ("position", "employee_count"),
            14: ("gas_station_name", "simulated_fee"),
            15: ("gas_station_name", "revenue_per_employee"),
        }

        if df.empty:
            st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")

        else:
            default_x, default_y = axes[n]

            st.caption(
                "เลือกคอลัมน์จากผลลัพธ์เพื่อเปลี่ยนกราฟได้ "
                "ตารางด้านล่างแสดงรายละเอียดครบ"
            )

            columns = list(df.columns)

            x_index = (
                columns.index(default_x)
                if default_x in columns
                else 0
            )

            x = st.selectbox(
                "แกนนอน",
                columns,
                index=x_index,
            )

            numeric = list(
                df.select_dtypes(include="number").columns
            )

            if numeric:

                y_index = (
                    numeric.index(default_y)
                    if default_y in numeric
                    else 0
                )

                y = st.selectbox(
                    "ค่าบนกราฟ",
                    numeric,
                    index=y_index,
                )

                plot = df[[x, y]].copy()

                plot[x] = plot[x].astype(str)

                # ไม่รวม ratio / percentage / average ซ้ำแบบเงียบ ๆ
                if plot[x].duplicated().any():

                    st.caption(
                        "มีหลายแถวต่อชื่อแกน "
                        "จึงใส่ลำดับแถวกำกับเพื่อแสดงแต่ละค่าตาม Grain "
                        "เลือกสถานีเดียวเพื่ออ่านง่ายขึ้น"
                    )

                    plot[x] = (
                        plot[x]
                        + " · "
                        + (plot.index + 1).astype(str)
                    )

                st.bar_chart(
                    plot.set_index(x),
                    y=y,
                )

    # =====================================================
    # Result table
    # =====================================================
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
    )

    # -----------------------------------------------------
    # Download CSV
    # -----------------------------------------------------
    st.download_button(
        "ดาวน์โหลดผลที่กรองแล้ว",
        df.to_csv(index=False).encode("utf-8-sig"),
        "dashboard_result.csv",
        "text/csv",
    )

    # -----------------------------------------------------
    # SQL
    # -----------------------------------------------------
    with st.expander("SQL ที่คำนวณจาก Dim/Fact"):
        st.code(
            sql,
            language="sql",
        )