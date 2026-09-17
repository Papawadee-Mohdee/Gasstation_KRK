with source as (
    select
        CustomerID::integer as customer_id,
        CustomerName as customer_name,
        Address as address,
        PhoneNumber as phone_number,
        Email as email,
        Notes as notes,
        VehicleTypeName as vehicle_type_name,
        LicensePlate as license_plate,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_customer') }}
),
unique_source as (
    select *,
        row_number() over (partition by customer_id order by customer_id) as row_num
    from source
)
select * exclude (row_num)
from unique_source
where row_num = 1
