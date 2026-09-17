# Dashboard

รันจากโฟลเดอร์หลัก: `python -m pip install -r requirements-dashboard.txt` แล้ว `python -m streamlit run app.py`

แดชบอร์ดอ่าน Dim/Fact โดยตรง ไม่สร้าง mart และไม่ใช้ข้อมูลขายจำลอง แบ่งเป็นยอดขายและพื้นที่ สินค้าและการชำระเงิน ช่วงเวลาและการให้บริการ น้ำมันคงเหลือ พนักงานและประสิทธิภาพ

Region เป็นกลุ่มพื้นที่ธุรกิจสมมติ 4 กลุ่ม ไม่ใช่จังหวัดหรือภาคของประเทศไทย: รหัสสถานี 1–25, 26–50, 51–75, 76–100 ตามลำดับ แก้ mapping ใน `Gasstation_dw_duckdb/seeds/station_region_map.csv` เมื่อได้รับกลุ่มจริง จากโฟลเดอร์ Gasstation_dw_duckdb รัน `dbt seed --profiles-dir . --select station_region_map` และ `dbt run --profiles-dir . --select dim_region dim_station_region` สำเนา data/station_region_map.csv ใช้เฉพาะเมื่อยังไม่มีสอง dimension นี้

ตัวกรองวันที่ Region และสถานีใช้ทุกหน้า หน้าคงเหลือใช้ธุรกรรมล่าสุดถึงวันสิ้นสุด ไม่บวกยอดคงเหลือข้ามเวลา อัตราค่าธรรมเนียมเป็นสมมติฐานปรับได้ จำนวนพนักงานเป็น master snapshot จึงไม่ใช่จำนวนคนเข้ากะจริง การเปรียบเทียบวันธรรมดาและสุดสัปดาห์เป็นค่าเฉลี่ยต่อวัน ไม่ใช่ผลทดสอบทางสถิติ

หากเปลี่ยนฐานข้อมูล กำหนดตัวแปร GASSTATION_DB เป็น path ของไฟล์ DuckDB ที่มี Dim/Fact ครบ
