select
    customerid::int      as customer_id,
    trim(customername)   as customer_name,
    trim(address)         as address,
    phonenumber           as phone_number,
    email                  as email,
    notes                  as notes,
    coalesce(vehicletypename, 'Unknown') as vehicle_type,
    case
        when vehicletypename ilike 'Motorcycle%' then 'Motorcycle'
        when vehicletypename in ('Sedan','SUV') then 'Passenger Car'
        when vehicletypename in ('Pickup Truck','Light Truck') then 'Truck'
        else 'Other'
    end                    as vehicle_category,
    licenseplate           as license_plate
from {{ source('gas_station_raw', 'customer') }}