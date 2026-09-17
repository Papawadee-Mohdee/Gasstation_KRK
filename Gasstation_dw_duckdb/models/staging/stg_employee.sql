with source as (

    select * 
    from {{ source('gas_station_raw', 'employee') }}
)
select
    *,
    current_localtimestamp() as ingestion_timestamp
from source