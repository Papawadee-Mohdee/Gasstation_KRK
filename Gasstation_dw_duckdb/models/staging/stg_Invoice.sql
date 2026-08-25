select
    invoiceid::int          as invoice_id,
    customerid::int          as customer_id,
    employeeid::int           as employee_id,
    gasstationid::int          as gasstation_id,
    issuedate::timestamp        as issue_date,
    totalamount::decimal          as total_amount,
    paymentmethod                  as payment_method
from {{ source('gas_station_raw', 'invoice') }}