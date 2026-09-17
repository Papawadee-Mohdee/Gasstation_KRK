with source as (
    select
        ProductID::integer as product_id,
        ProductName as product_name,
        UnitPrice::decimal(18,2) as unit_price,
        ProductType as product_type,
        Supplier as supplier,
        StockQuantity::decimal(18,4) as stock_quantity_snapshot,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_product') }}
),
unique_source as (
    select *,
        row_number() over (partition by product_id order by product_id) as row_num
    from source
)
select * exclude (row_num)
from unique_source
where row_num = 1
