{{ config(materialized='table') }}
with source as (
    select * from {{ ref('station_region_map') }}
)
select station_id as gasstation_key, region as region_key
from source
