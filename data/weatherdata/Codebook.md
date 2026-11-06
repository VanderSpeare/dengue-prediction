# Codebook — PM2.5 TP.HCM Dataset

## Thông Tin Chung

| Mục | Nội dung |
|---|---|
| **Tên dataset** | PM2.5 TP.HCM — Hourly Time Series |
| **Đơn vị quan sát** | 1 hàng = 1 giờ tại TP.HCM |
| **Tần suất** | Theo giờ (hourly) |
| **Múi giờ** | Asia/Ho_Chi_Minh (UTC+7) |
| **Phạm vi** | 2024 → nay |
| **Nguồn** | OpenAQ API + Open-Meteo Archive API |
| **Số features cuối** | 31 features (sử dụng cho training) — CSV lưu 33 cột, loại 2 cột trước khi train |

---

##  Phân Nhóm Biến

### Nhóm 1 — Metadata / Index

| Tên cột | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `time` | datetime64[ns] | — | Timestamp theo giờ, múi giờ Asia/Ho_Chi_Minh (không có tzinfo sau khi xử lý) |

---

### Nhóm 2 — Biến Khí Tượng (Đã Scale)


| Tên cột | Kiểu | Đơn vị gốc | Mô tả | Nguồn |
|---|---|---|---|---|
| `temperature` | float64 | °C | Nhiệt độ không khí tại độ cao 2m | Open-Meteo |
| `humidity` | float64 | % | Độ ẩm tương đối (0–100) | Open-Meteo |
| `wind_speed` | float64 | km/h | Tốc độ gió tại độ cao 10m | Open-Meteo |
| `pressure` | float64 | hPa | Áp suất khí quyển bề mặt | Open-Meteo |
| `precipitation` | float64 | mm | Lượng mưa tích lũy trong giờ | Open-Meteo |

---

### Nhóm 3 — Biến Thời Gian (Cyclic)

| Tên cột | Kiểu | Giá trị | Mô tả | Cách tạo |
|---|---|---|---|---|
| `hour` | int64 | 0 – 23 | Giờ trong ngày | `df['time'].dt.hour` |
| `month` | int64 | 1 – 12 | Tháng trong năm | `df['time'].dt.month` |
| `dayofweek` | int64 | 0 (T2) – 6 (CN) | Thứ trong tuần | `df['time'].dt.dayofweek` |
| `hour_sin` | float64 | [-1, 1] | Cyclical encoding giờ (phần sin) | `sin(2π × hour / 24)` |
| `hour_cos` | float64 | [-1, 1] | Cyclical encoding giờ (phần cos) | `cos(2π × hour / 24)` |
| `month_sin` | float64 | [-1, 1] | Cyclical encoding tháng (phần sin) | `sin(2π × month / 12)` |
| `month_cos` | float64 | [-1, 1] | Cyclical encoding tháng (phần cos) | `cos(2π × month / 12)` |
| `dow_sin` | float64 | [-1, 1] | Cyclical encoding thứ (phần sin) | `sin(2π × dayofweek / 7)` |
| `dow_cos` | float64 | [-1, 1] | Cyclical encoding thứ (phần cos) | `cos(2π × dayofweek / 7)` |

> **Lý do dùng cyclical encoding:** Giờ 23 và giờ 0 thực ra rất gần nhau, nhưng nếu dùng giá trị số nguyên thì khoảng cách là 23. Sin/cos encoding giải quyết vấn đề này bằng cách giữ tính liên tục vòng tròn.

---

### Nhóm 4 — Biến PM2.5 Gốc & Flags

| Tên cột | Kiểu | Đơn vị | Mô tả | Ghi chú |
|---|---|---|---|---|
| `pm25_raw` | float64 | µg/m³ | PM2.5 sau khi impute, **chưa scale** | Dùng làm base cho tất cả lag/rolling features |
| `pm25_interpolated` | bool | — | `True` nếu hàng này đã được nội suy (không có đo thực) | Dùng để audit chất lượng data |
| `pm25_outlier_iqr` | int64 | 0/1 | `1` nếu PM2.5 nằm ngoài [Q1 − 1.5×IQR, Q3 + 1.5×IQR] (fit trên Train) | Chỉ flag, không xóa |
| `n_obs` | int64 | count | Số trạm đo có giá trị hợp lệ trong giờ đó | Từ bước group-by OpenAQ |

---

### Nhóm 5 — Lag Features

> **Tất cả tính từ `pm25_raw`** (giá trị gốc µg/m³) để tránh data leakage.

| Tên cột | Kiểu | Đơn vị | Mô tả | Cách tạo |
|---|---|---|---|---|
| `pm25_lag_1` | float64 | µg/m³ | PM2.5 tại thời điểm t−1h | `pm25_raw.shift(1)` |
| `pm25_lag_3` | float64 | µg/m³ | PM2.5 tại thời điểm t−3h | `pm25_raw.shift(3)` |
| `pm25_lag_6` | float64 | µg/m³ | PM2.5 tại thời điểm t−6h | `pm25_raw.shift(6)` |
| `pm25_lag_24` | float64 | µg/m³ | PM2.5 cùng giờ hôm qua (t−24h) | `pm25_raw.shift(24)` |
| `pm25_lag_168` | float64 | µg/m³ | PM2.5 cùng giờ tuần trước (t−168h) | `pm25_raw.shift(168)` |

> **Justify bởi ACF/PACF:** ACF cho thấy autocorrelation có spike rõ tại lag 1, 24 và 168 → các lag này mang nhiều thông tin nhất.

