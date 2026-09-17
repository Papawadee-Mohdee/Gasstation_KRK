-- Grain: หนึ่งแถวต่อ InvoiceDetailID ห้ามนำยอดหัวบิลมาบวกซ้ำที่ระดับนี้
with source as (
    select * from {{ ref('stg_invoicedetail') }}
)
select d.InvoiceDetailID::bigint as invoice_detail_id,
    d.InvoiceID::bigint as invoice_id,
    d.ProductID::integer as product_id,
    i.customer_id, i.employee_id, i.gas_station_id, i.date_id, i.hour_id,
    d.QuantitySold::decimal(18,4) as quantity_sold,
    d.SellingPrice::decimal(18,2) as selling_price,
    d.TotalPrice::decimal(18,2) as sales_amount,
    current_localtimestamp() as insertion_timestamp
from source d
left join {{ ref('fact_invoices') }} i on d.InvoiceID::bigint = i.invoice_id
