# Gasstation_KRK
Project Group1

# Members
- 673020045-9 นายประภากร มีใส
- 673020244-3 นายกิตติพัศ ลาล้ำ
- 673020256-6 นางสาวปภาวดี เหมาะดี
- 673020264-7 นางสาวสุกัญญา อุดมกัน
- 673020266-3 นางสาวสุพิชญา ผ่องสนาม
- 673020270-2 นางสาวอาทิติญา ชาชัย

## Data Warehouse Architecture & Dimensional Modeling

คลังข้อมูล **GasStation Data Warehouse** ออกแบบตามหลักการ **Star Schema Modeling** โดยแบ่งออกเป็น **8 Dimension Tables** และ **2 Fact Tables** เพื่อรองรับการวิเคราะห์ข้อมูลเชิงลึกด้านยอดขาย (Sales Analytics) และการบริหารจัดการน้ำมันคงคลัง (Inventory Management)
---
### 1. Data Model Summary (ภาพรวมตารางทั้งหมด)

| Table Name | Model Type | Key / Primary Key | Primary Source / Logic | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`dim_customer`** | Dimension | `customer_key` | `stg_Customer` | ข้อมูลลูกค้า ประเภทยานพาหนะ และเลขทะเบียน |
| **`dim_employee`** | Dimension | `employee_key` | `stg_Employee` | ข้อมูลพนักงาน ตำแหน่ง และสาขาประจำ |
| **`dim_gasstation`** | Dimension | `gasstation_key` | `stg_GasStation` | ข้อมูลสาขาสถานีบริการน้ำมันและที่ตั้ง |
| **`dim_product`** | Dimension | `product_key` | `stg_Product` | ข้อมูลชนิดน้ำมัน/สินค้า และราคาตั้งขาย |
| **`dim_tank`** | Dimension | `tank_key` | `stg_StorageTank` | ข้อมูลถังจัดเก็บน้ำมัน วัสดุ และขนาดความจุ |
| **`dim_paymentmethod`** | Dimension | `paymentmethod_key` | `stg_Invoice` (Distinct) | ช่องทางการชำระเงิน (สร้าง Key ด้วย Row Number) |
| **`dim_date`** | Dimension | `date_key` (YYYYMMDD) | Dynamic Min/Max Date | มิติวัน (คำนวณช่วงวันออโต้จาก Invoice & Inventory) |
| **`dim_time`** | Dimension | `time_key` (0-23) | `range(0, 24)` | มิติเวลาในรอบวัน และการแบ่งช่วงเวลา (Day Part) |
| **`fact_sales`** | Fact | `invoice_detail_id` | `stg_Invoice` + `stg_InvoiceDetail` | แฟกต์รายการขายน้ำมันรายธุรกรรม (Sales Fact) |
| **`fact_inventory`** | Fact | `transaction_id` | `stg_InventoryTransaction` + `stg_StorageTank` | แฟกต์การเคลื่อนไหวสต็อกน้ำมันในถัง (Inventory Fact) |

---

### 2. Dimension Tables Detail (ตารางมิติ)

#### 🔹 `dim_customer`
* **Source:** `stg_Customer`
* **Description:** จัดเก็บประวัติลูกค้า ข้อมูลติดต่อ และจำแนกกลุ่มยานพาหนะ
* **Attributes:** `customer_key` (PK), `customer_id`, `customer_name`, `address`, `phone_number`, `email`, `vehicle_type`, `vehicle_category`, `license_plate`

#### 🔹 `dim_employee`
* **Source:** `stg_Employee`
* **Description:** จัดเก็บข้อมูลพนักงาน ตำแหน่งงาน และสาขาหลักที่สังกัด (`home_gasstation_id`)
* **Attributes:** `employee_key` (PK), `employee_id`, `employee_name`, `position`, `home_gasstation_id`, `phone_number`, `email`, `start_date`

#### 🔹 `dim_gasstation`
* **Source:** `stg_GasStation`
* **Description:** รายละเอียดสาขาสถานีบริการน้ำมัน ช่องทางติดต่อ และสถานที่ตั้ง
* **Attributes:** `gasstation_key` (PK), `gasstation_id`, `gasstation_name`, `address`, `phone_number`, `email`

#### 🔹 `dim_product`
* **Source:** `stg_Product`
* **Description:** รายการชนิดน้ำมันเชื้อเพลิง/สินค้า ซัพพลายเออร์ และราคาตั้งขาย (`list_unit_price`)
* **Attributes:** `product_key` (PK), `product_id`, `product_name`, `product_type`, `supplier`, `list_unit_price`

#### 🔹 `dim_tank`
* **Source:** `stg_StorageTank`
* **Description:** ข้อมูลถังจัดเก็บน้ำมันในแต่ละสาขา ประเภทวัสดุ และขนาดความจุ (ลิตร)
* **Attributes:** `tank_key` (PK), `tank_id`, `gasstation_id`, `tank_name`, `material_type`, `capacity_liters`

