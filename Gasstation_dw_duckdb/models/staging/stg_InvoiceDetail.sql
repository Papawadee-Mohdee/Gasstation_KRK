select
    invoicedetailid::int   as invoice_detail_id,
    invoiceid::int           as invoice_id,
    productid::int             as product_id,
    quantitysold::decimal        as quantity_sold,
    sellingprice::decimal          as selling_price,
    totalprice::decimal              as total_price
from {{ source('gas_station_raw', 'invoicedetail') }}