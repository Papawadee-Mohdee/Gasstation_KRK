with source as (
    select * from {{ source('gas_station_raw', 'storagetank') }}
)
select
    TankID::int            as tank_id,
    GasStationID::int      as gasstation_id,
    trim(TankName)         as tank_name,
    Capacity::double       as capacity_liters,
    trim(MaterialType)     as material_type,
    CurrentQuantity::double as current_quantity
from source