select
    employeeid::int        as employee_id,
    trim(employeename)     as employee_name,
    position                as position,
    gasstationid::int       as gasstation_id,
    phonenumber              as phone_number,
    email                     as email,
    startdate::date          as start_date,
    trim(address)             as address
from {{ source('gas_station_raw', 'employee') }}