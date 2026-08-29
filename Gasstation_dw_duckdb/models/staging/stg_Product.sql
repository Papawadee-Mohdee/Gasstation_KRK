with source as (
    select * from {{ source('gas_station_raw', 'product') }}
)
select
    ProductID::int         as product_id,
    trim(ProductName)      as product_name,
    UnitPrice::double      as unit_price,
    trim(ProductType)      as product_type,
    trim(Supplier)         as supplier,
    StockQuantity::double  as stock_quantity
from source