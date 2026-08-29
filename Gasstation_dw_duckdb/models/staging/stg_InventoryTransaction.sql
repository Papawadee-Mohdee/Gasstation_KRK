with source as (
    select * from {{ source('gas_station_raw', 'inventorytransaction') }}
)
select
    TransactionID::int            as transaction_id,
    TankID::int                   as tank_id,
    QuantityIn::double            as quantity_in,
    QuantityOut::double           as quantity_out,
    RemainingQuantity::double     as remaining_quantity,
    strptime(TransactionDate, '%d/%m/%Y %H:%M')::timestamp as transaction_date
from source