---

### Nhóm 6 — Rolling Statistics

> Sử dụng `shift(1)` trước khi rolling để đảm bảo không dùng giá trị hiện tại (`t`) khi tính thống kê cho điểm `t`.

| Tên cột | Kiểu | Đơn vị | Mô tả | Cách tạo |
|---|---|---|---|---|
| `pm25_roll_mean_24` | float64 | µg/m³ | Trung bình PM2.5 trong 24h gần nhất (không kể t) | `raw.shift(1).rolling(24).mean()` |
| `pm25_volatility_24` | float64 | µg/m³ | Độ biến động / lệch chuẩn PM2.5 trong 24h | `raw.shift(1).rolling(24).std()` |
| `pm25_roll_max_24` | float64 | µg/m³ | Giá trị max PM2.5 trong 24h | `raw.shift(1).rolling(24).max()` |
| `pm25_roll_min_24` | float64 | µg/m³ | Giá trị min PM2.5 trong 24h | `raw.shift(1).rolling(24).min()` |
| `pm25_roll_mean_168` | float64 | µg/m³ | Trung bình PM2.5 trong 168h (1 tuần) | `raw.shift(1).rolling(168).mean()` |

---

### Nhóm 7 — Difference Features

> **Justify bởi Stationarity test:** ADF/KPSS cho thấy chuỗi có thể difference-stationary → diff features giúp model capture tốc độ thay đổi.

| Tên cột | Kiểu | Đơn vị | Mô tả | Cách tạo |
|---|---|---|---|---|
| `pm25_diff_1` | float64 | µg/m³/h | Tốc độ thay đổi PM2.5 so với 1h trước | `raw.shift(1).diff(1)` |
| `pm25_diff_24` | float64 | µg/m³/h | Thay đổi PM2.5 so với cùng giờ hôm qua | `raw.shift(1).diff(24)` |

---

### Nhóm 8 — Biến Mưa & Weather Interactions

| Tên cột | Kiểu | Đơn vị | Mô tả | Cách tạo | Ghi chú |
|---|---|---|---|---|---|
| `precipitation_log` | float64 | log(mm) | Log transform lượng mưa (đã scale) | `log1p(precipitation)` | Xử lý phân phối lệch phải cực mạnh của mưa |
| `is_rain` | int64 | 0/1 | Có mưa trong giờ không | `(precipitation > 0).astype(int)` | Feature nhị phân bổ sung |
| `temp_humidity` | float64 | — | Tương tác nhiệt độ × độ ẩm | `temperature × humidity` | Capture hiệu ứng phi tuyến |
| `temp_diff_1` | float64 | °C/h | Tốc độ thay đổi nhiệt độ trong 1h | `temperature.shift(1).diff(1).fillna(0)` | `fillna(0)` để tránh NaN hàng đầu |
| `humidity_diff_1` | float64 | %/h | Tốc độ thay đổi độ ẩm trong 1h | `humidity.shift(1).diff(1).fillna(0)` | `fillna(0)` để tránh NaN hàng đầu |

---

### Nhóm 9 — Target Variable

| Tên cột | Kiểu | Đơn vị | Mô tả | Ghi chú |
|---|---|---|---|---|
| `pm25` | float64 | scaled | **TARGET** — Nồng độ PM2.5 đã được RobustScaler transform | Để inverse về µg/m³: `pm25_scaler.inverse_transform(...)` |

---
---

##  Quy Tắc Chất Lượng Dữ Liệu

| Quy tắc | Giá trị |
|---|---|
| Giá trị PM2.5 hợp lệ | [0, 400] µg/m³ (loại âm và > 400) |
| Giá trị sentinel bị loại | -999, -999.0 |
| Giới hạn nội suy PM2.5 | Tối đa 3 giờ liên tiếp |
| Giới hạn forward-fill khí tượng | Tối đa 3 giờ liên tiếp |
| Đứt gãy bị loại | > 7 ngày liên tục không có dữ liệu |
| Ngưỡng outlier IQR | Q1 − 1.5×IQR đến Q3 + 1.5×IQR (fit trên Train) |

---

##  Tiêu Chuẩn WHO Tham Chiếu

| Mức | Ngưỡng PM2.5 | Ý nghĩa |
|---|---|---|
| WHO Annual Guideline | 5 µg/m³ | Tiêu chuẩn hàng năm |
| WHO 24h Guideline | 15 µg/m³ | Tiêu chuẩn 24h (dùng trong notebook) |
| WHO Interim Target 3 | 25 µg/m³ | Mục tiêu trung gian |
| Nguy hiểm (Việt Nam) | > 75 µg/m³ | Theo QCVN 05:2023 |

---
## Sơ Đồ Nguồn Gốc Biến
```text
OpenAQ CSV
└─ value → pm25 → [làm sạch, nhóm theo giờ] → pm25_raw
│
┌──────────────┼──────────────────┐
lag features   rolling features   diff features
Open-Meteo API
└─ temperature, humidity, wind_speed, pressure, precipitation
│
├─ [log1p] → precipitation_log
├─ [binary] → is_rain
├─ [product] → temp_humidity
└─ [diff] → temp_diff_1, humidity_diff_1
time column
└─ dt.hour → hour → [sin/cos] → hour_sin, hour_cos
└─ dt.month → month → [sin/cos] → month_sin, month_cos
└─ dt.dayofweek → dayofweek → [sin/cos] → dow_sin, dow_cos
```