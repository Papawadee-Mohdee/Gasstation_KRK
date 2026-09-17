{{ config(materialized='table') }}
with source as (
    select * from {{ ref('station_region_map') }}
)
select distinct region as region_key, region as region_name, mapping_basis
from source
