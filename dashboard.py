"""Executive dashboard. Read-only dimension/fact queries, no mart tables."""
from pathlib import Path
import os
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
COLORS = ['#167D9A', '#ED9B40', '#5D6AB1', '#56A98C', '#D96966']
DAY_NAMES = {1:'จันทร์',2:'อังคาร',3:'พุธ',4:'พฤหัสบดี',5:'ศุกร์',6:'เสาร์',7:'อาทิตย์'}


def find_database():
    explicit = os.environ.get('GASSTATION_DB')
    paths = [Path(explicit)] if explicit else [ROOT/'Gasstation_dw_duckdb/duckdb/dev.duckdb',ROOT/'Gasstation_dw_duckdb/dev.duckdb',ROOT/'duckdb/gasstation.duckdb',ROOT/'duckdb/dev.duckdb',ROOT/'dev.duckdb']
    errors=[]
    for path in paths:
        if not path.is_file(): continue
        try:
            with duckdb.connect(str(path),read_only=True) as c:
                names={r[0] for r in c.execute("select table_name from information_schema.tables where table_schema='main'").fetchall()}
                old={'fact_sales','fact_inventory','dim_gasstation','dim_product','dim_employee','dim_tank','dim_date','dim_time','dim_paymentmethod'}
                new={'fact_sales','fact_invoices','fact_inventory','dim_gasstations','dim_products','dim_employees','dim_tanks','dim_date'}
                cols={r[0] for r in c.execute('describe fact_sales').fetchall()} if 'fact_sales' in names else set()
                if old<=names and 'gasstation_key' in cols: return path,'course'
                hybrid={'fact_sales','fact_invoices','fact_inventory','dim_gasstation','dim_products','dim_employee','dim_tanks','dim_date'}
                if hybrid<=names and 'gas_station_id' in cols: return path,'hybrid'
                if new<=names: return path,'dim_fact'
                errors.append(f'{path.name}: ตาราง Dim/Fact ยังไม่ครบ')
        except Exception as e: errors.append(f'{path.name}: {e}')
    raise RuntimeError('ไม่พบฐานข้อมูลที่มี Dim/Fact ครบ กรุณารัน dbt ก่อน หรือกำหนด GASSTATION_DB\n'+'\n'.join(errors))


def base_sql(layout):
    if layout=='course':
        return '''with stations as (
          select gasstation_key as station_id,gasstation_name as station_name,
          trim(split_part(address,',',1)) as street from dim_gasstation
        ), products as (
          select product_key as product_id,product_name,product_type from dim_product
        ), employees as (
          select employee_key as employee_id,employee_name,position,home_gasstation_id as station_id from dim_employee
        ), tanks as (
          select tank_key as tank_id,gasstation_id as station_id,tank_name,capacity_liters as capacity from dim_tank
        ), sales as (
          select f.invoice_id,f.invoice_detail_id,f.gasstation_key as station_id,
          f.employee_key as employee_id,f.product_key as product_id,d.full_date::date as date_day,
          f.time_key as hour,pm.payment_method,f.quantity_sold::double as liters,
          f.total_price::double as revenue
          from fact_sales f join dim_date d on f.date_key=d.date_key
          join dim_paymentmethod pm on f.paymentmethod_key=pm.paymentmethod_key
        ), invoices as (
          select invoice_id,station_id,employee_id,date_day,hour,payment_method,sum(revenue) as revenue
          from sales group by 1,2,3,4,5,6
        ), inventory as (
          select f.transaction_id,f.tank_key as tank_id,f.gasstation_key as station_id,
          d.full_date::date as date_day,f.time_key as hour,d.full_date::timestamp+f.time_key*interval '1 hour' as event_time,
          f.quantity_out::double as quantity_out,f.remaining_quantity::double as remaining_quantity
          from fact_inventory f join dim_date d on f.date_key=d.date_key
        )'''
    sql = '''with stations as (
        select gas_station_id as station_id,gas_station_name as station_name,street from dim_gasstations
    ),products as (select product_id,product_name,product_type from dim_products),
    employees as (select employee_id,employee_name,position,assigned_gas_station_id as station_id from dim_employees),
    tanks as (select tank_id,gas_station_id as station_id,tank_name,capacity from dim_tanks),
    sales as (
        select f.invoice_id,f.invoice_detail_id,f.gas_station_id as station_id,f.employee_id,f.product_id,
        d.date_day,f.hour_id as hour,i.payment_method,f.quantity_sold::double as liters,f.sales_amount::double as revenue
        from fact_sales f join dim_date d using(date_id) join fact_invoices i using(invoice_id)
    ),invoices as (
        select invoice_id,gas_station_id as station_id,employee_id,issue_timestamp::date as date_day,
        hour_id as hour,payment_method,total_amount::double as revenue from fact_invoices
    ),inventory as (
        select transaction_id,tank_id,gas_station_id as station_id,transaction_timestamp::date as date_day,
        transaction_timestamp as event_time,hour(transaction_timestamp) as hour,quantity_out::double as quantity_out,remaining_quantity::double as remaining_quantity
        from fact_inventory
    )'''
    if layout=='hybrid':
        sql=sql.replace('dim_gasstations','dim_gasstation').replace('dim_employees','dim_employee')
    return sql


