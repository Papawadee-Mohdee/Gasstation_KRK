with bounds as (
    select
        min(d) as min_d,
        max(d) as max_d
    from (
        select cast(issue_date as date) as d from {{ ref('stg_Invoice') }}
        union all
        select cast(transaction_date as date) as d from {{ ref('stg_InventoryTransaction') }}
    )
),
days as (
    select generate_series::date as full_date
    from bounds, generate_series(bounds.min_d, bounds.max_d, interval 1 day)
)
select
    cast(strftime(full_date, '%Y%m%d') as integer) as date_key,
    full_date,
    extract(year from full_date)      as year,
    extract(quarter from full_date)   as quarter,
    extract(month from full_date)     as month,
    strftime(full_date, '%B')         as month_name,
    extract(day from full_date)       as day_of_month,
    extract(isodow from full_date)    as iso_day_of_week,
    strftime(full_date, '%A')         as day_name,
    case when extract(isodow from full_date) in (6,7)
         then true else false end     as is_weekend
from days
order by full_date