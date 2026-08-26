select
    gasstation_id as gasstation_key,
    gasstation_id,
    gasstation_name,
    address,
    phone_number,
    email
from {{ ref('stg_GasStation') }}