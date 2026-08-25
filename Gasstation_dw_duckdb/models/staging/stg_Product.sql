select
    productid::int        as product_id,
    productname            as product_name,
    unitprice::decimal      as unit_price,
    producttype              as product_type,
    supplier                  as supplier,
    stockquantity::int         as stock_quantity
from {{ source('gas_station_raw', 'product') }}