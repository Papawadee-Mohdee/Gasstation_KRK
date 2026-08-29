with source as (
    select * from {{ source('gas_station_raw', 'gasstation') }}
)
select
    GasStationID::int      as gasstation_id,
    trim(GasStationName)   as gasstation_name,
    trim(Address)          as address,
    PhoneNumber            as phone_number,
    Email                  as email,
    Notes                  as notes
from source