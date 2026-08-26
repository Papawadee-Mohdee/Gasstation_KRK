select
    customer_id    as customer_key,
    customer_id,
    customer_name,
    address,
    phone_number,
    email,
    vehicle_type,
    vehicle_category,
    license_plate
from {{ ref('stg_Customer') }}