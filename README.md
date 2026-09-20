# Gasstation KRK Dashboard

ใช้ Python 3.12 และ virtual environment ชื่อ `.venv` เท่านั้น

## เปิดใช้งาน

Codespace ใหม่จะสร้าง `.venv` และติดตั้งแพ็กเกจให้อัตโนมัติ
สำหรับ Codespace เดิมหรือเครื่องใหม่ ให้เตรียมครั้งแรกด้วย:

```bash
bash scripts/setup.sh
```

จากโฟลเดอร์หลักของโปรเจกต์:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

เปิดหน้าแอปผ่านแท็บ **Ports** พอร์ต **8501** หยุดแอปด้วย Ctrl+C
เมื่อเปิด Terminal ใหม่ให้ activate อีกครั้ง ไม่ต้องสร้าง environment ใหม่

## ไฟล์ที่ใช้งาน

- `app.py`: dashboard ทั้ง 5 หมวด รวมตัวกรองและคำสั่ง SQL
- `warehouse_setup.py`: นำเข้า CSV และสร้าง Dim/Fact ด้วย dbt เมื่อยังไม่มีฐานข้อมูล
- `Gasstation_dw_duckdb/Datasets/`: ข้อมูลต้นทาง ต้องเก็บไว้เพื่อสร้างฐานข้อมูลใหม่
- `Gasstation_dw_duckdb/models/`: staging และ dimension/fact ที่ใช้สร้างคลังข้อมูล
- `Gasstation_dw_duckdb/dbt_project.yml`, `profiles.yml`: ตั้งค่า dbt
- `requirements.txt`: dependencies ที่โปรเจกต์ใช้โดยตรง
- `scripts/setup.sh`: สร้างหรือซ่อม .venv และติดตั้ง dependencies
- `.devcontainer/`, `.vscode/`, `.streamlit/`: ตั้งค่า Codespaces, Python และ Streamlit

ฐานข้อมูลหลักที่สร้างอัตโนมัติคือ `Gasstation_dw_duckdb/dev.duckdb`
การเปิดครั้งแรกอาจใช้เวลาหลายนาที ครั้งต่อไปใช้ฐานข้อมูลเดิม
ฐานข้อมูลที่สร้างแล้วและ .venv ไม่ถูกเก็บใน Git
หาก .venv เสีย ให้รัน `bash scripts/setup.sh` ซึ่งจะย้าย environment ที่เสียไปสำรองนอก repo ก่อนสร้างใหม่

## ข้อมูลบน dashboard

แสดงยอดขายและพื้นที่ สินค้าและการชำระเงิน ช่วงเวลาและการให้บริการ
น้ำมันคงเหลือ และพนักงานและประสิทธิภาพ โดยอ่าน Dim/Fact โดยตรง
ตัวกรองพื้นที่ใช้สายถนนจากข้อมูลสถานี ไม่ใช้การแบ่งภูมิภาคสมมติ
ปริมาณน้ำมันคงเหลือใช้ธุรกรรมล่าสุดถึงวันสิ้นสุดที่เลือก
ค่าธรรมเนียมบัตรเป็นการจำลอง และจำนวนพนักงานเป็น master snapshot ไม่ใช่คนเข้ากะจริง

หากต้องการใช้ฐานข้อมูลอื่น ให้กำหนด `GASSTATION_DB` เป็น path ของ DuckDB ที่มี Dim/Fact ครบ
แอปจะไม่เขียนทับฐานข้อมูลที่กำหนดเอง

โค้ดเก่าและไฟล์ที่เลิกใช้สามารถเรียกคืนได้จากประวัติ Git
