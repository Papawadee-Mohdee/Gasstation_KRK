with source as (
    select
        GasStationID::integer as gas_station_id,
        GasStationName as gas_station_name,
        Address as address,
        PhoneNumber as phone_number,
        Email as email,
        Notes as notes,
        trim(split_part(Address, ',', 1)) as street,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_gasstation') }}
),
unique_source as (
    select *,
        row_number() over (partition by gas_station_id order by gas_station_id) as row_num
    from source
)
select * exclude (row_num)
from unique_source
where row_num = 1
