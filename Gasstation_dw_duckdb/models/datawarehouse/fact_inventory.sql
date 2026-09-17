-- Grain: หนึ่งแถวต่อ TransactionID; remaining_quantity ห้ามรวมข้ามเวลา
with source as (
    select * from {{ ref('stg_inventorytransaction') }}
)
select s.TransactionID::bigint as transaction_id,
    s.TankID::integer as tank_id, t.gas_station_id, t.product_id,
    strptime(s.TransactionDate, '%d/%m/%Y %H:%M') as transaction_timestamp,
    strftime(strptime(s.TransactionDate, '%d/%m/%Y %H:%M'), '%Y%m%d')::integer as date_id,
    s.QuantityIn::decimal(18,4) as quantity_in,
    s.QuantityOut::decimal(18,4) as quantity_out,
    s.RemainingQuantity::decimal(18,4) as remaining_quantity,
    current_localtimestamp() as insertion_timestamp
from source s
left join {{ ref('dim_tanks') }} t on s.TankID::integer = t.tank_id
