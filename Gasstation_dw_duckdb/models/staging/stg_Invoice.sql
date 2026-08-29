with source as (
    select * from {{ source('gas_station_raw', 'invoice') }}
)
select
    InvoiceID::int         as invoice_id,
    CustomerID::int        as customer_id,
    EmployeeID::int        as employee_id,
    GasStationID::int      as gasstation_id,
    strptime(IssueDate, '%d/%m/%Y %H:%M')::timestamp as issue_date,
    TotalAmount::double    as total_amount,
    trim(PaymentMethod)    as payment_method
from source