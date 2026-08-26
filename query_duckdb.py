import duckdb
import pandas as pd

# Connect to the DuckDB database
conn = duckdb.connect('Gasstation_dw_duckdb/dev.duckdb')

# Get all table names
tables = conn.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
).fetchall()

print("Tables in dev.duckdb:")
for table in tables:
    print(f"  - {table[0]}")

def show_table(table_name, limit=20):
    print("\n" + "=" * 80)
    print(f"Table: {table_name}")
    print("=" * 80)
    result = conn.execute(f'SELECT * FROM main."{table_name}" LIMIT {limit}').fetchall()
    df = pd.DataFrame(result, columns=[desc[0] for desc in conn.description])
    print(df)
    return df

# --- Staging layer ---
show_table("stg_Customer")
show_table("stg_Employee")
show_table("stg_GasStation")
show_table("stg_Invoice")
show_table("stg_InvoiceDetail")
show_table("stg_Product")
show_table("stg_StorageTank")
show_table("stg_InventoryTransaction")

# --- Dimension tables ---
show_table("dim_date")
show_table("dim_time")
show_table("dim_customer")
show_table("dim_employee")
show_table("dim_gasstation")
show_table("dim_product")
show_table("dim_paymentmethod")
show_table("dim_tank")

# --- Fact tables (ถ้าสร้างแล้ว) ---
# show_table("fct_sales")
# show_table("fct_inventory")

conn.close()