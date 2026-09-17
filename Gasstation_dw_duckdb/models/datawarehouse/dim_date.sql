with source as (
    select
    cast(strptime(IssueDate, '%d/%m/%Y %H:%M') as date) as date_day
    from {{ ref('stg_invoice') }}

    union

    select
    cast(strptime(TransactionDate, '%d/%m/%Y %H:%M') as date) as date_day
    from {{ ref('stg_inventorytransaction') }}
),
date_spine as (
    select unnest(generate_series(min(date_day), max(date_day), interval 1 day))::date as date_day
    from source
)
select strftime(date_day, '%Y%m%d')::integer as date_id, date_day,
    year(date_day) as year, quarter(date_day) as quarter,
    month(date_day) as month, day(date_day) as day,
    isodow(date_day) as weekday_number, dayname(date_day) as weekday_name,
    case when isodow(date_day) in (6,7) then 'Weekend' else 'Weekday' end as day_type
from date_spine
