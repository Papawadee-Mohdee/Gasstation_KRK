with source as (
    select
        EmployeeID::integer as employee_id,
        EmployeeName as employee_name,
        Position as position,
        GasStationID::integer as assigned_gas_station_id,
        PhoneNumber as phone_number,
        Email as email,
        StartDate::date as start_date,
        Address as address,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_employee') }}
),
unique_source as (
    select *,
        row_number() over (partition by employee_id order by employee_id) as row_num
    from source
)
select * exclude (row_num)
from unique_source
where row_num = 1
