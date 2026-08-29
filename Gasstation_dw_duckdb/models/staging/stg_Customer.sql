with source as (
    select * from {{ source('gas_station_raw', 'customer') }}
)
select
    CustomerID::int                      as customer_id,
    trim(CustomerName)                   as customer_name,
    trim(Address)                        as address,
    PhoneNumber                          as phone_number,
    Email                                as email,
    Notes                                as notes,
    coalesce(VehicleTypeName, 'Unknown') as vehicle_type,
    case
        when VehicleTypeName ilike 'Motorcycle%' then 'Motorcycle'
        when VehicleTypeName in ('Sedan','SUV') then 'Passenger Car'
        when VehicleTypeName in ('Pickup Truck','Light Truck') then 'Truck'
        else 'Other'
    end                                  as vehicle_category,
    LicensePlate                         as license_plate
from source