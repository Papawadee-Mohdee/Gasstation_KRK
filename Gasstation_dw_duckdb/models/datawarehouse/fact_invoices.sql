-- Grain: หนึ่งแถวต่อ InvoiceID ใช้นับบิลและยอดขายรวมสถานี
with source as (
    select * from {{ ref('stg_invoice') }}
)
select InvoiceID::bigint as invoice_id,
    CustomerID::integer as customer_id, EmployeeID::integer as employee_id,
    GasStationID::integer as gas_station_id,
    strptime(IssueDate, '%d/%m/%Y %H:%M') as issue_timestamp,
    strftime(
    strptime(IssueDate, '%d/%m/%Y %H:%M'),
    '%Y%m%d'
)::integer as date_id,
    hour(strptime(IssueDate, '%d/%m/%Y %H:%M'))::integer as hour_id,
    TotalAmount::decimal(18,2) as total_amount,
    PaymentMethod as payment_method,
    1 as invoice_count,
    current_localtimestamp() as insertion_timestamp
from source
