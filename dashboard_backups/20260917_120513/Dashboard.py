"""Read-only queries over reusable dimension and atomic fact tables.
No CREATE TABLE, CREATE VIEW or dbt mart models are used here.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TITLES={1:'ยอดเฉลี่ยรายวันและกลุ่มสถานี',2:'สินค้าขายดี',3:'ช่วงเวลาหนาแน่น',4:'สัดส่วนวิธีชำระเงิน',5:'วันธรรมดาและสุดสัปดาห์',6:'พนักงานที่ออกบิลสูงสุด',7:'ยอดขายตามถนน',8:'เบนซินและดีเซล',9:'สถานีสูงสุดและต่ำสุดรายวัน',10:'วันในสัปดาห์ที่ขายดี',11:'เปรียบเทียบน้ำมันจ่ายกับน้ำมันขาย',12:'ระดับน้ำมันล่าสุด',13:'โครงสร้างพนักงาน',14:'ค่าธรรมเนียมบัตรจำลอง',15:'ยอดขายต่อพนักงาน'}

def question_query(number,start,end,stations,fee_rate=.02,warning_ratio=.20,tolerance=.01):
    if number not in TITLES: raise ValueError('Invalid question')
    if start>end: raise ValueError('Invalid date range')
    files=list((ROOT/'dashboard_queries').glob(f'bq{number:02}_*.sql'))
    sql=files[0].read_text()
    # Stock snapshot is as-of end; flow comparisons use the whole selected interval.
    inventory_start='true' if number==12 else 'transaction_timestamp::date >= (select start_date from settings)'
    prefix=f'''with settings as (
        select ?::date as start_date,?::date as end_date,?::integer[] as station_ids,
               ?::double as fee_rate,?::double as warning_ratio,?::double as quantity_tolerance
    ),selected_stations as (
        select * from dim_gasstations where gas_station_id in
            (select unnest(station_ids) from settings)
    ),selected_dates as (
        select * from dim_date where date_day between
            (select start_date from settings) and (select end_date from settings)
    ),selected_invoices as (
        select * from fact_invoices where gas_station_id in (select gas_station_id from selected_stations)
        and date_id in (select date_id from selected_dates)
    ),selected_sales as (
        select * from fact_sales where gas_station_id in (select gas_station_id from selected_stations)
        and date_id in (select date_id from selected_dates)
    ),selected_inventory as (
        select * from fact_inventory where gas_station_id in (select gas_station_id from selected_stations)
        and {inventory_start} and transaction_timestamp::date <= (select end_date from settings)
    ),result as ({sql}) select * from result order by all'''
    return prefix,[start,end,list(stations),fee_rate,warning_ratio,tolerance]

DIMENSIONS={
    'สถานี':'g.gas_station_name','ถนน':'g.street','วันที่':'d.date_day',
    'เดือน':"strftime(d.date_day,'%Y-%m')",'ประเภทวัน':'d.day_type',
    'วันในสัปดาห์':"cast(d.weekday_number as varchar)||' '||d.weekday_name",
    'ชั่วโมง':'f.hour_id','พนักงาน':'e.employee_name','ประเภทรถ':'c.vehicle_type_name'}
PRODUCT_DIMENSIONS={'สินค้า':'p.product_name','ประเภทสินค้า':'p.product_type'}

def explore_query(grain,dimensions,metric,start,end,stations):
    allowed=dict(DIMENSIONS)
    if grain=='sales': allowed.update(PRODUCT_DIMENSIONS)
    else: allowed['วิธีชำระเงิน']='f.payment_method'
    metrics={'ยอดขาย':'sum(f.sales_amount)' if grain=='sales' else 'sum(f.total_amount)',
             'จำนวนบิล':'count(distinct f.invoice_id)'}
    if grain=='sales': metrics['ปริมาณเชื้อเพลิง (ลิตร)']="sum(case when p.product_type in ('Gasoline','Diesel') then f.quantity_sold else 0 end)"
    if grain not in ['sales','invoices'] or metric not in metrics or not 1<=len(dimensions)<=2 or any(x not in allowed for x in dimensions): raise ValueError('Invalid explorer selection')
    fields=','.join(f'{allowed[n]} as axis_{i+1}' for i,n in enumerate(dimensions))
    table='fact_sales' if grain=='sales' else 'fact_invoices'
    product_join='left join dim_products p on f.product_id=p.product_id' if grain=='sales' else ''
    sql=f'''select {fields},{metrics[metric]} as value from {table} f
    join dim_gasstations g on f.gas_station_id=g.gas_station_id
    join dim_date d on f.date_id=d.date_id
    left join dim_employees e on f.employee_id=e.employee_id
    left join dim_customers c on f.customer_id=c.customer_id
    {product_join}
    where d.date_day between ?::date and ?::date and f.gas_station_id in (select unnest(?::integer[]))
    group by {','.join(str(i+1) for i in range(len(dimensions)))} order by {','.join(str(i+1) for i in range(len(dimensions)))}'''
    return sql,[start,end,list(stations)]
