select
    product_id as product_key,
    product_id,
    product_name,
    product_type,
    supplier,
    unit_price as list_unit_price
from {{ ref('stg_Product') }}