with inventory_txn as (
    select * from {{ ref('stg_InventoryTransaction') }}
),
tank as (
    select * from {{ ref('stg_StorageTank') }}
),
date_dim as (
    select * from {{ ref('dim_date') }}
),
time_dim as (
    select * from {{ ref('dim_time') }}
)

select
    d.date_key,
    t.time_key,
    it.tank_id             as tank_key,
    tk.gasstation_id         as gasstation_key,
    it.transaction_id          as transaction_id,        -- degenerate dimension
    it.quantity_in                                        as quantity_in,
    it.quantity_out                                         as quantity_out,
    it.remaining_quantity                                     as remaining_quantity

from inventory_txn it
join tank tk
    on it.tank_id = tk.tank_id
join date_dim d
    on cast(it.transaction_date as date) = d.full_date
join time_dim t
    on extract(hour from it.transaction_date) = t.time_key