@st.cache_data(show_spinner=False)
def query(db,stamp,layout,sql,params=()):
    with duckdb.connect(db,read_only=True) as c:
        return c.execute(base_sql(layout)+' '+sql,list(params)).fetch_df()


def prepare_stations(stations):
    result = stations.copy()
    result['street'] = (result['street'].astype('string').fillna('')
                        .str.strip().replace('', 'ไม่ระบุสายถนน'))
    return result


def plot(fig):
    fig.update_layout(template='plotly_white',font=dict(family='sans-serif',size=13,color='#24364B'),
        margin=dict(l=10,r=10,t=15,b=10),paper_bgcolor='rgba(0,0,0,0)',
        legend_title_text='',colorway=COLORS,hovermode='closest')
    st.plotly_chart(fig,width='stretch')


def bars(df,x,y,color=None,orientation='v',**kw):
    if df.empty: st.info('ไม่มีข้อมูลในช่วงที่เลือก'); return
    plot(px.bar(df,x=x,y=y,color=color,orientation=orientation,color_discrete_sequence=COLORS,**kw))


def table(df,label='ดูข้อมูลประกอบกราฟ'):
    with st.expander(label):
        st.dataframe(df,hide_index=True,width='stretch')
        st.download_button('ดาวน์โหลด CSV',df.to_csv(index=False).encode('utf-8-sig'),file_name='dashboard_data.csv',mime='text/csv',key=label)


