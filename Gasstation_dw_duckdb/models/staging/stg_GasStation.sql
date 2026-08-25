select
    gasstationid::int       as gasstation_id,
    trim(gasstationname)    as gasstation_name,
    trim(address)            as address,
    phonenumber               as phone_number,
    email                      as email,
    notes                      as notes
from {{ source('gas_station_raw', 'gasstation') }}