#### 🔹 `dim_paymentmethod`
* **Source:** `stg_Invoice` (Distinct `payment_method`)
* **Logic:** ดึงรายการรูปแบบชำระเงินที่ไม่ซ้ำกัน และสร้าง Surrogate Key ด้วย `row_number()`
* **Attributes:** `paymentmethod_key` (PK), `payment_method`

#### 🔹 `dim_date`
* **Source:** Dynamic Date Series Generator
* **Logic:** หาค่าวันที่เริ่มต้น (`min_d`) ถึงวันสิ้นสุด (`max_d`) จากการทำ Union ระหว่าง `stg_Invoice.issue_date` และ `stg_InventoryTransaction.transaction_date` แล้วสร้าง Date Dimension แบบอัตโนมัติ
* **Attributes:** 
  * `date_key` (Integer: YYYYMMDD)
  * `full_date` (Date)
  * `year`, `quarter`, `month`, `month_name`, `day_of_month`
  * `iso_day_of_week`, `day_name`
  * `is_weekend` (Boolean: `true` สำหรับเสาร์-อาทิตย์)

#### 🔹 `dim_time`
* **Source:** `range(0, 24)`
* **Logic:** สร้างชั่วโมง 0 ถึง 23 พร้อมแบ่งช่วงเวลาการทำงาน/บริการ (`day_part`)
* **Attributes:** 
  * `time_key` / `hour_24` (0 - 23)
  * `day_part`:
    * `Morning (05-10)` : 05:00 - 10:59 น.
    * `Midday (11-13)` : 11:00 - 13:59 น.
    * `Afternoon (14-17)` : 14:00 - 17:59 น.
    * `Evening (18-21)` : 18:00 - 21:59 น.
    * `Night (22-04)` : 22:00 - 04:59 น.

---

### 3. Fact Tables Detail (ตารางแฟกต์)

#### `fact_sales` (Sales Transactions Fact)
* **Grain:** 1 แถว ต่อ 1 รายการสินค้าในใบเสร็จรับเงิน (Invoice Detail Item)
* **Source Tables:** `stg_InvoiceDetail` (Main)  JOIN `stg_Invoice`, `dim_date`, `dim_time`, `dim_paymentmethod`
* **Foreign Keys:** `date_key`, `time_key`, `customer_key`, `employee_key`, `gasstation_key`, `product_key`, `paymentmethod_key`
* **Degenerate Dimensions:** `invoice_id`, `invoice_detail_id`
* **Fact Measures:**
  * `quantity_sold`: ปริมาณน้ำมันที่ขาย (ลิตร)
  * `selling_price`: ราคาขายต่อหน่วย ณ ช่วงเวลานั้น
  * `total_price`: มูลค่ายอดขายรวมสุทธิ (`quantity_sold * selling_price`)
  * `line_count`: ค่าคงที่ (1) สำหรับใช้นับจำนวนรายการขาย

####  `fact_inventory` (Inventory Transactions Fact)
* **Grain:** 1 แถว ต่อ 1 ธุรกรรมการรับ/จ่ายน้ำมันในถังเก็บ (Storage Tank Transaction)
* **Source Tables:** `stg_InventoryTransaction` (Main) JOIN `stg_StorageTank`, `dim_date`, `dim_time`
* **Foreign Keys:** `date_key`, `time_key`, `tank_key`, `gasstation_key` (เชื่อมผ่าน `stg_StorageTank`)
* **Degenerate Dimensions:** `transaction_id`
* **Fact Measures:**
  * `quantity_in`: ปริมาณน้ำมันที่รับเข้าถัง (ลิตร)
  * `quantity_out`: ปริมาณน้ำมันที่จ่ายออกจากถัง (ลิตร)
  * `remaining_quantity`: ปริมาณน้ำมันคงเหลือในถังหลังทำรายการ (ลิตร)

---

### 4. Data Lineage Flow (การเชื่อมโยงข้อมูล dbt Transformation)

```text
[ STAGING LAYER (OLTP) ]                [ DATA WAREHOUSE LAYER (OLAP) ]

stg_Customer ─────────────────────────► dim_customer
stg_Employee ─────────────────────────► dim_employee
stg_GasStation ───────────────────────► dim_gasstation
stg_Product ──────────────────────────► dim_product
stg_StorageTank ──────────────────────► dim_tank

stg_Invoice (payment_method) ─────────► dim_paymentmethod
stg_Invoice + stg_InventoryTxn ───────► dim_date (Dynamic bounds)
range(0, 24) ─────────────────────────► dim_time

stg_InvoiceDetail ──┐
stg_Invoice ────────┼─────────────────► fact_sales
dim_paymentmethod ──┤
dim_date / dim_time ┘

stg_InventoryTransaction ──┐
stg_StorageTank ───────────┼──────────► fact_inventory
dim_date / dim_time ───────┘