def main():
    st.set_page_config(page_title='Gas Station | ภาพรวมธุรกิจ',page_icon='⛽',layout='wide')
    st.markdown('''<style>.stApp {background:#F5F7FB} [data-testid="stSidebar"]{background:white}
    [data-testid="stMetric"]{background:white;padding:18px;border:1px solid #E3EAF0;border-radius:12px}
    h1,h2,h3{color:#17334B} .block-container{padding-top:2rem}</style>''',unsafe_allow_html=True)
    try:
        path,layout=find_database();stamp=path.stat().st_mtime_ns
        q=lambda sql,params=():query(str(path),stamp,layout,sql,tuple(params))
        stations=prepare_stations(q('select * from stations order by station_id'))
        bounds=q('select min(date_day) as lo,max(date_day) as hi from invoices').iloc[0]
    except Exception as e:
        st.error(str(e));st.stop()
    with st.sidebar:
        st.markdown('## ⛽ GAS STATION')
        st.caption('ยอดขาย • พื้นที่ • การดำเนินงาน')
        page=st.radio('เลือกภาพรวม',['ยอดขายและพื้นที่','สินค้าและการชำระเงิน','ช่วงเวลาและการให้บริการ','น้ำมันคงเหลือ','พนักงานและประสิทธิภาพ'])
        dates=st.date_input('ช่วงวันที่',(bounds.lo.date(),bounds.hi.date()),min_value=bounds.lo.date(),max_value=bounds.hi.date())
        if len(dates)!=2: st.info('เลือกวันเริ่มและวันสิ้นสุด');st.stop()
        selected_streets=st.multiselect('แบ่งตามสายถนน',sorted(stations.street.unique()))
        eligible=stations[stations.street.isin(selected_streets)] if selected_streets else stations
        ids=st.multiselect('สถานี',eligible.station_id.tolist(),format_func=lambda n:stations.set_index('station_id').loc[n,'station_name'])
        chosen=eligible[eligible.station_id.isin(ids)] if ids else eligible
        st.caption('ไม่เลือก = ทุกสายถนน / ทุกสถานี')
        st.caption('จัดกลุ่มสถานีตามข้อมูลถนน โดยข้อมูลที่ว่างจะแสดงเป็น ไม่ระบุสายถนน')
    if chosen.empty:st.info('ไม่พบสถานีที่ตรงกับตัวกรอง');st.stop()
    start,end=dates;day_count=(end-start).days+1;station_ids=chosen.station_id.astype(int).tolist()
    args=[start,end,station_ids]
    scope='date_day between ? and ? and station_id in (select unnest(?::integer[]))'
    def invoice_sql(body): return q(body,args)
    # Aggregate before enriching with station/street to avoid multiplying facts.
    daily=invoice_sql(f'select station_id,date_day,sum(revenue) as revenue,count(*) as bills from invoices where {scope} group by 1,2')
    grid=pd.MultiIndex.from_product([station_ids,pd.date_range(start,end)],names=['station_id','date_day']).to_frame(index=False)
    daily=grid.merge(daily,on=['station_id','date_day'],how='left').fillna({'revenue':0,'bills':0}).merge(chosen,on='station_id',validate='many_to_one')
    totals=daily.groupby(['station_id','station_name','street'],as_index=False)[['revenue','bills']].sum()
    total=float(totals.revenue.sum());bills=int(totals.bills.sum())
    st.title(page)
    st.caption(f'{start:%d/%m/%Y} – {end:%d/%m/%Y} · {day_count} วัน · {len(chosen)} สถานี · หน่วยเงินตามต้นทาง')
    a,b,c,d=st.columns(4)
    a.metric('ยอดขายรวม (ล้าน)',f'{total/1_000_000:,.2f}',help=f'ยอดเต็ม {total:,.2f} หน่วยเงินตามต้นทาง');b.metric('จำนวนบิล',f'{bills:,}')
    c.metric('ยอดเฉลี่ยต่อวัน (ล้าน)',f'{total/day_count/1_000_000:,.2f}',help=f'ยอดเต็ม {total/day_count:,.2f} หน่วยเงินต่อวัน');d.metric('ยอดเฉลี่ยต่อบิล',f'{total/bills:,.2f}' if bills else '—')
    if page=='ยอดขายและพื้นที่':
        trend=daily.groupby('date_day',as_index=False).revenue.sum()
        st.subheader('ยอดขายรายวันของพื้นที่ที่เลือก')
        plot(px.line(trend,x='date_day',y='revenue',markers=True,labels={'date_day':'วันที่','revenue':'ยอดขาย'}))
        left,right=st.columns(2)
        with left:
            st.subheader('ยอดขายของแต่ละ สายถนน')
            roads_summary=totals.groupby('street',as_index=False).agg(revenue=('revenue','sum'),stations=('station_id','count'))
            roads_summary['per_station']=roads_summary.revenue/roads_summary.stations
            bars(roads_summary,'street','revenue',hover_data=['stations','per_station'],labels={'street':'สายถนน','revenue':'ยอดขาย','stations':'จำนวนสถานี','per_station':'ยอดขายต่อสถานี'})
        with right:
            st.subheader('สถานีที่สร้างยอดขายสูงสุด')
            top=totals.nlargest(10,'revenue').sort_values('revenue')
            bars(top,'revenue','station_name','street',orientation='h',labels={'revenue':'ยอดขาย','station_name':'สถานี','street':'สายถนน'})
        left,right=st.columns(2)
        with left:
            st.subheader('การกระจายสถานีตามยอดขายเฉลี่ยต่อวัน')
            totals['average']=totals.revenue/day_count
            rank=totals.average.rank(method='min')
            percentile=(rank-1)/(len(totals)-1) if len(totals)>1 else rank*0
            totals['tier']=pd.cut(percentile,[-1,1/3-1e-12,2/3-1e-12,1],labels=['ต่ำ','ปานกลาง','สูง'])
            tiers=totals.groupby('tier',observed=True).size().reset_index(name='stations')
            plot(px.pie(tiers,names='tier',values='stations',hole=.65,color_discrete_sequence=COLORS))
            st.caption('แบ่งกลุ่มสัมพัทธ์ตามอันดับยอดเฉลี่ยในสถานีที่เลือก ไม่ใช่เป้าหมายยอดขายบริษัท')
        with right:
            st.subheader('ถนนที่มียอดขายสูงและต่ำ')
            roads=totals.groupby('street',as_index=False).revenue.sum().sort_values('revenue')
            roads=pd.concat([roads.head(5),roads.tail(5)]).drop_duplicates('street')
            bars(roads,'revenue','street',orientation='h',labels={'revenue':'ยอดขายรวม','street':'ถนน'})
        st.subheader('ช่องว่างยอดขายระหว่างสถานีสูงสุดและต่ำสุดในแต่ละวัน')
        extremes=daily.groupby('date_day',as_index=False).agg(high=('revenue','max'),low=('revenue','min'))
        plot(px.line(extremes.rename(columns={'high':'สูงสุด','low':'ต่ำสุด'}),x='date_day',y=['สูงสุด','ต่ำสุด'],labels={'date_day':'วันที่','value':'ยอดขาย'},markers=True))
        detail=daily.merge(extremes,on='date_day');detail=detail[(detail.revenue==detail.high)|(detail.revenue==detail.low)].copy()
        detail['high_to_low']=detail.high/detail.low.replace(0,float('nan'))
        table(detail[['date_day','station_name','revenue','high_to_low']].rename(columns={'date_day':'วันที่','station_name':'สถานี','revenue':'ยอดขาย','high_to_low':'สูงสุดเทียบต่ำสุด (เท่า)'}),'รายชื่อสถานีสูงสุดและต่ำสุดในแต่ละวัน')
    elif page=='สินค้าและการชำระเงิน':
        products=q(f'''select s.station_id,p.product_name,p.product_type,sum(s.liters) as liters,sum(s.revenue) as revenue
            from sales s join products p using(product_id) where {scope} group by 1,2,3''',args)
        mix=products.groupby(['product_name','product_type'],as_index=False)[['liters','revenue']].sum()
        fuel=mix[mix.product_type.isin(['Gasoline','Diesel'])]
        l,r=st.columns(2)
        with l:
            st.subheader('น้ำมันที่ขายได้มากที่สุด — ลิตร')
            bars(fuel,'product_name','liters','product_name',labels={'product_name':'น้ำมัน','liters':'ลิตร'})
        with r:
            st.subheader('สินค้าที่สร้างยอดขายมากที่สุด — มูลค่า')
            bars(mix,'product_name','revenue','product_name',labels={'product_name':'สินค้า','revenue':'ยอดขาย'})
        st.subheader('สินค้าขายดีในแต่ละสถานี')
        unit=st.radio('เปรียบเทียบด้วย',['มูลค่าขาย','ลิตรเชื้อเพลิง'],horizontal=True)
        measure='revenue' if unit=='มูลค่าขาย' else 'liters'
        detail=products.merge(chosen,on='station_id')
        if measure=='liters': detail=detail[detail.product_type.isin(['Gasoline','Diesel'])]
        detail=detail[detail.station_id.isin(totals.nlargest(10,'revenue').station_id)]
        bars(detail,'station_name',measure,'product_name',barmode='group',labels={'station_name':'สถานี',measure:unit,'product_name':'สินค้า'})
        st.caption('แสดงสูงสุด 10 สถานีตามยอดขายรวม เลือกสถานีเพื่อเจาะดูพื้นที่อื่น')
        st.subheader('สัดส่วนยอดขายเบนซินและดีเซลของแต่ละสถานี')
        station_mix=products[products.product_type.isin(['Gasoline','Diesel'])].groupby(['station_id','product_type'],as_index=False).revenue.sum().merge(chosen,on='station_id')
        station_mix['share']=station_mix.revenue/station_mix.groupby('station_id').revenue.transform('sum').replace(0,float('nan'))*100
        st.caption('แสดงสูงสุด 15 สถานีตามยอดขายรวม')
        bars(station_mix[station_mix.station_id.isin(totals.nlargest(15,'revenue').station_id)],'station_name','share','product_type',labels={'station_name':'สถานี','share':'สัดส่วนยอดขาย (%)','product_type':'เชื้อเพลิง'})
        pay=q(f'select station_id,payment_method,count(*) as bills,sum(revenue) as revenue from invoices where {scope} group by 1,2',args).merge(chosen,on='station_id')
        l,r=st.columns(2)
        with l:
            st.subheader('ลูกค้าชำระเงินด้วยวิธีใด')
            pm=pay.groupby('payment_method',as_index=False).bills.sum()
            plot(px.pie(pm,names='payment_method',values='bills',hole=.6,color_discrete_sequence=COLORS))
        with r:
            st.subheader('สัดส่วนการชำระเงินในแต่ละ สายถนน')
            rp=pay.groupby(['street','payment_method'],as_index=False).bills.sum()
            rp['share']=rp.bills/rp.groupby('street').bills.transform('sum')*100
            bars(rp,'street','share','payment_method',labels={'street':'สายถนน','share':'สัดส่วนจำนวนบิล (%)','payment_method':'วิธีชำระเงิน'})
        st.subheader('เงินสดและบัตรเครดิตในแต่ละสถานี')
        pay['share']=pay.bills/pay.groupby('station_id').bills.transform('sum')*100
        bars(pay[pay.station_id.isin(totals.nlargest(15,'bills').station_id)],'station_name','share','payment_method',labels={'station_name':'สถานี','share':'สัดส่วนจำนวนบิล (%)','payment_method':'วิธีชำระเงิน'})
        st.caption('แสดงสูงสุด 15 สถานีตามจำนวนบิล เลือกสถานีเพื่อเจาะดูพื้นที่อื่น')
        st.subheader('ค่าธรรมเนียมบัตรเครดิตจำลอง')
        fee=st.slider('อัตราค่าธรรมเนียม (%)',0.0,5.0,2.0,.1)/100
        fees=pay[pay.payment_method=='Credit Card'].groupby('station_id',as_index=False).revenue.sum().rename(columns={'revenue':'card_sales'})
        fees=totals.merge(fees,on='station_id',how='left').fillna({'card_sales':0});fees['fee']=fees.card_sales*fee;fees['share']=fees.fee/fees.revenue.replace(0,float('nan'))*100
        bars(fees.nlargest(15,'share'),'station_name','share',hover_data=['fee'],labels={'station_name':'สถานี','fee':'ค่าธรรมเนียมจำลอง','share':'ค่าธรรมเนียมต่อยอดขาย (%)'})
        st.caption('แสดง 15 สถานีที่มีสัดส่วนค่าธรรมเนียมสูงสุด')
        table(products.merge(chosen[['station_id','station_name','street']],on='station_id'),'ยอดขายสินค้าแยกสถานี')
    elif page=='ช่วงเวลาและการให้บริการ':
        hourly=q(f'select station_id,hour,count(*) as bills from invoices where {scope} group by 1,2',args).merge(chosen,on='station_id')
        st.subheader('ชั่วโมงที่มีการออกบิลหนาแน่นที่สุด')
        hours=hourly.groupby('hour').bills.sum().reindex(range(24),fill_value=0).reset_index()
        bars(hours,'hour','bills',labels={'hour':'ชั่วโมง (0–23)','bills':'จำนวนบิล'})
        st.caption('ตารางสีแสดงสูงสุด 20 สถานีตามจำนวนบิล เลือกสถานีเพื่อดูรายละเอียด')
        hourly=hourly[hourly.station_id.isin(totals.nlargest(20,'bills').station_id)]
        heat=hourly.pivot_table(index='station_name',columns='hour',values='bills',fill_value=0).reindex(columns=range(24),fill_value=0)
        plot(px.imshow(heat,aspect='auto',color_continuous_scale='Teal',labels={'x':'ชั่วโมง','y':'สถานี','color':'จำนวนบิล'}))
        daily['weekday']=daily.date_day.dt.isocalendar().day.astype(int);daily['day_type']=daily.weekday.map(lambda x:'สุดสัปดาห์' if x>=6 else 'วันธรรมดา')
        network=daily.groupby(['date_day','day_type'],as_index=False)[['revenue','bills']].sum()
        comp=network.groupby('day_type',as_index=False).agg(revenue=('revenue','mean'),bills=('bills','mean'),days=('date_day','count'))
        l,r=st.columns(2)
        with l:
            st.subheader('ยอดขายเฉลี่ยต่อวัน: วันธรรมดาเทียบสุดสัปดาห์')
            bars(comp,'day_type','revenue',hover_data=['days'],labels={'day_type':'ประเภทวัน','revenue':'ยอดขายเฉลี่ยต่อวัน','days':'จำนวนวัน'})
        with r:
            st.subheader('จำนวนบิลเฉลี่ยต่อวัน')
            bars(comp,'day_type','bills',hover_data=['days'],labels={'day_type':'ประเภทวัน','bills':'บิลเฉลี่ยต่อวัน','days':'จำนวนวัน'})
        st.caption('การเปรียบเทียบเชิงพรรณนา ไม่ใช่ข้อสรุปนัยสำคัญทางสถิติ และไม่แทนจำนวนผู้เข้าใช้พื้นที่จริง')
        st.subheader('วันใดของสัปดาห์ขายดีที่สุดในแต่ละสถานี')
        weekdays=daily.groupby(['station_name','weekday'],as_index=False).revenue.mean()
        weekdays['day']=weekdays.weekday.map(DAY_NAMES)
        best=weekdays[weekdays.station_name.isin(totals.nlargest(20,'revenue').station_name)].pivot(index='station_name',columns='weekday',values='revenue').rename(columns=DAY_NAMES)
        plot(px.imshow(best,aspect='auto',color_continuous_scale='Teal',labels={'x':'วันในสัปดาห์','y':'สถานี','color':'ยอดเฉลี่ยต่อวัน'}))
        st.caption('แสดงสูงสุด 20 สถานีตามยอดขายรวม สีเข้มหมายถึงยอดเฉลี่ยสูงกว่า')
    elif page=='น้ำมันคงเหลือ':
        latest=q(''' ,ranked as (
            select *,row_number() over(partition by tank_id order by event_time desc,transaction_id desc) as rn
            from inventory where date_day<=? and station_id in (select unnest(?::integer[]))
        ) select t.*,i.remaining_quantity,i.date_day as last_date from tanks t
          left join ranked i on t.tank_id=i.tank_id and i.rn=1
          where t.station_id in (select unnest(?::integer[]))''',[end,station_ids,station_ids]).merge(chosen,on='station_id')
        latest['percent']=latest.remaining_quantity/latest.capacity.replace(0,float('nan'))*100
        threshold=st.slider('เกณฑ์เตือนปริมาณคงเหลือ (%)',5,50,20)
        latest['status']=latest.percent.map(lambda x:'ไม่มีข้อมูล' if pd.isna(x) else 'ต่ำกว่าเกณฑ์' if x<=threshold else 'ปกติ')
        st.subheader(f'ระดับน้ำมันในถัง ณ {end:%d/%m/%Y}')
        st.caption('ใช้ธุรกรรมล่าสุดถึงวันสิ้นสุดที่เลือก ไม่รวมยอดคงเหลือข้ามเวลา และไม่จำกัดด้วยวันเริ่ม')
        st.metric('ถังที่ต้องตรวจระดับน้ำมัน',int((latest.status=='ต่ำกว่าเกณฑ์').sum()))
        latest['tank_label']=latest.station_name+' · '+latest.tank_name
        plot(px.bar(latest.sort_values('percent').head(30),x='percent',y='tank_label',color='status',orientation='h',color_discrete_map={'ปกติ':'#167D9A','ต่ำกว่าเกณฑ์':'#D96966','ไม่มีข้อมูล':'#999'},labels={'percent':'คงเหลือ / ความจุ (%)','tank_label':'ถัง'}).add_vline(x=threshold,line_dash='dash',line_color='#D96966'))
        st.caption('แสดง 30 ถังที่มีสัดส่วนคงเหลือต่ำสุด รายละเอียดครบทุกถังอยู่ด้านล่าง')
        # Aggregate each process first. Mapping is derived from the fuel name in TankName.
        diff=q(f''' ,sold as (
            select s.station_id,s.date_day,p.product_name,sum(s.liters) as sold
            from sales s join products p using(product_id) where {scope} and p.product_type in ('Gasoline','Diesel') group by 1,2,3
        ),outflow as (
            select i.station_id,i.date_day,trim(regexp_replace(t.tank_name,' Tank$','')) as product_name,sum(i.quantity_out) as tank_out
            from inventory i join tanks t using(tank_id) where i.date_day between ? and ? and i.station_id in (select unnest(?::integer[])) group by 1,2,3
        ) select coalesce(s.station_id,o.station_id) as station_id,coalesce(s.date_day,o.date_day) as date_day,
        coalesce(s.product_name,o.product_name) as product_name,coalesce(s.sold,0) as sold,coalesce(o.tank_out,0) as tank_out,
        coalesce(o.tank_out,0)-coalesce(s.sold,0) as difference,
        case when s.station_id is null or o.station_id is null then 'ข้อมูลไม่ครบสองฝั่ง' else 'ครบ' end as coverage
        from sold s full outer join outflow o on s.station_id=o.station_id and s.date_day=o.date_day and s.product_name=o.product_name''',args+args).merge(chosen,on='station_id')
        st.subheader('น้ำมันจ่ายออกจากถังเทียบกับปริมาณขาย')
        flagged=diff[(diff.difference.abs()>.01)|(diff.coverage!='ครบ')]
        if flagged.empty: st.success('ปริมาณจ่ายและปริมาณขายตรงกันทุกกลุ่มวัน–สถานี–สินค้า ภายใน 0.01 ลิตร')
        else: bars(flagged,'station_name','difference','product_name',labels={'station_name':'สถานี','difference':'ส่วนต่าง (ลิตร)','product_name':'น้ำมัน'})
        st.caption('สินค้าของถังอนุมานจากชื่อถัง ความคลาดเคลื่อนเป็นรายการให้ตรวจสอบ ไม่ใช่หลักฐานการสูญหาย')
        table(latest[['station_name','tank_name','remaining_quantity','capacity','percent','last_date','status']],'สถานะน้ำมันทุกถัง')
        table(diff[['date_day','station_name','product_name','sold','tank_out','difference','coverage']],'ผลเปรียบเทียบน้ำมันรายวัน')
    else:
        staff=q('select station_id,position,count(*) as staff from employees where station_id in (select unnest(?::integer[])) group by 1,2',[station_ids]).merge(chosen,on='station_id')
        l,r=st.columns(2)
        with l:
            st.subheader('โครงสร้างตำแหน่งงานในแต่ละ สายถนน')
            structure=staff.groupby(['street','position'],as_index=False).staff.sum()
            bars(structure,'street','staff','position',labels={'street':'สายถนน','staff':'จำนวนพนักงาน','position':'ตำแหน่ง'})
        with r:
            st.subheader('พนักงานที่ออกบิลมากที่สุด')
            employees=q(f'''select i.station_id,i.employee_id,e.employee_name,count(*) as bills
                from invoices i left join employees e using(employee_id) where i.date_day between ? and ?
                and i.station_id in (select unnest(?::integer[])) group by 1,2,3''',args)
            top=employees.nlargest(10,'bills').merge(chosen,on='station_id').sort_values('bills')
            bars(top,'bills','employee_name','station_name',orientation='h',labels={'bills':'จำนวนบิล','employee_name':'พนักงาน','station_name':'สถานี'})
        st.subheader('สัดส่วนตำแหน่งงานในแต่ละสถานี')
        staff['share']=staff.staff/staff.groupby('station_id').staff.transform('sum')*100
        bars(staff[staff.station_id.isin(totals.nlargest(15,'revenue').station_id)],'station_name','share','position',labels={'station_name':'สถานี','share':'สัดส่วนพนักงาน (%)','position':'ตำแหน่ง'})
        st.caption('แสดงสูงสุด 15 สถานีตามยอดขายรวม เลือกสถานีเพื่อดูสาขาอื่น')
        count=staff.groupby('station_id').staff.sum();pump=staff[staff.position=='Pump Attendant'].groupby('station_id').staff.sum()
        productivity=totals.copy();productivity['staff']=productivity.station_id.map(count).fillna(0)
        productivity['pump']=productivity.station_id.map(pump).fillna(0)
        productivity['revenue_per_employee']=productivity.revenue/productivity.staff.replace(0,float('nan'))
        productivity['daily_bills_per_pump']=productivity.bills/day_count/productivity.pump.replace(0,float('nan'))
        l,r=st.columns(2)
        with l:
            st.subheader('ยอดขายต่อพนักงานของแต่ละสถานี')
            bars(productivity.nlargest(15,'revenue_per_employee').sort_values('revenue_per_employee'),'revenue_per_employee','station_name','street',orientation='h',labels={'revenue_per_employee':'ยอดขายต่อคนในช่วงที่เลือก','station_name':'สถานี','street':'สายถนน'})
        with r:
            st.subheader('ภาระงานต่อพนักงานเติมน้ำมัน')
            plot(px.scatter(productivity,x='pump',y='daily_bills_per_pump',size='revenue',color='street',hover_name='station_name',labels={'pump':'จำนวนพนักงานเติมน้ำมัน','daily_bills_per_pump':'บิลเฉลี่ยต่อคนต่อวัน','street':'สายถนน'}))
        st.caption('พนักงานเป็นจำนวนคนใน master snapshot ไม่ใช่คนเข้ากะจริง ยังตัดสินความเพียงพอไม่ได้เพราะไม่มีเวลาทำงานและมาตรฐานภาระงาน')
        leaders=employees[employees.bills==employees.groupby('station_id').bills.transform('max')].merge(chosen,on='station_id')
        table(leaders[['station_name','employee_name','bills']],'พนักงานออกบิลสูงสุดของทุกสถานี รวมอันดับเสมอ')
        table(staff[['station_name','position','staff']],'จำนวนพนักงานแยกตำแหน่งและสถานี')
        table(productivity,'ตัววัดประสิทธิภาพรายสถานี')


if __name__=='__main__':
    main()
