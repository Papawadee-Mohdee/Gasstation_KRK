-- ไม่มี ProductID ใน StorageTank: อนุมานจากชื่อถังที่ตัดคำว่า " Tank" เท่านั้น
with source as (
    select TankID::integer as tank_id,
        GasStationID::integer as gas_station_id,
        TankName as tank_name,
        Capacity::decimal(18,4) as capacity,
        MaterialType as material_type,
        CurrentQuantity::decimal(18,4) as current_quantity_snapshot,
        trim(regexp_replace(TankName, ' Tank$', '')) as inferred_product_name
    from {{ ref('stg_storagetank') }}
),
unique_source as (
    select *, row_number() over (partition by tank_id order by tank_id) as row_num
    from source
)
select s.* exclude(row_num), p.product_id,
    case when p.product_id is null then 'unmapped' else 'derived_from_tank_name' end as mapping_method,
    current_localtimestamp() as insertion_timestamp
from unique_source s
left join {{ ref('dim_products') }} p on s.inferred_product_name = p.product_name
where row_num = 1
