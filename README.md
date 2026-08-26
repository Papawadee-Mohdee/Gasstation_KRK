# Gasstation_KRK
Project Group1

# Members
- 673020045-9 นายประภากร มีใส
- 673020244-3 นายกิตติพัศ ลาล้ำ
- 673020256-6 นางสาวปภาวดี เหมาะดี
- 673020264-7 นางสาวสุกัญญา อุดมกัน
- 673020266-3 นางสาวสุพิชญา ผ่องสนาม
- 673020270-2 นางสาวอาทิติญา ชาชัย

##  Multidimensional Data Model: Dimension Tables (`dim_*`)

คลังข้อมูล **Gasstation_dw_duckdb** ถูกออกแบบตามสถาปัตยกรรม **Star Schema** โดยใช้ตารางมิติ (Dimension Tables) เป็นบริบทในการจำแนก วิเคราะห์ และเจาะลึกตัวเลขทางธุรกิจ (Measures) จากตารางแฟกต์ (`fact_sales` และ `fact_inventory`)

---

### 1. Dimension Tables Summary

| Dimension Table | Primary / Surrogate Key | Business Description | Hierarchy & Granularity |
| :--- | :--- | :--- | :--- |
| **`dim_customer`** | `CustomerID` | ข้อมูลลูกค้า ประวัติการติดต่อ และประเภทยานพาหนะ | Vehicle Type → Customer |
| **`dim_employee`** | `EmployeeID` | ข้อมูลพนักงาน ตำแหน่งงาน และสาขาที่สังกัด | Position → Employee |
| **`dim_gasstation`** | `GasStationID` | ข้อมูลสาขาสถานีบริการน้ำมันและที่ตั้ง | Region / Address → Gas Station |
| **`dim_product`** | `ProductID` | ข้อมูลประเภทน้ำมัน ราคาสินค้า และซัพพลายเออร์ | Product Type → Product Name |
| **`dim_tank`** | `TankID` | ข้อมูลถังจัดเก็บน้ำมัน ขนาดความจุ และประเภทวัสดุ | Material Type → Capacity → Tank |
| **`dim_paymentmethod`** | `PaymentMethod` | จำแนกช่องทางการชำระเงิน (Cash, Credit Card, QR) | Payment Category → Payment Method |
| **`dim_date`** | `date_key` (`full_date`) | มิติเวลาในระดับวัน สำหรับวิเคราะห์แนวโน้มตามช่วงเวลา | Year → Quarter → Month → Day |
| **`dim_time`** | `time_key` (`hour`) | มิติเวลาในระดับชั่วโมง สำหรับวิเคราะห์ช่วงเวลาหนาแน่น | Time Period (Shift/Peak) → Hour |

---

### 2. Schema Specifications & Attributes

#### `dim_customer`
* **Objective:** วิเคราะห์พฤติกรรมการซื้อ สัดส่วนประเภทยานพาหนะ และข้อมูลประชากรของลูกค้า
* **Key Attributes:** `CustomerID`, `CustomerName`, `Address`, `PhoneNumber`, `Email`, `VehicleTypeName`, `LicensePlate`, `Notes`

#### `dim_employee`
* **Objective:** ประเมินประสิทธิภาพการทำงาน ยอดขายรายบุคคล และการบริหารกำลังคนในแต่ละสาขา
* **Key Attributes:** `EmployeeID`, `EmployeeName`, `Position`, `GasStationID`, `PhoneNumber`, `Email`, `StartDate`

#### `dim_gasstation`
* **Objective:** เปรียบเทียบผลประกอบการ ยอดขาย และปริมาณการจ่ายน้ำมันจำแนกตามสาขา
* **Key Attributes:** `GasStationID`, `GasStationName`, `Address`, `PhoneNumber`, `Email`, `Notes`

#### `dim_product`
* **Objective:** วิเคราะห์ความต้องการซื้อ สัดส่วนรายได้ และราคาขายของน้ำมันแต่ละชนิด (`RON95`, `E5 RON92`, `Diesel`)
* **Key Attributes:** `ProductID`, `ProductName`, `UnitPrice`, `ProductType`, `Supplier`

#### `dim_tank`
* **Objective:** ติดตามความจุ ถังจัดเก็บน้ำมัน และประสิทธิภาพการหมุนเวียนสต็อกในแต่ละสาขา
* **Key Attributes:** `TankID`, `GasStationID`, `TankName`, `Capacity`, `MaterialType`

#### `dim_paymentmethod`
* **Objective:** สรุปสัดส่วนพฤติกรรมการชำระเงินของลูกค้าเพื่อวางแผนระบบรับชำระเงิน
* **Key Attributes:** `PaymentMethodName`

#### `dim_date`
* **Objective:** วิเคราะห์ข้อมูลอนุกรมเวลา (Time-Series) คำนวณอัตราการเติบโต YoY/MoM และช่วงฤดูกาล
* **Key Attributes:** `date_key`, `full_date`, `year`, `quarter`, `month`, `month_name`, `day`, `day_of_week`

#### `dim_time`
* **Objective:** จำแนกช่วงเวลาหนาแน่น (Peak Hours) และพฤติกรรมการเข้าใช้บริการในแต่ละรอบวัน
* **Key Attributes:** `time_key`, `hour`, `time_of_day` *(e.g., Morning, Afternoon, Evening, Night)*

---

### 3. Data Lineage Flow (dbt Transformation)

```text
[ Staging Layer (OLTP Source) ]          [ Data Warehouse Layer (OLAP) ]
stg_Customer.sql                  ───►   dim_customer.sql
stg_Employee.sql                  ───►   dim_employee.sql
stg_GasStation.sql                 ───►   dim_gasstation.sql
stg_Product.sql                    ───►   dim_product.sql
stg_InventoryTransaction.sql       ───►   dim_tank.sql
stg_Invoice.sql                    ───►   dim_paymentmethod.sql / dim_date.sql / dim_time.sql
