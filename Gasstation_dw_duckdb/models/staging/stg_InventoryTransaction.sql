select
    transactionid::int      as transaction_id,
    tankid::int              as tank_id,
    quantityin::decimal        as quantity_in,
    quantityout::decimal         as quantity_out,
    remainingquantity::decimal     as remaining_quantity,
    strptime(transactiondate, '%d/%m/%Y %H:%M')::timestamp as transaction_date
from {{ source('gas_station_raw', 'inventorytransaction') }}