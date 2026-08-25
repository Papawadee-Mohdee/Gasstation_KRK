select
    tankid::int             as tank_id,
    gasstationid::int         as gasstation_id,
    tankname                    as tank_name,
    capacity::int                 as capacity_liters,
    materialtype                    as material_type,
    currentquantity::decimal          as current_quantity
from {{ source('gas_station_raw', 'storagetank') }}