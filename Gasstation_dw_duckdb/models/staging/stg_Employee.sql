with source as (
    select * from {{ source('gas_station_raw', 'employee') }}
)
select
    EmployeeID::int        as employee_id,
    trim(EmployeeName)     as employee_name,
    trim(Position)         as position,
    GasStationID::int      as gasstation_id,
    PhoneNumber            as phone_number,
    Email                  as email,
    StartDate::date        as start_date,
    trim(Address)          as address
from source