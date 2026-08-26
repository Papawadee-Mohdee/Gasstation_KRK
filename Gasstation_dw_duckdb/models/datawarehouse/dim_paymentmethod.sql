select
    row_number() over (order by payment_method) as paymentmethod_key,
    payment_method
from (
    select distinct payment_method
    from {{ ref('stg_Invoice') }}
)