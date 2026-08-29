with source as (
    select * from {{ source('gas_station_raw', 'invoicedetail') }}
)
select
    InvoiceDetailID::int   as invoice_detail_id,
    InvoiceID::int         as invoice_id,
    ProductID::int         as product_id,
    QuantitySold::double   as quantity_sold,
    SellingPrice::double   as selling_price,
    TotalPrice::double     as total_price
from source