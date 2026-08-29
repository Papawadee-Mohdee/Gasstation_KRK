import duckdb
import glob
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'dev.duckdb')

# รายชื่อโฟลเดอร์ที่ค้นหาไฟล์ CSV
candidate_dirs = [
    os.path.join(base_dir, 'seeds'),
    base_dir,
    os.path.abspath(os.path.join(base_dir, '..')),
    os.path.abspath(os.path.join(base_dir, '..', 'seeds')),
]

csv_files = []
found_dir = None

for d in candidate_dirs:
    files = glob.glob(os.path.join(d, '*.csv'))
    # ค้นหาโฟลเดอร์ที่มีไฟล์ Customer.csv หรือ Invoice.csv อยู่จริง
    if any(os.path.basename(f).lower() in ['customer.csv', 'invoice.csv'] for f in files):
        csv_files = files
        found_dir = d
        break

print(f" Database Path: {db_path}")
print(f" Found CSV Directory: {found_dir}")
print(f" Found {len(csv_files)} CSV files\n")

if not csv_files:
    print("❌ ERROR: Could not find CSV files!")
    print("โปรดเช็กว่าไฟล์ Customer.csv, Invoice.csv อยู่ในโฟลเดอร์ไหน")
    exit(1)

conn = duckdb.connect(db_path)

for csv_file in sorted(csv_files):
    table_name = os.path.basename(csv_file).replace('.csv', '')
    print(f"Loading {table_name}...")
    conn.execute(f'CREATE OR REPLACE TABLE main."{table_name}" AS SELECT * FROM read_csv_auto(\'{csv_file}\');')
    count = conn.execute(f'SELECT count(*) FROM main."{table_name}"').fetchone()[0]
    print(f"   Successfully created main.\"{table_name}\" ({count:,} rows)")

print("\n--------------------------------------------------")
print(" All raw CSV tables loaded into DuckDB successfully!")
print("--------------------------------------------------")
conn.close()