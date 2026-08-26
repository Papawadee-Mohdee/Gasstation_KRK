with invoice as (
    select * from {{ ref('stg_Invoice') }}
),
invoice_detail as (
    select * from {{ ref('stg_InvoiceDetail') }}
),
payment_method as (
    select * from {{ ref('dim_paymentmethod') }}
),
date_dim as (
    select * from {{ ref('dim_date') }}
),
time_dim as (
    select * from {{ ref('dim_time') }}
)

select
    d.date_key,
    t.time_key,
    i.customer_id           as customer_key,
    i.employee_id            as employee_key,
    i.gasstation_id            as gasstation_key,
    id.product_id                as product_key,
    pm.paymentmethod_key,
    i.invoice_id                  as invoice_id,          -- degenerate dimension
    id.invoice_detail_id            as invoice_detail_id,   -- degenerate dimension
    id.quantity_sold                                        as quantity_sold,
    id.selling_price                                          as selling_price,
    id.total_price                                              as total_price,
    1                                                              as line_count

from invoice_detail id
join invoice i
    on id.invoice_id = i.invoice_id
join date_dim d
    on cast(i.issue_date as date) = d.full_date
join time_dim t
    on extract(hour from i.issue_date) = t.time_key
join payment_method pm
    on i.payment_method = pm.payment_method