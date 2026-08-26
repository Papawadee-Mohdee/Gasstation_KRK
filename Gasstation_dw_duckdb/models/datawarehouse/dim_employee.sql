select
    employee_id   as employee_key,
    employee_id,
    employee_name,
    position,
    gasstation_id as home_gasstation_id,
    phone_number,
    email,
    start_date
from {{ ref('stg_Employee') }}