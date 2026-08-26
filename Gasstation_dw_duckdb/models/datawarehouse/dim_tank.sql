select
    tank_id       as tank_key,
    tank_id,
    gasstation_id,
    tank_name,
    material_type,
    capacity_liters
from {{ ref('stg_StorageTank') }}