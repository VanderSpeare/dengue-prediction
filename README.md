# Hệ Thống Giám Sát Dịch Tễ Cộng Đồng, Dự Báo Sốt Xuất Huyết Dựa Trên GIS, Dữ Liệu Khí Hậu & Trí Tuệ Nhân Tạo
## Community Epidemiological Surveillance, Spatial GIS Analytics & Climate-Enhanced Dengue Early Warning System

---

## 📖 MỤC LỤC
1. [Giới Thiệu Tổng Quan](#1-giới-thiệu-tổng-quan)
2. [Kiến Trúc Hệ Thống (System Architecture)](#2-kiến-trúc-hệ-thống-system-architecture)
3. [Tổng Hợp Các Thuật Toán Áp Dụng (Algorithms)](#3-tổng-hợp-các-thuật-toán-áp-dụng-algorithms)
4. [Tổng Hợp Các Phương Trình Toán Học & Thống Kê (Mathematical & Statistical Equations)](#4-tổng-hợp-các-phương-trình-toán-học--thống-kê-mathematical--statistical-equations)
5. [Tổng Hợp Các Công Nghệ Đã Áp Dụng (Technologies & Libraries)](#5-tổng-hợp-các-công-nghệ-đã-áp-dụng-technologies--libraries)
6. [Danh Sách Các Bài Báo Khoa Học & Tài Liệu Tham Khảo (Scientific Publications & References)](#6-danh-sách-các-bài-báo-khoa-học--tài-liệu-tham-khảo-scientific-publications--references)
7. [Tài Liệu Hướng Dẫn & Link Tài Nguyên Trực Tuyến (Official Documentation & Tutorials)](#7-tài-liệu-hướng-dẫn--link-tài-nguyên-trực-tuyến-official-documentation--tutorials)
8. [Hướng Dẫn Triển Khai & Khởi Chạy (Deployment & Execution)](#8-hướng-dẫn-triển-khai--khởi-chạy-deployment--execution)
9. [Tổng Hợp Các Sơ Đồ Thiết Kế Hệ Thống Phân Mảnh (Modular System Design Diagrams)](#9-tổng-hợp-các-sơ-đồ-thiết-kế-hệ-thống-phân-mảnh-modular-system-design-diagrams)

---

## 1. GIỚI THIỆU TỔNG QUAN

Dự án **Hệ Thống Giám Sát Dịch Tễ Cộng Đồng, Dự Báo Sốt Xuất Huyết Dựa Trên GIS, Dữ Liệu Khí Hậu & Trí Tuệ Nhân Tạo** là một giải pháp y tế số hiện đại được nghiên cứu và phát triển nhằm giải quyết triệt để bài toán cảnh báo sớm và giám sát véc-tơ truyền bệnh sốt xuất huyết Dengue tại các đô thị nhiệt đới (trọng tâm tại TP. Hồ Chí Minh và mở rộng 34 tỉnh/thành phố trên cả nước). Hệ thống tập trung toàn diện vào 4 trụ cột công nghệ cốt lõi:

- **Hệ Thống Thông Tin Địa Lý & Bản Đồ ArcGIS / Leaflet Đa Chiều (GIS & Spatial Analytics)**:
  - Kiến trúc bản đồ kép **ArcGIS Maps SDK for JavaScript 4.29 (2D `MapView` / 3D `SceneView`) song song với Leaflet**: hỗ trợ bật/tắt 4 tầng dữ liệu qua `LayerList`, `Legend`, `Search`, chọn Basemap (đường phố, vệ tinh, địa hình, nền tối) và chế độ hiển thị **Song Song** phù hợp cả người dân lẫn cán bộ chuyên môn HCDC.
  - Bản đồ nhiệt dịch tễ đa tầng (*Choropleth Map*) theo 34 tỉnh/thành phố (`vietnam_34_provinces_2025.geojson`) và ranh giới **Quận/Huyện TP. Hồ Chí Minh** (`hcmc_districts.geojson`, `hcmc_districts_risk.geojson`), cùng chi tiết phường/xã, tuyến đường trọng điểm TP.HCM.
  - Thuật toán khoanh vùng ổ dịch Geodesic Buffer (100m – 2000m) tự động phân tầng 4 mức độ nguy cơ (Vùng Đỏ, Cam, Vàng, Xanh) trên hệ quy chiếu chuẩn WGS84 (EPSG:4326).
- **Học Máy Dự Báo Đa Cấp & Đa Biến Môi Trường - Khí Hậu (Climate-Enhanced XGBoost Regressor)**:
  - Dự báo chuỗi thời gian đệ quy số ca mắc sốt xuất huyết 3 tháng tương lai (Holdout Out-of-Time) ở cả **2 cấp**: **34 Tỉnh/Thành phố** (`train_model` / `predict_future`) và **từng Quận/Huyện tại TP. Hồ Chí Minh** (`train_district_model` / `predict_future_districts`).
  - Tích hợp toàn diện các biến độ trễ sinh học khí hậu: Lượng mưa trễ (`rain_lag_1`, `rain_lag_2`), nhiệt độ trễ (`temp_lag_1`, `temp_lag_2`), độ ẩm trễ (`humidity_lag_1`, `humidity_lag_2`), tương tác Nhiệt-Ẩm ($T \times H$) và nồng độ bụi mịn vi khí hậu đô thị (PM2.5).
  - Mã hóa tính tuần hoàn thời gian bằng hàm lượng giác ($\sin/\cos$).
- **Phản Ánh Cộng Đồng & Điều Phối Quản Lý Dịch Khép Kín (Participatory GIS & HCDC Workflow)**:
  - **Đối tượng Người dân:** Xem bản đồ cảnh báo đa cấp, ghim tọa độ GPS thực địa ổ bọ gậy/nước tù đọng/ca nghi ngờ (`map_pins_service`), theo dõi tiến độ xử lý từng điểm phản ánh và trò chuyện với Trợ lý AI / Đặt lịch khám.
  - **Đối tượng Cán bộ Y tế / HCDC:** Đăng nhập xác thực (`DoctorAuthService` SHA-256) để mở khóa **Trung Tâm Điều Phối HCDC**, thực hiện duyệt/xác minh điểm phản ánh cộng đồng (`pending` → `verified` → `spraying` → `resolved`), phân công đội phun thuốc cho từng ổ dịch (`cluster_actions`), và đồng bộ trạng thái trực tiếp lên bản đồ ArcGIS & Leaflet.
- **Trí Tuệ Nhân Tạo Đánh Giá Rủi Ro Đa Chiều (Gemini Multi-modal Risk Index & Advisory)**:
  - Thiết lập công thức tính toán **Chỉ số Rủi ro Đa chiều ($RiskIndex$)**: Kết hợp có trọng số giữa dự báo XGBoost (45%) + Bất thường khí tượng (25%) + Mật độ phản ánh cộng đồng trong bán kính 500m (30%).
  - Tích hợp mô hình ngôn ngữ lớn Google Gemini 2.5 Flash để tự động xuất báo cáo đánh giá dịch tễ chuyên sâu và lịch trình hành động can thiệp dập dịch khẩn cấp.
  - Mô phỏng kịch bản giả định biến đổi môi trường và hiệu quả can thiệp dập dịch (*Scenario Simulation*).
  - Trợ lý y tế AI trực tuyến có neo tìm kiếm thời gian thực (*Google Search Grounding*) và bộ lọc lâm sàng phát hiện dấu hiệu sốt xuất huyết nguy kịch để cảnh báo cấp cứu 115.

---

## 2. KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               NGUỒN DỮ LIỆU ĐẦU VÀO                              │
├──────────────────────────┬─────────────────────────────┬─────────────────────────┤
│ Dữ liệu Ca bệnh Lâm sàng │ Khí tượng & Quan trắc       │ Phản ánh Cộng đồng GIS  │
│ • File Excel bệnh viện   │ • WeatherAPI.com (Lịch sử)  │ • Tọa độ GPS người dân  │
│ • Lọc mã ICD-10 (A90/A97)│ • Open-Meteo Archive API    │ • Điểm bọ gậy/lăng quăng│
│ • Bóc tách địa chỉ NLP   │ • OpenAQ (Bụi mịn PM2.5)    │ • Ý kiến & Bình luận    │
└────────────┬─────────────┴──────────────┬──────────────┴────────────┬────────────┘
             │                            │                           │
             ▼                            ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      TẦNG TIỀN XỬ LÝ & BẢO TRÌ DỮ LIỆU DỊCH TỄ                   │
│  • Khử trùng lặp bệnh nhân đa nguồn   • Hierarchical NLP Address Parser          │
│  • Chuẩn hóa 63 -> 34 tỉnh/thành      • Mã hóa chu kỳ lượng giác: sin/cos        │
│  • Tính suất mắc / 100k dân           • Kỹ nghệ đặc trưng trễ khí hậu (Lags 1-2) │
│  • Tác vụ nền APScheduler             • Hybrid Persistence: MongoDB <-> Local CSV│
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
┌─────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│   MÔ HÌNH DỰ BÁO ML     │ │  AI MULTI-MODAL ADVISORY  │ │    GIS & BUFFER ENGINE    │
│  • XGBoost Regressor    │ │  • Google Gemini 2.5 Flash│ │  • GeoPandas + Shapely    │
│  • Holdout Out-of-Time  │ │  • Multi-modal Risk Index │ │  • Geodesic Buffer Zoning │
│  • Recursive 3-Month    │ │  • Scenario Simulation    │ │  • Crowdsourcing Heatmap  │
│  • Đầy đủ Lags Khí Hậu  │ │  • Search Grounding + 115 │ │  • GeoJSON ArcGIS/Plotly  │
└───────────┬─────────────┘ └─────────────┬─────────────┘ └─────────────┬─────────────┘
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          │
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         TẦNG ỨNG DỤNG & GIAO DIỆN NGƯỜI DÙNG                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1. Dashboard Giám sát: Bản đồ nhiệt Choropleth, Scatter Hotspots & Xu hướng thời gian│
│ 2. Dự báo Học máy XGBoost: Dự báo đệ quy số ca theo chu kỳ và biến số khí hậu   │
│ 3. Bản đồ Phản ánh Cộng đồng: Ghim vị trí ổ lăng quăng, bình luận thực địa GIS  │
│ 4. Đánh giá Rủi ro Đa chiều AI: Multi-modal Risk Index & Mô phỏng Breteau Index  │
│ 5. Trợ lý Y tế AI Thông minh: Hỏi đáp dịch tễ, Google Grounding, Báo ca nặng 115 │
│ 6. Điều phối Dập dịch HCDC: Bảng điều khiển quản lý điểm nóng và xe dập dịch     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. TỔNG HỢP CÁC THUẬT TOÁN ÁP DỤNG (ALGORITHMS)

### 3.1. Thuật Toán Gradient Tree Boosting (XGBoost Regressor)
- **Vị trí file code:** [`src/model.py`](file:///d:/ProJect/dengue-prediction/dengue-prediction/src/model.py)
- **Mô tả:** Sử dụng thuật toán học kết hợp (Ensemble Learning) dựa trên cây quyết định tăng cường Gradient (Gradient Boosted Decision Trees - GBDT) để dự báo số ca mắc sốt xuất huyết theo tháng cho từng tỉnh/thành phố.
- **Cơ chế hoạt động:**
  - Tối ưu hóa hàm mất mát hồi quy bình phương (`reg:squarederror`) thông qua khai triển chuỗi Taylor bậc hai.
  - Sử dụng hàm phạt điều chuẩn $\Omega(f)$ chứa cả thành phần $L_1$ (Lasso/alpha) và $L_2$ (Ridge/lambda) để kiểm soát độ phức tạp và ngăn ngừa hiện tượng quá khớp (overfitting).
  - Tích hợp tính năng hỗ trợ phân loại trực tiếp (`enable_categorical=True`) giúp biểu diễn danh mục tỉnh thành trực tiếp trên cấu trúc cây mà không làm bùng nổ số chiều như One-Hot Encoding.
  - Phân tách tập dữ liệu đánh giá theo trục thời gian (Time-based Holdout Split) thay vì chia ngẫu nhiên, giữ nguyên bản chất trật tự nhân quả của chuỗi thời gian.

### 3.2. Thuật Toán Dự Báo Chuỗi Thời Gian Đa Bước Đệ Quy (Recursive Multi-Step Time Series Forecasting)
- **Vị trí file code:** [`src/model.py`](file:///d:/ProJect/dengue-prediction/dengue-prediction/src/model.py) (`predict_future`)
- **Mô tả:** Dự báo số ca bệnh tương lai cho $n$ tháng kế tiếp ($h = 1, 2, \dots, n$).
- **Cơ chế hoạt động:**
  - Tại bước $h = 1$: Đặc trưng trễ số ca bệnh lấy từ dữ liệu quá khứ thực tế ($y_t, y_{t-1}$).
  - Tại bước $h > 1$: Đặc trưng trễ tự động cập nhật bằng các giá trị đã được dự báo ở các bước trước đó ($\hat{y}_{t+h-1}, \hat{y}_{t+h-2}$).
  - Vòng lặp cuộn tiến thời gian (Roll-forward calendar) tự động tăng tháng/năm, tính toán lại các biến chu kỳ $(\sin, \cos)$ tương ứng với thời điểm dự báo.
  - Áp dụng kỹ thuật chặn dưới không âm (Non-negative clipping): $\hat{y} = \max(0, \hat{y})$ để đảm bảo tính hợp lý trong dịch tễ học.

### 3.3. Thuật Toán Bóc Tách Địa Chỉ Đa Tầng Bằng NLP & Suy Luận Quan Hệ Không Gian (Hierarchical Address Parsing & Spatial Inference)
- **Vị trí file code:** [`src/data_processor.py`](file:///d:/ProJect/dengue-prediction/dengue-prediction/src/data_processor.py) (`parse_hierarchical_address`)
- **Mô tả:** Giải thuật bóc tách và phân rã chuỗi địa chỉ tự nhiên thành 4 cấp độ hành chính: `Street > Ward > District > Province`.
- **Cơ chế hoạt động:**
  - **Khử dấu & Chuẩn hóa thực thể:** Sử dụng thuật toán phân tách chuẩn Unicode NFD (`unicodedata.normalize`) loại bỏ dấu thanh tiếng Việt và ánh xạ 63 tỉnh/thành cũ sang 34 tỉnh/thành theo đề án cải cách địa giới hành chính (`MERGE_MAP`).
  - **Phân rã bằng Regular Expression đa tầng:** Lần lượt quét và trích xuất Tuyến phố (`r'(\d+[\w\/\-]*\s+[^,;]+|\b(?:đường|phố|hẻm|ngõ|ấp|tổ|khu\s+phố)\s+[^,;]+)'`), Phường/Xã (`r'(phường\s+[\w\s\d]+|xã\s+[\w\s\d]+|thị trấn\s+[\w\s\d]+|p\.\s*[\w\s\d]+|x\.\s*[\w\s\d]+)'`), Quận/Huyện và Tỉnh/Thành phố.
  - **Suy luận liên cấp không gian (Hierarchical Spatial Inference):** Khi chuỗi địa chỉ chỉ ghi nhận Phường mà thiếu Quận, hệ thống tự động tra cứu từ điển ánh xạ `HCMC_WARD_TO_DISTRICT` để suy ra Quận/Huyện cha tương ứng.
  - **Gán tọa độ đại diện đa cấp:** Gán tọa độ theo thứ tự ưu tiên độ mịn giảm dần: Tuyến đường $\rightarrow$ Phường $\rightarrow$ Quận $\rightarrow$ Tỉnh $\rightarrow$ Tọa độ mặc định.

### 3.4. Thuật Toán Tạo Vùng Đệm Khoanh Vùng Ổ Dịch Geodesic Buffer (Geodesic Buffer Zoning)
- **Vị trí file code:** [`src/gis_mapper.py`](file:///d:/ProJect/dengue-prediction/dengue-prediction/src/gis_mapper.py) (`create_cluster_geojson`)
- **Mô tả:** Chuyển đổi bán kính dập dịch thực tế từ đơn vị mét sang đa giác hình học trên mặt cầu Trái Đất (WGS84).
- **Cơ chế hoạt động:**
  - Quy đổi bán kính $R$ (mét) sang độ vĩ tuyến ($\Delta\phi = R / 111320.0$).
  - Quy đổi bán kính sang độ kinh tuyến có hiệu chỉnh theo vĩ độ: $\Delta\lambda = R / (111320.0 \cdot \max(0.1, \cos(\phi)))$.
  - Tạo vùng đệm đa giác tròn qua phương thức `Point.buffer(buffer_deg)` của thư viện Shapely và đóng gói ra GeoDataFrame chuẩn `EPSG:4326`.

### 3.5. Thuật Toán Khử Trùng Lặp Ca Bệnh Đa Trường Khóa (Multi-Key Deduplication)
- **Vị trí file code:** [`src/data_processor.py`](file:///d:/ProJect/dengue-prediction/dengue-prediction/src/data_processor.py)
- **Mô tả:** Loại bỏ các bản ghi trùng lặp khi một bệnh nhân tái khám hoặc xuất hiện nhiều lần trong các bảng tính Excel của các bệnh viện khác nhau.
- **Cơ chế hoạt động:** Gộp 4 trường thông tin nhận diện cốt lõi: `['Họ tên', 'Năm sinh', 'Giới tính', 'Địa chỉ']`, chuẩn hóa chuỗi và loại bỏ bản ghi trùng nhằm bảo đảm tính chính xác của số liệu dịch tễ.

### 3.6. Thuật Toán Lọc Mã Bệnh Theo Phân Loại Quốc Tế (ICD-10 Filtering)
- **Vị trí file code:** [`src/data_processor.py`](file:///d:/ProJect/dengue-prediction/dengue-prediction/src/data_processor.py)
- **Mô tả:** Sử dụng biểu thức chính quy `A90|A97` lọc chính xác các hồ sơ mắc Sốt xuất huyết Dengue cổ điển (ICD-10: A90) và Sốt xuất huyết Dengue nặng / có dấu hiệu cảnh báo (ICD-10/11: A97).

### 3.7. Thuật Toán Mô Phỏng Kịch Bản Dịch Tễ Đa Yếu Tố (Multi-Factor Epidemiological Simulation)
- **Vị trí file code:** [`src/ai_prediction_service.py`](file:///d:/ProJect/dengue-prediction/dengue-prediction/src/ai_prediction_service.py)
- **Mô tả:** Đánh giá sự kết hợp giữa các tham số môi trường và vector truyền bệnh (lượng mưa, độ ẩm, nhiệt độ, chỉ số bọ gậy Breteau Index) cùng với nỗ lực can thiệp y tế để tính toán tỷ lệ gia tăng hoặc suy giảm số ca bệnh. Hỗ trợ 2 chế độ:
  - *Chế độ Trực tuyến (Online):* Sử dụng Google Gemini AI kèm Prompt dịch tễ học chuyên sâu và cấu hình JSON có cấu trúc.
  - *Chế độ Ngoại tuyến (Offline Fallback):* Áp dụng thuật toán hàm trọng số hồi quy phi tuyến tính.

### 3.8. Thuật Toán Tính Toán Chỉ Số Rủi Ro Đa Chiều (Multi-modal Risk Index Algorithm)
- **Mô tả:** Hợp nhất 3 nguồn dữ liệu then chốt: kết quả dự báo tương lai của mô hình XGBoost, độ lệch bất thường khí hậu trạm quan trắc và mật độ phản ánh thực địa của cộng đồng trong bán kính 500m.
- **Cơ chế hoạt động:**
  $$RiskIndex = \left[ 0.45 \cdot \left(\frac{\widehat{Y}_{XGBoost}}{Y_{max}}\right) + 0.25 \cdot ClimaRisk + 0.30 \cdot CommDensity_{500m} \right] \times 100$$
  Kết quả được chuyển giao cho Google Gemini 2.5 Flash để tự động xuất khuyến nghị can thiệp dịch tễ và phân bổ đội hình phun thuốc dập dịch.

### 3.9. Thuật Toán Phân Tích Mật Độ Phản Ánh Không Gian (Spatial Crowdsourced Density & Point Clustering)
- **Mô tả:** Tính toán mật độ các phản ánh ổ bọ gậy, điểm nước đọng và ca sốt nghi ngờ do người dân ghim trong bán kính $R = 500\text{m} - 1000\text{m}$.
- **Cơ chế hoạt động:** Sử dụng giải thuật khoảng cách cầu Geodesic Haversine để đếm số lượng phản ánh xung quanh tâm tọa độ truy vấn, áp dụng kỹ thuật ước lượng mật độ nhân (Kernel Density Estimation - KDE) để biểu diễn bản đồ nhiệt các điểm nóng cần can thiệp dập dịch khẩn cấp.

---

## 4. TỔNG HỢP CÁC PHƯƠNG TRÌNH TOÁN HỌC & THỐNG KÊ (MATHEMATICAL & STATISTICAL EQUATIONS)

### 4.1. Mã Hóa Chu Kỳ Thời Gian Bằng Lượng Giác (Cyclical Trigonometric Feature Encoding)
Để biểu diễn các chu kỳ thời gian (tháng, giờ, thứ) mà vẫn bảo toàn tính liên tục khép kín (ví dụ: khoảng cách giữa tháng 12 và tháng 1 là 1 đơn vị, giữa 23h và 0h là 1 giờ):

$$\text{month\_sin} = \sin\left(\frac{2\pi \cdot m}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \cdot m}{12}\right) \quad (m \in [1, 12])$$

$$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot h}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot h}{24}\right) \quad (h \in [0, 23])$$

$$\text{dow\_sin} = \sin\left(\frac{2\pi \cdot d}{7}\right), \quad \text{dow\_cos} = \cos\left(\frac{2\pi \cdot d}{7}\right) \quad (d \in [0, 6])$$

### 4.2. Tỷ Suất Mắc Bệnh Chuẩn Hóa Trên Quy Mô Dân Số (Incidence Rate per 100,000 Population)
Chỉ số dịch tễ học chuẩn quốc tế đo lường cường độ lây nhiễm không phụ thuộc vào quy mô dân số tuyệt đối của địa phương:

$$\text{Incidence Rate} = \left(\frac{\text{Cases}}{\text{Population}}\right) \times 100{,}000$$

### 4.3. Hàm Mục Tiêu Tối Ưu Hóa Của XGBoost Hồi Quy (XGBoost Objective Function)
Hàm mục tiêu tại vòng lặp thứ $t$ kết hợp giữa độ đo tổn thất bình phương và hàm điều chuẩn độ phức tạp của tập cây:

$$\mathcal{L}^{(t)} = \sum_{i=1}^n \left( y_i - \left(\hat{y}_i^{(t-1)} + f_t(x_i)\right) \right)^2 + \Omega(f_t)$$

Trong đó hàm điều chuẩn độ phức tạp cây $\Omega(f)$:

$$\Omega(f_t) = \gamma T + \frac{1}{2}\lambda \sum_{j=1}^T w_j^2 + \alpha \sum_{j=1}^T |w_j|$$

*(với $T$ là số lượng lá cây, $w_j$ là trọng số lá thứ $j$, $\gamma$ là hệ số phạt tạo nhánh mới, $\lambda$ là hệ số điều chuẩn $L_2$, $\alpha$ là hệ số điều chuẩn $L_1$).*

Khai triển Taylor bậc hai của hàm mục tiêu quanh giá trị dự báo trước đó $\hat{y}_i^{(t-1)}$:

$$\tilde{\mathcal{L}}^{(t)} \approx \sum_{i=1}^n \left[ g_i f_t(x_i) + \frac{1}{2} h_i f_t^2(x_i) \right] + \Omega(f_t)$$

với Gradient bậc 1 $g_i$ và Hessian bậc 2 $h_i$:
$$g_i = 2\left(\hat{y}_i^{(t-1)} - y_i\right), \quad h_i = 2$$

Trọng số tối ưu $w_j^*$ tại mỗi lá $j$:
$$w_j^* = -\frac{\sum_{i \in I_j} g_i}{\sum_{i \in I_j} h_i + \lambda} = -\frac{\sum_{i \in I_j} 2\left(\hat{y}_i^{(t-1)} - y_i\right)}{2 |I_j| + \lambda}$$

### 4.4. Các Chỉ Số Đánh Giá Mô Hình Hồi Quy (Regression Metrics)
- **Sai số toàn phương trung bình căn bậc hai (Root Mean Squared Error - RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n \left(y_i - \hat{y}_i\right)^2}$$

- **Sai số tuyệt đối trung bình (Mean Absolute Error - MAE):**
  $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n \left|y_i - \hat{y}_i\right|$$

### 4.5. Chuyển Đổi Bán Kính Đệm Không Gian Geodesic (Geodesic Buffer Conversion)
Khi tạo vùng đệm bán kính thực tế $R$ (mét) trên hệ tọa độ địa lý WGS84 (kinh/vĩ độ):

- Biến thiên vĩ độ ($\Delta\phi$):
  $$\Delta\phi = \frac{R}{111{,}320} \quad (\text{độ})$$

- Biến thiên kinh độ có hiệu chỉnh độ cong bề mặt Trái Đất theo vĩ độ ($\Delta\lambda$):
  $$\Delta\lambda = \frac{R}{111{,}320 \cdot \max(0.1, \, \cos(\phi_{\text{rad}}))} \quad (\text{độ})$$

- Bán kính vùng đệm phẳng đại diện ($\overline{\Delta\text{deg}}$):
  $$\overline{\Delta\text{deg}} = \frac{\Delta\phi + \Delta\lambda}{2}$$

- Vùng đệm ổ dịch $\mathcal{B}(P, R)$ bao quanh điểm tâm dịch $P(\phi_0, \lambda_0)$:
  $$\mathcal{B}(P, R) = \left\{ Q(\phi, \lambda) \in \mathbb{R}^2 \;\middle|\; \sqrt{(\phi - \phi_0)^2 + (\lambda - \lambda_0)^2} \le \overline{\Delta\text{deg}} \right\}$$

### 4.6. Chỉ Số Véc-tơ Truyền Bệnh Breteau Index (BI)
Chỉ số Breteau Index biểu thị mật độ dụng cụ chứa nước có bọ gậy/lăng quăng muỗi *Aedes* trên 100 gia đình điều tra:

$$\text{BI} = \frac{\text{Số dụng cụ chứa nước dương tính có bọ gậy}}{\text{Số nhà điều tra}} \times 100$$

- $\text{BI} < 20$: Mức an toàn / kiểm soát tốt.
- $20 \le \text{BI} < 50$: Nguy cơ cao, mật độ muỗi tăng mạnh.
- $\text{BI} \ge 50$: Cấp bùng phát dịch, cần can thiệp dập dịch diện rộng khẩn cấp.

### 4.7. Chỉ Số Rủi Ro Đa Chiều (Multi-modal Risk Index)
$$RiskIndex = \left[ w_1 \cdot \left(\frac{\widehat{Y}_{XGBoost}}{Y_{max}}\right) + w_2 \cdot ClimaRisk + w_3 \cdot CommDensity_{500m} \right] \times 100$$
với trọng số: $w_1 = 0.45$, $w_2 = 0.25$, $w_3 = 0.30$.

---

## 5. TỔNG HỢP CÁC CÔNG NGHỆ ĐÃ ÁP DỤNG (TECHNOLOGIES & LIBRARIES)

| Nhóm Công Nghệ | Tên Công Nghệ / Thư Viện | Phiên Bản | Mục Đích Sử Dụng Trong Dự Án |
| :--- | :--- | :--- | :--- |
| **Ngôn ngữ nền tảng** | **Python** | 3.10 - 3.13 | Toàn bộ backend xử lý dữ liệu, huấn luyện mô hình, kết nối API và giao diện web. |
| **Học máy (Machine Learning)** | **XGBoost** | $\ge 2.0.0$ | Thuật toán Gradient Boosted Trees hồi quy số ca bệnh theo tháng kèm hỗ trợ phân loại trực tiếp `enable_categorical=True`. |
| | **Scikit-learn** | $\ge 1.3.0$ | Các thước đo đánh giá sai số mô hình (RMSE, MAE), tiền xử lý và chia tách tập dữ liệu. |
| | **Joblib** | $\ge 1.3.0$ | Đóng gói và lưu trữ mô hình đã huấn luyện kèm bộ danh mục tỉnh và metrics (`joblib.dump`). |
| **Xử lý Dữ liệu & Tính toán** | **Pandas** | $== 2.2.3$ | Thao tác bảng dữ liệu chuỗi thời gian, lọc dữ liệu, phân nhóm theo tháng (`pd.Grouper(freq='ME')`), join dữ liệu thời tiết. |
| | **NumPy** | $\ge 1.24$ | Các phép toán mảng vector hóa, tính toán hàm lượng giác $(\sin, \cos)$ và xử lý logic số học. |
| | **Openpyxl** | $== 3.1.5$ | Đọc và bóc tách dữ liệu các bảng tính Excel lâm sàng bệnh án nhiều sheet từ các bệnh viện. |
| **Địa lý & Không gian (GIS)** | **GeoPandas** | $\ge 0.14.0$ | Quản lý GeoDataFrame ranh giới 34 tỉnh/thành phố và các lớp đa giác không gian. |
| | **Shapely** | $\ge 2.0.0$ | Xử lý đối tượng hình học (`Point`, `Polygon`), tạo đa giác vùng đệm tròn (`buffer`), sửa lỗi hình học (`make_valid`). |
| | **Fiona** | $\ge 1.9.0$ | Trình điều khiển đọc/ghi tệp định dạng không gian GeoJSON chuẩn EPSG:4326. |
| | **ArcGIS Maps SDK for JavaScript** | 4.29 | Hiển thị bản đồ WebGIS đa lớp (2D `MapView` & 3D `SceneView`), `LayerList`, `Legend`, `Search`, `Circle` geodesic buffer và đa giác Choropleth cấp Tỉnh & Quận TP.HCM. |
| | **Leaflet** | 1.9.4 | Bản đồ tương tác nhẹ song song với ArcGIS phục vụ người dân ghim tọa độ GPS phản ánh thực địa. |
| **Trí tuệ Nhân tạo (GenAI)** | **Google GenAI SDK** | $\ge 0.3.0$ | Bộ SDK chính thức kết nối Google Gemini API (hỗ trợ `gemini-2.5-flash`, `gemini-3.5-flash-lite`). |
| | **Google Search Grounding** | — | Kỹ thuật neo tìm kiếm Google thực tế giúp Chatbot cập nhật báo cáo dịch tễ mới nhất thời gian thực. |
| | **Structured Output (JSON)** | — | Ép kiểu đầu ra của mô hình ngôn ngữ lớn về đúng schema JSON chuẩn phục vụ hiển thị trực quan. |
| **Cơ sở dữ liệu & Lưu trữ** | **MongoDB Atlas / PyMongo** | $\ge 4.6.0$ | Cơ sở dữ liệu NoSQL lưu trữ phản ánh cộng đồng, lịch sử ca bệnh, dữ liệu thời tiết và cache dự báo AI. |
| | **Dnspython** | $\ge 2.6.0$ | Hỗ trợ phân giải tên miền kết nối MongoDB SRV Connection String (`mongodb+srv://`). |
| | **Certifi** | $\ge 2024$ | Cung cấp Mozilla CA Bundle phục vụ xác thực bảo mật SSL/TLS tin cậy khi kết nối MongoDB. |
| **Giao diện & Trực quan hóa** | **Streamlit** | $\ge 1.30.0$ | Framework giao diện ứng dụng web chính (Dashboard đa tab, tương tác bản đồ, ghim GPS, AI chat). |
| | **Plotly** | $\ge 5.18.0$ | Vẽ bản đồ Choropleth, Scatter Bubble Map nhiệt, biểu đồ đường kép hai trục tung, biểu đồ nhiệt trực quan. |
| | **HTML5 / CSS3** | — | Thiết kế các khối thẻ thông tin y tế, hiệu ứng glassmorphism, responsive sidebar, huy hiệu trạng thái. |
| **Điều phối & Tác vụ nền** | **APScheduler** | $\ge 3.10.0$ | Bộ lập lịch chạy ngầm (BackgroundScheduler) tự động đồng bộ thời tiết hàng tuần (HCMC) và hàng tháng (34 tỉnh). |
| **Bảo mật & Chuẩn hóa** | **Pydantic** | $\ge 2.0$ | Kiểm định cấu trúc dữ liệu nghiêm ngặt cho phiếu phản ánh cộng đồng, tọa độ và mô phỏng. |
| | **Python-Dotenv** | $\ge 1.0.0$ | Quản lý biến môi trường bảo mật tập trung qua tệp `.env`. |

---

## 6. DANH SÁCH CÁC BÀI BÁO KHOA HỌC & TÀI LIỆU THAM KHẢO (SCIENTIFIC PUBLICATIONS & REFERENCES)

### 6.1. Nghiên Cứu Về Dịch Tễ Học Sốt Xuất Huyết & Tác Động Của Khí Hậu (Climate & Dengue Epidemiology)
1. **Bhatt, S., Gething, P. W., Brady, O. J., Messina, J. P., Farlow, A. W., Moyes, C. L., ... & Hay, S. I. (2013).**
   *The global distribution and burden of dengue.* **Nature**, 496(7446), 504-507.
   - [DOI: 10.1038/nature12060](https://doi.org/10.1038/nature12060)
2. **Colon-Gonzalez, F. J., Fezzi, C., Lake, I. R., & Hunter, P. R. (2013).**
   *The effects of weather and climate change on dengue.* **PLoS Neglected Tropical Diseases**, 7(11), e2503.
   - [DOI: 10.1371/journal.pntd.0002503](https://doi.org/10.1371/journal.pntd.0002503)
3. **World Health Organization (WHO) (2009 / 2024 update).**
   *Dengue: guidelines for diagnosis, treatment, prevention and control.* **World Health Organization**, Geneva.
   - [WHO Dengue Guidelines Link](https://www.who.int/publications/i/item/9789241547871)
4. **Bộ Y Tế Việt Nam (2023).**
   *Hướng dẫn chẩn đoán, điều trị Sốt xuất huyết Dengue (Ban hành kèm theo Quyết định số 2760/QĐ-BYT ngày 04/07/2023).* **Cổng Thông Tin Bộ Y Tế**.
   - [Văn Bản Quyết Định Bộ Y Tế](https://kcb.vn/van-ban/quyet-dinh-so-2760-qd-byt-ngay-04-7-2023-cua-bo-truong-bo-y-te-huong-dan-chan-doan-dieu-tri-sot-xuat-huyet-dengue.html)

### 6.2. Nghiên Cứu Về Thuật Toán Học Máy & Chuỗi Thời Gian Trong Y Tế (Machine Learning & Time Series Forecasting)
5. **Chen, T., & Guestrin, C. (2016).**
   *XGBoost: A scalable tree boosting system.* In **Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining** (pp. 785-794).
   - [DOI: 10.1145/2939672.2939785](https://doi.org/10.1145/2939672.2939785)
6. **Friedman, J. H. (2001).**
   *Greedy function approximation: a gradient boosting machine.* **Annals of Statistics**, 29(5), 1189-1232.
   - [JSTOR Link](https://www.jstor.org/stable/2699986)
7. **Hyndman, R. J., & Athanasopoulos, G. (2021).**
   *Forecasting: principles and practice (3rd ed).* **OTexts: Melbourne, Australia**.
   - [OTexts Online Book](https://otexts.com/fpp3/)
8. **Scavuzzo, J. M., Trucco, F., Espinosa, M., Tauro, C. B., Abril, M., Scavuzzo, C. M., & Frery, A. C. (2018).**
   *Modeling Dengue vector abundance using statistical and machine learning techniques in Argentina.* **Acta Tropica**, 185, 320-337.
   - [DOI: 10.1016/j.actatropica.2018.06.011](https://doi.org/10.1016/j.actatropica.2018.06.011)

### 6.3. Trí Tuệ Nhân Tạo Tạo Sinh & Neo Tri Thức Thực Tế Trong Y Khoa (LLMs & Search Grounding)
9. **Gemini Team, Google (2024).**
   *Gemini: A family of highly capable multimodal models.* **Google DeepMind Technical Report**.
   - [arXiv:2312.11805](https://arxiv.org/abs/2312.11805)
10. **Singhal, K., Azizi, S., Tu, T., Mahdavi, S. S., Wei, J., Chung, H. W., ... & Natarajan, V. (2023).**
    *Large language models encode clinical knowledge.* **Nature**, 620(7972), 172-180.
    - [DOI: 10.1038/s41586-023-06291-2](https://doi.org/10.1038/s41586-023-06291-2)

---

## 7. TÀI LIỆU HƯỚNG DẪN & LINK TÀI NGUYÊN TRỰC TUYẾN (OFFICIAL DOCUMENTATION & TUTORIALS)

### 7.1. Thư Viện Học Máy & Khoa Học Dữ Liệu
- **XGBoost Python Documentation:** [https://xgboost.readthedocs.io/en/stable/python/python_intro.html](https://xgboost.readthedocs.io/en/stable/python/python_intro.html)
- **Scikit-learn Evaluation Metrics:** [https://scikit-learn.org/stable/modules/model_evaluation.html#regression-metrics](https://scikit-learn.org/stable/modules/model_evaluation.html#regression-metrics)
- **Pandas Time Series:** [https://pandas.pydata.org/docs/reference/api/pandas.Grouper.html](https://pandas.pydata.org/docs/reference/api/pandas.Grouper.html)

### 7.2. Địa Không Gian & Bản Đồ (GIS)
- **GeoPandas User Guide:** [https://geopandas.org/en/stable/docs/user_guide.html](https://geopandas.org/en/stable/docs/user_guide.html)
- **Shapely Geometry Documentation:** [https://shapely.readthedocs.io/en/stable/manual.html#object.buffer](https://shapely.readthedocs.io/en/stable/manual.html#object.buffer)
- **Plotly Express Maps:** [https://plotly.com/python/mapbox-county-choropleth/](https://plotly.com/python/mapbox-county-choropleth/)

### 7.3. Google GenAI & Gemini SDK
- **Google GenAI Python SDK (`google-genai`):** [https://googleapis.github.io/python-genai/](https://googleapis.github.io/python-genai/)
- **Gemini Search Grounding:** [https://ai.google.dev/gemini-api/docs/grounding](https://ai.google.dev/gemini-api/docs/grounding)
- **Structured Outputs (JSON Schema):** [https://ai.google.dev/gemini-api/docs/structured-output](https://ai.google.dev/gemini-api/docs/structured-output)

### 7.4. Cơ Sở Dữ Liệu & API Thời Tiết
- **MongoDB Atlas & PyMongo:** [https://pymongo.readthedocs.io/en/stable/tutorial.html](https://pymongo.readthedocs.io/en/stable/tutorial.html)
- **WeatherAPI History Endpoint:** [https://www.weatherapi.com/docs/](https://www.weatherapi.com/docs/)
- **Open-Meteo Historical Weather API:** [https://open-meteo.com/en/docs/historical-weather-api](https://open-meteo.com/en/docs/historical-weather-api)

---

## 8. HƯỚNG DẪN TRIỂN KHAI & KHỞI CHẠY (DEPLOYMENT & EXECUTION)

### 8.1. Cài Đặt Môi Trường
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 8.2. Cấu Hình Biến Môi Trường (`.env`)
```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=dengue_prediction_db
WEATHERAPI_KEY=your_weatherapi_key_here
```

### 8.3. Khởi Chạy Pipeline Dữ Liệu & Huấn Luyện Mô Hình
```powershell
python main.py
```

### 8.4. Khởi Chạy Ứng Dụng Web Dashboard Chính
```powershell
streamlit run src/dashboard.py
```
*Truy cập ứng dụng tại: `http://localhost:8501`*

### 8.5. Chạy Kiểm Thử Tự Động (Unit & Integration Tests)
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

---

## 9. TỔNG HỢP CÁC SƠ ĐỒ THIẾT KẾ HỆ THỐNG PHÂN MẢNH (MODULAR SYSTEM DESIGN DIAGRAMS)

### 9.1. Nhóm Sơ Đồ Kiến Trúc Hệ Thống (System Architecture Diagrams)

#### Hình 9.1.1: Sơ đồ Kiến trúc Phân tầng Tổng thể Hệ thống (High-Level Layered Architecture)
```mermaid
flowchart TB
    subgraph L1 ["1. TẦNG NGUỒN DỮ LIỆU ĐẦU VÀO (DATA SOURCE LAYER)"]
        D1["Dữ liệu Ca bệnh Lâm sàng Bệnh viện<br/>(Excel: data2024.xlsx, data2025.xlsx)"]
        D2["Dữ liệu Ranh giới Địa chính 34 Tỉnh/TP<br/>(GeoJSON: vietnam_34_provinces_2025)"]
        D3["Dữ liệu Dân số ADM1 OCHA/UNFPA<br/>(CSV: vnm_admpop_adm1_2024.csv)"]
        D4["API Trạm Khí tượng WeatherAPI.com<br/>(Mưa, Nhiệt độ, Độ ẩm lịch sử)"]
        D5["API Khí hậu & Tái phân tích Open-Meteo<br/>(Chuỗi thời gian khí tượng & PM2.5)"]
        D6["Phản ánh Thực địa Cộng đồng (Crowdsourcing)<br/>(Tọa độ GPS, Điểm bọ gậy, Nước tù đọng)"]
    end

    subgraph L2 ["2. TẦNG LƯU TRỮ VÀ BỘ NHỚ ĐỆM KÉP (HYBRID PERSISTENCE LAYER)"]
        subgraph L2_Cloud ["MongoDB Atlas Cloud Cluster (Nguồn Dữ Liệu Chính)"]
            MC1[("citizen_reports & spatial_feedbacks")]
            MC2[("intervention_plans & risk_evaluations")]
            MC3[("historical_cases & hotspots")]
            MC4[("weather_cache & ai_cache")]
        end
        subgraph L2_Local ["Local Server Cache (Cơ Chế Chịu Lỗi Ngoại Tuyến)"]
            LC1["data/processed/*.csv"]
            LC2["ai_evaluation_cache.json"]
            LC3["outputs/models/dengue_model.pkl"]
            LC4["outputs/maps/*.geojson"]
        end
    end

    subgraph L3 ["3. TẦNG ĐỘNG CƠ XỬ LÝ & MÔ HÌNH HÓA (CORE ENGINE LAYER)"]
        E1["Động cơ Bóc tách Địa chỉ Tự nhiên NLP<br/>(Hierarchical Address Parser)"]
        E2["Động cơ Trích xuất Đặc trưng Khí tượng Trễ<br/>(Feature Engineering: Lags, T*H, PM2.5)"]
        E3["Động cơ Học máy Dự báo Chuỗi thời gian<br/>(Climate-Enhanced XGBoost Engine)"]
        E4["Động cơ Không gian Địa lý & Vùng đệm Ổ dịch<br/>(GIS Geodesic Buffer Engine)"]
        E5["Động cơ Đánh giá Rủi ro Đa chiều AI<br/>(Multi-modal Risk Index & Gemini 2.5 Flash)"]
        E6["Động cơ Trợ lý Y tế & Tìm kiếm Trực tuyến<br/>(Gemini Live Search Grounding)"]
        E7["Động cơ Phân tích Mật độ Điểm nóng Không gian<br/>(Spatial Point Clustering & KDE)"]
    end

    subgraph L4 ["4. TẦNG ỨNG DỤNG & GIAO DIỆN NGƯỜI DÙNG (APPLICATION LAYER)"]
        A1["Dashboard Giám sát Dịch tễ Bản đồ Nhiệt (Tab 1)"]
        A2["Dự báo Học máy Đa biến Môi trường XGBoost (Tab 2)"]
        A3["Bản đồ Phản ánh Dịch tễ Cộng đồng GIS (Tab 3)"]
        A4["Đánh giá Rủi ro Đa chiều & Mô phỏng Kịch bản AI (Tab 4)"]
        A5["Trợ lý Y tế AI Hỏi đáp Thông minh & Báo ca nặng (Tab 5)"]
        A6["Bảng Điều phối Dập dịch Cán bộ Y tế Dự phòng (Tab 6)"]
    end

    D1 & D2 & D3 & D4 & D5 & D6 --> L3
    L3 <--> L2
    L3 --> L4
```

---

#### Hình 9.1.2: Kiến trúc Phân hệ Pipeline Dữ liệu & Học máy (Data & ML Pipeline Subsystem Architecture)
```mermaid
flowchart LR
    subgraph InputStage ["Tiếp Nhận Dữ Liệu"]
        F1["Raw Excel Files<br/>(data2024, data2025)"]
        F2["Population Data<br/>(ADM1 UNFPA)"]
        F3["Weather Data<br/>(WeatherAPI/Open-Meteo)"]
    end

    subgraph ProcessingStage ["Xử Lý Dịch Tễ & Đặc Trưng"]
        P1["Lọc Mã ICD-10<br/>(A90/A97)"]
        P2["Khử Trùng Lặp<br/>4 Trường Khóa"]
        P3["Hierarchical Parser<br/>Phố > Phường > Quận > Tỉnh"]
        P4["Tính Incidence Rate<br/>/ 100k Dân"]
        P5["Mã Hóa Chu Kỳ<br/>sin/cos(month)"]
        P6["Tạo Feature Trễ<br/>Lags Khí hậu 1-2 & T*H"]
    end

    subgraph ModelStage ["Học Máy & Địa Không Gian"]
        M1["XGBoost Booster<br/>Time-based Holdout"]
        M2["Dự Báo Đệ Quy<br/>Roll-forward 3 Tháng"]
        M3["GIS Spatial Mapper<br/>Buffer 100m - 2000m"]
    end

    subgraph OutputStage ["Lưu Trữ & Hiển Thị"]
        O1[("MongoDB Collections")]
        O2["CSV/JSON Processed"]
        O3["GeoJSON Layers"]
        O4["Streamlit Interactive UI"]
    end

    F1 --> P1 --> P2 --> P3 --> P4
    F2 --> P4
    P4 --> P5 --> P6
    F3 --> P6
    P6 --> M1 --> M2
    P3 --> M3
    M2 --> O1 & O2 & O4
    M3 --> O3 & O4
```

---

#### Hình 9.1.3: Kiến trúc Phân hệ Trí tuệ Nhân tạo & Đánh giá Rủi ro (AI Intelligence Architecture)
```mermaid
flowchart TB
    subgraph Context_Builder ["Bộ Tổng Hợp Ngữ Cảnh Đa Chiều"]
        CB1["Dữ liệu Ca bệnh Lịch sử (2024-2025)"]
        CB2["Quan trắc Khí tượng Trạm Địa phương"]
        CB3["Dự báo Nền từ Mô hình XGBoost"]
        CB4["Mật độ Phản ánh Bọ gậy Cộng đồng (500m)"]
    end

    subgraph MultiModal_Engine ["Động Cơ Đánh Giá Rủi Ro Đa Chiều"]
        calc["Tính RiskIndex = 0.45*ML + 0.25*Weather + 0.30*Crowdsource"]
    end

    subgraph AI_Core ["Lõi Suy Luận Trí Tuệ Nhân Tạo (Google GenAI)"]
        G1["Google Gemini 2.5 Flash<br/>(Structured Output: application/json)"]
        G2["Google Gemini 3.5 Flash-Lite<br/>(Streaming Chatbot + Search Grounding)"]
        G3["Offline Fallback Formula Engine<br/>(Hàm trọng số toán học ngoại tuyến)"]
    end

    subgraph UI_Deliverable ["Hiển Thị Báo Cáo & Can Thiệp"]
        R1["Thẻ Đánh Giá Dịch Tễ & Phân Tầng Rủi Ro"]
        R2["Báo Cáo Đề Xuất 3 Hành Động Can Thiệp Dập Dịch"]
        R3["Chatbot Tư Vấn & Cảnh Báo Nguy Kịch 115"]
    end

    CB1 & CB2 & CB3 & CB4 --> calc --> G1
    G1 -.->|Khi mất mạng| G3
    G1 --> R1 & R2
    G2 --> R3
    G3 --> R1
```

---

#### Hình 9.1.4: Kiến trúc Phân hệ Phản Ánh Dịch Tễ Không Gian Cộng Đồng & Bản Đồ Số GIS (Spatial Crowdsourcing & GIS Surveillance Architecture)
```mermaid
flowchart TB
    subgraph MobileWeb_User ["Người Dân / Cộng Đồng Thực Địa"]
        PV1["Ghim vị trí tọa độ GPS trên bản đồ số"]
        PV2["Chọn loại phản ánh: Ổ bọ gậy / Nước đọng / Ca sốt"]
        PV3["Gửi hình ảnh, bình luận và mô tả hiện trường"]
        PV4["Theo dõi tiến độ xác minh và xử lý dập dịch"]
    end

    subgraph Crowdsourcing_Core ["Lõi Dịch Vụ Phản Ánh Không Gian (CitizenReportService)"]
        CS1["Chuẩn hóa tọa độ WGS84 (EPSG:4326)"]
        CS2["Tính khoảng cách Geodesic & Mật độ lân cận 500m"]
        CS3["Cấp mã định danh duy nhất: RP-YYYYMMDD-XXXX"]
        CS4["Bộ lọc ngôn ngữ & Kiểm tra dữ liệu hợp lệ (Pydantic)"]
    end

    subgraph Storage_Cloud ["Lưu Trữ Đám Mây MongoDB Atlas"]
        M1[("collection: citizen_reports<br/>(Lưu phản ánh, tọa độ, hình ảnh, trạng thái)")]
        M2[("collection: spatial_hotspots<br/>(Điểm nóng dịch tễ được xác minh)")]
        M3[("collection: intervention_logs<br/>(Nhật ký phun hóa chất, diệt lăng quăng)")]
    end

    subgraph Health_Officer ["Cán Bộ Y Tế Dự Phòng (HCDC / Trạm Y Tế)"]
        DV1["Tiếp nhận & Xác minh thực địa: PENDING -> VERIFIED"]
        DV2["Xem bản đồ nhiệt phản ánh MarkerCluster"]
        DV3["Kích hoạt AI đánh giá rủi ro kết hợp XGBoost"]
        DV4["Lập kế hoạch xe phun hóa chất & dập dịch"]
    end

    PV1 & PV2 & PV3 --> Crowdsourcing_Core
    Crowdsourcing_Core --> M1
    M1 --> DV1 & DV2
    DV1 --> M2 --> DV3 --> DV4 --> M3
    M3 -.->|Cập nhật trạng thái RESOLVED| PV4
```

---

### 9.2. Nhóm Sơ Đồ Luồng Nghiệp Vụ (Process Flowcharts)

#### Hình 9.2.1: Sơ đồ Luồng Tiền Xử Lý Dữ Liệu Lâm Sàng Bệnh Án
```mermaid
flowchart TD
    StartRaw(["Nhận tệp Excel lâm sàng raw: data2024.xlsx, data2025.xlsx"]) --> ReadSheets["Đọc toàn bộ các Sheets trong tệp bằng Openpyxl"]
    ReadSheets --> FilterICD["Áp dụng biểu thức chính quy lọc mã bệnh:<br/>ICD-10 regex: 'A90|A97'"]
    FilterICD --> CleanCols["Chuẩn hóa tên cột: Ngày vào viện, Họ tên, Địa chỉ, Chẩn đoán"]
    CleanCols --> Dedup["Khử trùng lặp bệnh nhân đa nguồn:<br/>Gộp khóa: [Họ tên + Năm sinh + Giới tính + Địa chỉ]"]
    Dedup --> ExtractDate["Trích xuất thời gian: Năm, Tháng, Ngày<br/>Nhóm theo tháng: pd.Grouper(freq='ME')"]
    ExtractDate --> EndClean(["Xuất bảng dữ liệu lâm sàng sạch đã khử trùng lặp"])
```

---

#### Hình 9.2.2: Sơ đồ Luồng Bóc Tách Địa Chỉ Phân Cấp NLP
```mermaid
flowchart TD
    InAddr(["Nhập chuỗi địa chỉ tự nhiên bệnh nhân"]) --> Normalize["Chuẩn hóa Unicode NFD & Bóc tách dấu thanh"]
    Normalize --> MapProvince["Ánh xạ tỉnh thành qua từ điển MERGE_MAP (63 -> 34 tỉnh mới)"]
    MapProvince --> MatchStreet["Quét Regex Tuyến đường / Số nhà / Hẻm / Phố"]
    MatchStreet --> MatchWard["Quét Regex Phường / Xã / Thị trấn"]
    MatchWard --> MatchDistrict["Quét Regex Quận / Huyện"]
    MatchDistrict --> CheckInfer{"Có Phường mà<br/>thiếu Quận?"}
    CheckInfer -- "Có" --> LookupTable["Tra cứu bảng HCMC_WARD_TO_DISTRICT -> Suy ra Quận cha"]
    CheckInfer -- "Không" --> AssignCoords["Gán tọa độ đại diện theo cấp độ mịn cao nhất"]
    LookupTable --> AssignCoords
    AssignCoords --> OutGeoJSON(["Xuất bản ghi có cấu trúc: Street, Ward, District, Province, Lat, Lon"])
```

---

#### Hình 9.2.3: Sơ đồ Luồng Kỹ Nghệ Đặc Trưng Khí Hậu & Huấn Luyện XGBoost
```mermaid
flowchart TD
    StartData(["Dữ liệu số ca bệnh lịch sử theo tháng"]) --> MergeWeather["Kết hợp chuỗi khí tượng trạm quan trắc (Mưa, Nhiệt độ, Độ ẩm)"]
    MergeWeather --> CyclicalEnc["Mã hóa chu kỳ thời gian lượng giác:<br/>month_sin, month_cos"]
    CyclicalEnc --> CreateLags["Tạo đặc trưng độ trễ khí hậu:<br/>• rain_lag_1, rain_lag_2<br/>• temp_lag_1, temp_lag_2<br/>• humidity_lag_1, temp_humidity<br/>• cases_lag_1, cases_lag_2"]
    CreateLags --> TimeSplit["Phân tách tập dữ liệu theo trục thời gian (Time-based Holdout Split)"]
    TimeSplit --> TrainXGB["Huấn luyện mô hình XGBoost Regressor (objective='reg:squarederror')"]
    TrainXGB --> EvalMetrics["Đánh giá sai số trên tập kiểm định Out-of-Time: RMSE, MAE"]
    EvalMetrics --> SaveModel["Lưu mô hình dengue_model.pkl & xuất dự báo latest_predictions.csv"]
```

---

#### Hình 9.2.4: Sơ đồ Luồng Thuật Toán Dự Báo Chuỗi Thời Gian Đệ Quy
```mermaid
flowchart TD
    StartFore(["Bắt đầu dự báo đệ quy h tháng tương lai (h = 1..3)"]) --> InitStep["Khởi tạo bước h = 1: Lấy lag_1 = y_t, lag_2 = y_{t-1}"]
    InitStep --> LoopCheck{"h <= n_months?"}
    LoopCheck -- "Có" --> RollCal["Cuộn tiến thời gian: Cập nhật tháng/năm, tính lại sin/cos"]
    RollCal --> PredictStep["Đưa vector đặc trưng vào XGBoost.predict() -> Thu được y_hat"]
    PredictStep --> ClipZero["Chặn dưới không âm: y_hat = max(0, y_hat)"]
    ClipZero --> UpdateLags["Cập nhật đệ quy cho bước sau:<br/>lag_2 = lag_1<br/>lag_1 = y_hat"]
    UpdateLags --> IncStep["Tăng bước: h = h + 1"]
    IncStep --> LoopCheck
    LoopCheck -- "Không" --> ReturnForecast(["Trả về bảng dự báo chuỗi thời gian 3 tháng hoàn chỉnh"])
```

---

#### Hình 9.2.5: Sơ đồ Luồng Phân Tầng Nguy Cơ & Dựng Vùng Đệm Geodesic Buffer
```mermaid
flowchart TD
    StartCluster(["Điểm nóng dịch tễ có tọa độ [lat, lon] và số ca mắc"]) --> CheckLevel{"Xét cấp địa giới hành chính"}
    CheckLevel -- "Tuyến đường" --> ClassifyStreet["Phân tầng tuyến đường:<br/>>=5 ca: Vùng Đỏ (R=500m)<br/>3-4 ca: Vùng Cam (R=300m)<br/>2 ca: Vùng Vàng (R=200m)<br/>1 ca: Vùng Xanh (R=100m)"]
    CheckLevel -- "Phường/Xã" --> ClassifyWard["Phân tầng phường/xã:<br/>>=15 ca: Vùng Đỏ (R=1000m)<br/>8-14 ca: Vùng Cam (R=600m)<br/>3-7 ca: Vùng Vàng (R=300m)"]
    CheckLevel -- "Quận/Huyện" --> ClassifyDistrict["Phân tầng quận/huyện:<br/>>=50 ca: Vùng Đỏ (R=2000m)<br/>20-49 ca: Vùng Cam (R=1200m)"]
    ClassifyStreet & ClassifyWard & ClassifyDistrict --> CalcBuffer["Quy đổi bán kính mét sang độ kinh/vĩ đại diện:<br/>buffer_deg = (deg_lat + deg_lon) / 2"]
    CalcBuffer --> ShapelyBuffer["Dựng đa giác tròn Point(lon, lat).buffer(buffer_deg)"]
    ShapelyBuffer --> ExportGeoJSON(["Xuất GeoJSON chuẩn WGS84 hiển thị trên Leaflet/ArcGIS"])
```

---

#### Hình 9.2.6: Sơ đồ Luồng Người Dân Gửi Phản Ánh Dịch Tễ Thực Địa & Ghim Tọa Độ Không Gian GIS
```mermaid
flowchart TD
    StartCitizen(["Người dân mở Tab 'Bản Đồ Phản Ánh Cộng Đồng'"]) --> PickLocation["Bật định vị GPS thiết bị hoặc click chọn vị trí trên Bản đồ số Leaflet"]
    PickLocation --> ShowMarker["Hiển thị ghim tạm thời tại tọa độ [lat, lon] WGS84"]
    ShowMarker --> FillForm["Nhập thông tin phản ánh thực địa:<br/>1. Phân loại: Ổ bọ gậy / Điểm nước đọng / Ca sốt nghi ngờ<br/>2. Mức độ nguy cơ: Thấp / Trung bình / Cao / Khẩn cấp<br/>3. Ý kiến đóng góp & Mô tả hiện trường<br/>4. Họ tên & Số điện thoại (tùy chọn)"]
    FillForm --> ValidateForm{"Kiểm tra tính hợp lệ dữ liệu?"}
    ValidateForm -- "Không" --> AlertError["Hiển thị cảnh báo: Yêu cầu chọn vị trí và nội dung mô tả"]
    AlertError --> FillForm
    ValidateForm -- "Hợp lệ" --> SubmitReport["Bấm 'Gửi Phản Ánh Thực Địa'"]
    SubmitReport --> CalcDensity["Hệ thống tự động tính mật độ phản ánh xung quanh trong bán kính 500m"]
    CalcDensity --> SaveMongo["Lưu bản ghi vào MongoDB Atlas collection 'citizen_reports':<br/>• report_id: RP-YYYYMMDD-XXXX<br/>• status: PENDING<br/>• coordinates: [lat, lon]"]
    SaveMongo --> RenderFeedback["Hiển thị phản ánh lên bản đồ MarkerCluster và cung cấp khuyến nghị diệt bọ gậy tại chỗ"]
    RenderFeedback --> EndCitizen(["Hoàn tất quy trình phản ánh"])
```

---

#### Hình 9.2.7: Sơ đồ Luồng Cán Bộ Y Tế Dự Phòng Tiếp Nhận, Xác Minh Phản Ánh & Điều Phối Can Thiệp Ổ Dịch
```mermaid
flowchart TD
    StartOfficer(["Cán bộ y tế đăng nhập Bảng Điều Phối Dập Dịch"]) --> ViewQueue["Xem danh sách phản ánh cộng đồng theo thời gian thực (Lọc PENDING)"]
    ViewQueue --> VerifyAction{"Kiểm tra thông tin & Điều tra thực địa"}
    VerifyAction -- "Không chính xác" --> RejectReport["Cập nhật verification_status = 'REJECTED' (Ghi rõ lý do)"]
    VerifyAction -- "Xác nhận có ổ bọ gậy" --> ApproveReport["Cập nhật verification_status = 'VERIFIED'"]
    ApproveReport --> ClusterAnalysis["Gộp các phản ánh lân cận thành Điểm Nóng Dịch Tễ (SPATIAL_HOTSPOT)"]
    ClusterAnalysis --> TriggerAI["Kích hoạt AI đánh giá Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index)"]
    TriggerAI --> GenInterventionPlan["Tự động lập kế hoạch dập dịch:<br/>1. Điều phối xe phun hóa chất dập dịch<br/>2. Huy động lực lượng đoàn thể diệt bọ gậy<br/>3. Thông báo khuyến cáo người dân trong bán kính Geodesic"]
    GenInterventionPlan --> ExecutePlan["Đội cơ động thực hiện can thiệp thực địa -> Cập nhật trạng thái RESOLVED"]
    RejectReport & ExecutePlan --> EndOfficer(["Kết thúc chu trình xử lý phản ánh"])
```

---

### 9.3. Nhóm Sơ Đồ Ca Sử Dụng (Use Case Diagrams)

#### Hình 9.3.1: Sơ đồ Ca Sử Dụng - Phân Hệ Người Dân & Cộng Đồng (Citizen / Community Use Cases)
```mermaid
flowchart LR
    Actor_Citizen((Người Dân /<br/>Cộng Đồng))

    subgraph UC_CitizenModule ["Phân Hệ Người Dân & Cộng Đồng"]
        UC_C1["Xem bản đồ cảnh báo ổ dịch & vùng đệm Geodesic"]
        UC_C2["Ghim tọa độ GPS điểm nước đọng & ổ bọ gậy"]
        UC_C3["Gửi hình ảnh & bình luận phản ánh thực địa"]
        UC_C4["Báo cáo ca sốt nghi ngờ trong khu dân cư"]
        UC_C5["Theo dõi tiến độ xác minh & xử lý phản ánh"]
        UC_C6["Hỏi đáp triệu chứng & phòng bệnh với Trợ lý AI"]
        UC_C7["Nhận cảnh báo đỏ cấp cứu khi có triệu chứng nặng"]
    end

    Actor_Citizen --> UC_C1
    Actor_Citizen --> UC_C2
    Actor_Citizen --> UC_C3
    Actor_Citizen --> UC_C4
    Actor_Citizen --> UC_C5
    Actor_Citizen --> UC_C6

    UC_C2 -.->|include| UC_C3
    UC_C6 -.->|include| UC_C7
```

---

#### Hình 9.3.2: Sơ đồ Ca Sử Dụng - Phân Hệ Cán Bộ Dịch Tễ & Điều Phối Dập Dịch (Epidemiologist & Health Officer Use Cases)
```mermaid
flowchart LR
    Actor_Epi((Cán Bộ Dịch Tễ /<br/>Nhà Quản Lý Y Tế))

    subgraph UC_EpiModule ["Phân Hệ Cán Bộ Dịch Tễ & Điều Phối Dập Dịch"]
        UC_E1["Xem bản đồ nhiệt dịch tễ đa tầng theo 34 tỉnh/thành"]
        UC_E2["Xem khoanh vùng ổ dịch Geodesic Buffer (100m - 2000m)"]
        UC_E3["Chạy mô hình XGBoost dự báo ca bệnh theo biến khí hậu"]
        UC_E4["Tiếp nhận, xác minh phản ánh dịch tễ từ cộng đồng"]
        UC_E5["Kích hoạt AI tính toán Chỉ số Rủi ro Đa chiều (RiskIndex)"]
        UC_E6["Chạy mô phỏng kịch bản biến động theo Breteau Index (BI)"]
        UC_E7["Lập kế hoạch & điều phối xe phun hóa chất dập dịch"]
        UC_E8["Xuất báo cáo dịch tễ định kỳ phục vụ giao ban"]
    end

    Actor_Epi --> UC_E1
    Actor_Epi --> UC_E2
    Actor_Epi --> UC_E3
    Actor_Epi --> UC_E4
    Actor_Epi --> UC_E5
    Actor_Epi --> UC_E6
    Actor_Epi --> UC_E7
    Actor_Epi --> UC_E8

    UC_E5 -.->|include| UC_E3
    UC_E5 -.->|include| UC_E4
    UC_E7 -.->|include| UC_E5
```

---

#### Hình 9.3.3: Sơ đồ Ca Sử Dụng - Phân Hệ Tác Vụ Nền Tự Động Hóa (System Scheduler Use Cases)
```mermaid
flowchart LR
    Actor_Daemon((Tiến Trình Chạy Ngầm /<br/>APScheduler Daemon))

    subgraph UC_DaemonModule ["Phân Hệ Tự Động Hóa Hệ Thống"]
        UC_A1["Đồng bộ nhanh thời tiết TP.HCM (Thứ Hai hàng tuần lúc 02:00)"]
        UC_A2["Đồng bộ toàn diện khí tượng 34 tỉnh/thành (Ngày 1 hàng tháng lúc 03:00)"]
        UC_A3["Tự động chuyển đổi Fallback khi WeatherAPI hết hạn mức sang Open-Meteo"]
        UC_A4["Sao lưu định kỳ dữ liệu từ Local CSV lên MongoDB Atlas"]
        UC_A5["Kiểm tra trạng thái kết nối mạng & Duy trì bộ đệm an toàn"]
    end

    Actor_Daemon --> UC_A1
    Actor_Daemon --> UC_A2
    Actor_Daemon --> UC_A3
    Actor_Daemon --> UC_A4
    Actor_Daemon --> UC_A5
```

---

### 9.4. Nhóm Sơ Đồ Thực Thể - Quan Hệ (ERD Diagrams)

#### Hình 9.4.1: Sơ đồ ERD - Miền Nghiệp Vụ Phản Ánh Dịch Tễ Cộng Đồng (Community Crowdsourcing Domain)
```mermaid
erDiagram
    CITIZEN_REPORTS ||--o{ COMMUNITY_FEEDBACKS : "nhan_binh_luan"
    CITIZEN_REPORTS ||--o| SPATIAL_HOTSPOTS : "xac_minh_thanh_o_dich"
    SPATIAL_HOTSPOTS ||--o{ INTERVENTION_LOGS : "thuc_hien_can_thiep"
    SPATIAL_HOTSPOTS ||--o{ RISK_EVALUATIONS : "danh_gia_boi_ai"

    CITIZEN_REPORTS {
        string report_id PK "Mã định danh phản ánh (RP-YYYYMMDD-XXXX)"
        float latitude "Tọa độ vĩ độ (GPS WGS84)"
        float longitude "Tọa độ kinh độ (GPS WGS84)"
        string address_text "Địa chỉ người dân nhập tự do"
        string report_type "LARVAE | STAGNANT_WATER | SUSPECTED_FEVER | OTHER"
        string description "Mô tả chi tiết và ý kiến phản ánh"
        string severity "LOW | MEDIUM | HIGH | CRITICAL"
        string image_url "Đường dẫn ảnh hiện trường"
        string reporter_name "Họ tên người dân (hoặc Ẩn danh)"
        string reporter_phone "Số điện thoại liên lạc"
        string verification_status "PENDING | VERIFIED | REJECTED | RESOLVED"
        string created_at "Thời điểm gửi phản ánh (ISO Timestamp)"
    }

    COMMUNITY_FEEDBACKS {
        string feedback_id PK "Mã định danh bình luận"
        string report_id FK "Mã phản ánh liên kết"
        string user_name "Tên người bình luận"
        string comment "Nội dung ý kiến đóng góp"
        string created_at "Thời điểm đăng bình luận"
    }

    SPATIAL_HOTSPOTS {
        string hotspot_id PK "Mã định danh điểm nóng dịch tễ"
        string cluster_name "Tên ổ dịch / Tuyến đường trọng điểm"
        float lat "Vĩ độ tâm ổ dịch"
        float lon "Kinh độ tâm ổ dịch"
        float radius_meters "Bán kính khoanh vùng Geodesic (100m - 2000m)"
        int case_count "Số ca bệnh lâm sàng ghi nhận"
        int report_count "Số phản ánh cộng đồng trong bán kính"
        float breteau_index "Chỉ số bọ gậy Breteau Index (BI)"
        string risk_level "RED | ORANGE | YELLOW | GREEN"
        string status "ACTIVE | CONTROLLED | RESOLVED"
    }

    RISK_EVALUATIONS {
        string eval_id PK "Mã định danh phiên đánh giá AI"
        string hotspot_id FK "Mã điểm nóng liên kết"
        float multi_modal_risk_score "Chỉ số Rủi ro Đa chiều (0 - 100)"
        float xgboost_predicted_cases "Số ca dự báo từ XGBoost"
        float climate_anomaly_score "Điểm bất thường khí hậu"
        float citizen_density_score "Mật độ phản ánh cộng đồng 500m"
        string ai_advisory_text "Văn bản đánh giá dịch tễ do Gemini sinh"
        string recommended_actions "Danh sách hành động can thiệp y tế"
        string generated_at "Thời điểm AI sinh đánh giá"
    }

    INTERVENTION_LOGS {
        string log_id PK "Mã định danh nhật ký can thiệp"
        string hotspot_id FK "Mã điểm nóng dập dịch"
        string action_type "CHEMICAL_SPRAY | LARVICIDE_DISPERSAL | CLEANUP_CAMPAIGN"
        string team_name "Đội ngũ phụ trách (Đội cơ động HCDC / Đoàn thanh niên)"
        string status "SCHEDULED | IN_PROGRESS | COMPLETED"
        string executed_at "Thời điểm triển khai thực địa"
        string notes "Ghi chú kết quả sau can thiệp"
    }
```

---

#### Hình 9.4.2: Sơ đồ ERD - Miền Nghiệp Vụ Dịch Tễ Học & Địa Không Gian (Epidemiology & Geospatial Domain)
```mermaid
erDiagram
    PROVINCES ||--o{ DISTRICTS : "quan_ly_hanh_chinh"
    DISTRICTS ||--o{ WARDS : "quan_ly_hanh_chinh"
    WARDS ||--o{ STREETS : "chua_tuyen_pho"
    
    PROVINCES ||--o{ HISTORICAL_CASES : "thong_ke_ca_tinh"
    DISTRICTS ||--o{ DISTRICT_CASES : "thong_ke_ca_quan"
    WARDS ||--o{ WARD_CASES : "thong_ke_ca_phuong"
    STREETS ||--o{ STREET_HOTSPOTS : "thong_ke_ca_duong"
    
    PROVINCES ||--o{ EPIDEMIC_CLUSTERS : "co_cum_dich"

    PROVINCES {
        string province_name PK "Tên tỉnh/thành phố (34 tỉnh chuẩn hóa)"
        float default_lat "Vĩ độ trung tâm"
        float default_lon "Kinh độ trung tâm"
        float population "Dân số toàn tỉnh (người)"
    }

    DISTRICTS {
        string district_name PK "Tên quận/huyện"
        string province_name FK "Tỉnh/thành phố trực thuộc"
        float lat "Vĩ độ trung tâm quận"
        float lon "Kinh độ trung tâm quận"
    }

    WARDS {
        string ward_name PK "Tên phường/xã/thị trấn"
        string district_name FK "Quận/huyện trực thuộc"
        float lat "Vĩ độ phường"
        float lon "Kinh độ phường"
    }

    STREETS {
        string street_name PK "Tên đường/phố/ấp"
        string ward_name FK "Phường/xã trực thuộc"
        float lat "Vĩ độ điểm nóng tuyến phố"
        float lon "Kinh độ điểm nóng tuyến phố"
    }

    HISTORICAL_CASES {
        string id PK "Mã bản ghi ca bệnh tỉnh"
        string province FK "Tên tỉnh/thành phố"
        datetime date "Thời điểm báo cáo (cuối tháng)"
        int year "Năm"
        int month "Tháng"
        int cases "Tổng số ca bệnh trong tháng"
        float population "Dân số tỉnh"
        float incidence_rate "Tỷ suất mắc / 100k dân"
    }

    EPIDEMIC_CLUSTERS {
        string cluster_id PK "Mã cụm dịch (ST_xxx, WD_xxx, DT_xxx)"
        string name "Tên gọi vùng ổ dịch"
        string level "Phố | Phường | Quận"
        string province FK "Tỉnh/thành"
        string district "Quận/huyện"
        string ward "Phường/xã"
        string street "Tuyến phố"
        datetime date "Tháng phát hiện ổ dịch"
        int cases "Số ca nhiễm ghi nhận"
        string risk_level "Vùng Đỏ | Vùng Cam | Vùng Vàng | Vùng Xanh"
        string risk_color "Mã màu hex cảnh báo (#d90429...)"
        float radius_meters "Bán kính khoanh vùng dập dịch (mét)"
        string recommendation "Biện pháp can thiệp y tế khuyến cáo"
        float lat "Tọa độ tâm ổ dịch (Vĩ độ)"
        float lon "Tọa độ tâm ổ dịch (Kinh độ)"
    }
```

---

### 9.5. Nhóm Sơ Đồ Lớp Phần Mềm Chi Tiết (Detailed Class Diagrams)

#### Hình 9.5.1: Sơ đồ Lớp - Tầng Truy Cập Dữ Liệu & Quản Lý MongoDB (Data Access Layer Class Diagram)
```mermaid
classDiagram
    class MongoDataService {
        +string uri
        +string db_name
        +MongoClient client
        +Database db
        +bool is_connected
        +string connection_error
        +connect() bool
        +load_dataset(dataset_key: string, local_csv_path: Path) DataFrame
        +save_dataset(dataset_key: string, df: DataFrame, local_csv_path: Path) bool
        +backup_dataframe_to_mongo(dataset_key: string, df: DataFrame) bool
    }

    class DatabaseCollections {
        <<enumeration>>
        HISTORICAL_CASES
        DISTRICT_BREAKDOWN
        WARD_BREAKDOWN
        STREET_HOTSPOTS
        EPIDEMIC_CLUSTERS
        WEATHER_CACHE
        CITIZEN_REPORTS
        SPATIAL_HOTSPOTS
        INTERVENTION_LOGS
    }

    MongoDataService ..> DatabaseCollections : queries
```

---

#### Hình 9.5.2: Sơ đồ Lớp - Phân Hệ Phản Ánh Dịch Tễ Không Gian & Đánh Giá Rủi Ro (Crowdsourcing & Risk Assessment Class Diagram)
```mermaid
classDiagram
    class CitizenReportService {
        -db_manager: MongoDataService
        -spatial_calculator: SpatialRiskCalculator
        +submit_report(report_data: dict) CitizenReport
        +get_reports_in_radius(lat: float, lon: float, radius_m: float) list~CitizenReport~
        +verify_report(report_id: str, status: str, officer_notes: str) bool
        +add_community_feedback(report_id: str, feedback: dict) bool
        +get_crowdsourcing_geojson() dict
    }

    class SpatialRiskCalculator {
        -earth_radius: float
        +calculate_geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) float
        +calculate_community_density(target_lat: float, target_lon: float, radius_m: float) float
        +compute_multi_modal_risk_index(xgboost_cases: float, climate_score: float, community_density: float) float
        +create_geodesic_buffer(lat: float, lon: float, radius_m: float) Polygon
    }

    class XGBoostClimateForecaster {
        -model_path: str
        -model: Booster
        -feature_names: list~str~
        +load_model() bool
        +create_climate_features(weather_df: DataFrame) DataFrame
        +predict_recursive(province: str, horizon_months: int) DataFrame
        +evaluate_metrics(y_true: Series, y_pred: Series) dict
    }

    class GeminiAdvisoryEngine {
        -api_key: str
        -model_name: str
        +evaluate_multi_modal_risk(risk_context: dict) MultiModalAdvisory
        +simulate_scenario(params: ScenarioParams) ScenarioResult
        +chat_consultation(user_prompt: str, history: list) StreamGenerator
        +check_severe_symptoms(prompt: str) bool
    }

    class CitizenReport {
        +report_id: str
        +latitude: float
        +longitude: float
        +report_type: str
        +description: str
        +severity: str
        +verification_status: str
        +created_at: str
    }

    CitizenReportService --> SpatialRiskCalculator : "uses"
    CitizenReportService --> CitizenReport : "manages"
    CitizenReportService ..> GeminiAdvisoryEngine : "provides context for"
    SpatialRiskCalculator ..> XGBoostClimateForecaster : "combines output"
```

---

### 9.6. Nhóm Sơ Đồ Trình Tự Chi Tiết (Detailed Sequence Diagrams)

#### Hình 9.6.1: Sơ đồ Trình tự - Người Dân Gửi Phản Ánh Ổ Lăng Quăng & Nhận Khuyến Nghị Y Tế
```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Người Dân Thực Địa
    participant UI as Bản Đồ Phản Ánh (Streamlit Tab 3)
    participant Service as CitizenReportService
    participant SpatialCalc as SpatialRiskCalculator
    participant DB as MongoDB Manager
    participant ReportsColl as Collection 'citizen_reports'

    Citizen->>UI: Bật định vị GPS hoặc click chọn điểm trên Bản đồ Leaflet
    UI-->>Citizen: Hiển thị Marker tại tọa độ [10.7769, 106.7009]
    Citizen->>UI: Chọn loại "Ổ bọ gậy / Nước đọng", nhập ý kiến mô tả -> Bấm "Gửi Phản Ánh"
    UI->>Service: submit_report(report_payload)
    
    Service->>SpatialCalc: calculate_community_density(10.7769, 106.7009, 500m)
    SpatialCalc->>DB: Truy vấn số phản ánh lân cận trong bán kính 500m
    DB-->>SpatialCalc: 6 phản ánh tồn tại trong khu vực
    SpatialCalc-->>Service: Mật độ cục bộ = 0.65 (Mức nguy cơ Cao)

    Service->>Service: Sinh mã phản ánh duy nhất: "RP-20261115-A1B2"
    Service->>DB: Lưu bản ghi phản ánh vào MongoDB
    DB->>ReportsColl: insert_one(report_document)
    ReportsColl-->>DB: Acknowledged = True
    DB-->>Service: OK

    Service-->>UI: Trả về kết quả ghi nhận thành công kèm khuyến nghị y tế
    UI-->>Citizen: Hiển thị thông báo: "Phản ánh đã được gửi tới HCDC!<br/>Khu vực có mật độ nguy cơ cao. Khuyến cáo: úp chum vại, đổ dầu thải."
```

---

#### Hình 9.6.2: Sơ đồ Trình tự - AI Gemini Đánh Giá Rủi Ro Đa Chiều & Tạo Kế Hoạch Can Thiệp
```mermaid
sequenceDiagram
    autonumber
    actor Officer as Cán Bộ Dịch Tễ (HCDC)
    participant UI as Bảng Điều Phối Dập Dịch (Tab 6)
    participant Advisor as GeminiAdvisoryEngine
    participant ML as XGBoostClimateForecaster
    participant Calc as SpatialRiskCalculator
    participant DB as MongoDB Manager

    Officer->>UI: Chọn địa bàn ("Quận Bình Thạnh") -> Bấm "Kích Hoạt Đánh Giá Rủi Ro Đa Chiều"
    UI->>ML: predict_recursive("Quận Bình Thạnh", horizon=1)
    ML-->>UI: Số ca dự báo tháng tới = 145 ca
    
    UI->>Calc: get_climate_anomaly_and_density("Quận Bình Thạnh")
    Calc->>DB: Lấy dữ liệu trạm quan trắc (mưa, nhiệt độ, độ ẩm) & số phản ánh lăng quăng
    DB-->>Calc: Lượng mưa tăng 40%, 18 phản ánh ổ bọ gậy chưa xử lý
    Calc-->>UI: Điểm thời tiết = 0.78, Mật độ phản ánh = 0.85
    
    UI->>Calc: compute_multi_modal_risk_index(145, 0.78, 0.85)
    Calc-->>UI: Multi-modal Risk Index = 82.4 / 100 (CẤP BÁO ĐỘNG ĐỎ)
    
    UI->>Advisor: evaluate_multi_modal_risk(risk_context)
    Advisor->>Advisor: Gọi Google Gemini 2.5 Flash với Structured JSON Prompt
    Advisor-->>UI: JSON Advisory: Báo cáo dịch tễ, phân tích tương quan mưa - bọ gậy, đề xuất 3 tọa độ phun hóa chất khẩn cấp
    UI-->>Officer: Hiển thị Thẻ Báo Động Đỏ & Dự thảo Kế hoạch Điều phối Xe Dập Dịch
```

---

#### Hình 9.6.3: Sơ đồ Trình tự - Chatbot Y Tế Live Search Grounding & Nhận Diện Ca Bệnh Nặng 115
```mermaid
sequenceDiagram
    autonumber
    actor Patient as Bệnh Nhân / Người Dân
    participant UI as Giao Diện Trò Chuyện (Streamlit Tab 5)
    participant Engine as GeminiChatEngine
    participant GeminiAPI as Google GenAI Client
    participant SearchTool as Google Search Grounding Tool

    Patient->>UI: Gửi câu hỏi: "Tôi bị sốt xuất huyết ngày thứ 3, nôn ra máu và chân tay lạnh thì làm sao?"
    UI->>Engine: process_query_stream(query, role="Nguoi dan", chat_history)

    Engine->>Engine: Khởi tạo System Instruction y tế chuẩn xác
    Engine->>GeminiAPI: chats.create(model="gemini-3.5-flash-lite", tools=[GoogleSearch()])
    Engine->>GeminiAPI: chat.send_message_stream(query)

    GeminiAPI->>SearchTool: Kích hoạt tra cứu thông tin dịch tễ & triệu chứng thực tế
    SearchTool-->>GeminiAPI: Kết quả tra cứu trực tuyến mới nhất
    
    loop Truyền dữ liệu dạng luồng (Token Streaming)
        GeminiAPI-->>Engine: Trả về từng chunk văn bản
        Engine-->>UI: yield chunk (Hiển thị mượt mà qua st.write_stream)
    end

    UI->>UI: Quét toàn bộ nội dung câu hỏi qua danh sách từ khóa nguy kịch (_SEVERE_PATIENT_SIGNS)
    alt Phát hiện từ khóa "nôn ra máu", "chân tay lạnh"
        UI-->>Patient: Nối thêm Khối Cảnh Báo Khẩn Cấp Đỏ (Emergency Warning Box):<br/>🚨 CẢNH BÁO NGUY HIỂM: Dấu hiệu sốt xuất huyết nặng!<br/>Người bệnh cần đến ngay khoa Cấp cứu hoặc gọi 115!
    else Câu hỏi thông thường
        UI-->>Patient: Kết thúc câu trả lời tư vấn chăm sóc tại nhà
    end
```

---

### 9.7. Nhóm Sơ Đồ Chuyển Trạng Thái (State Machine Diagrams)

#### Hình 9.7.1: Sơ đồ Trạng Thái - Vòng Đời Phiếu Phản Ánh Dịch Tễ (CitizenReport Lifecycle)
```mermaid
stateDiagram-v2
    [*] --> SUBMITTED: Người dân gửi phản ánh + Ghim GPS

    SUBMITTED --> PENDING_VERIFICATION: Lưu trữ vào hệ thống & Đưa vào hàng đợi xác minh
    
    PENDING_VERIFICATION --> VERIFIED: Cán bộ y tế thực địa kiểm tra & xác nhận có ổ bọ gậy
    PENDING_VERIFICATION --> REJECTED: Phản ánh không có thật hoặc thông tin sai lệch
    
    VERIFIED --> SCHEDULED_INTERVENTION: Đưa vào danh sách điểm nóng cần xử lý dập dịch
    
    SCHEDULED_INTERVENTION --> IN_PROGRESS: Đội cơ động triển khai phun thuốc / xử lý nước đọng
    
    IN_PROGRESS --> RESOLVED: Hoàn tất dập dịch & Người dân đánh giá kết quả
    
    REJECTED --> [*]
    RESOLVED --> [*]
```

---

#### Hình 9.7.2: Sơ đồ Trạng Thái - Cấp Độ Cảnh Báo Nguy Cơ Khu Vực Dịch Tễ
```mermaid
stateDiagram-v2
    [*] --> GREEN_CONTROL: Số ca < 2 & Không có phản ánh bọ gậy (Vùng Xanh)
    
    GREEN_CONTROL --> YELLOW_WARNING: Xuất hiện 2 ca hoặc phát hiện 1-2 ổ bọ gậy (Vùng Vàng)
    
    YELLOW_WARNING --> ORANGE_HIGH_RISK: Tăng lên 3-4 ca hoặc mật độ phản ánh 500m cao (Vùng Cam)
    YELLOW_WARNING --> GREEN_CONTROL: Đã xử lý vệ sinh môi trường & không phát sinh ca mới
    
    ORANGE_HIGH_RISK --> RED_OUTBREAK: Số ca >= 5 hoặc Breteau Index >= 50 (Vùng Đỏ - Bùng phát dịch)
    ORANGE_HIGH_RISK --> YELLOW_WARNING: Phun hóa chất khoanh vùng & ca bệnh giảm
    
    RED_OUTBREAK --> ORANGE_HIGH_RISK: Dập dịch khẩn cấp thành công, khống chế chuỗi lây
```

---

#### Hình 9.7.3: Sơ đồ Trạng Thái - Phân Tầng Cảnh Báo Nguy Cơ Dịch Tễ
```mermaid
stateDiagram-v2
    [*] --> VungXanh : Số ca mắc ở mức kiểm soát thấp

    VungXanh --> VungVang : Số ca vượt ngưỡng cảnh báo (Tuyến: 2 ca | Phường: 3 ca | Quận: 5 ca)
    VungVang --> VungCam : Dịch lan rộng (Tuyến: 3 ca | Phường: 8 ca | Quận: 20 ca)
    VungCam --> VungDo : Bùng phát ổ dịch lớn (Tuyến: >= 5 ca | Phường: >= 15 ca | Quận: >= 50 ca)

    VungDo --> VungCam : Hiệu quả can thiệp dập dịch: Số ca giảm xuống ngưỡng an toàn
    VungCam --> VungVang : Giám sát chặt chẽ: Ổ dịch cục bộ được khống chế
    VungVang --> VungXanh : Vệ sinh môi trường triệt để: Hết chu kỳ lây nhiễm
```

---

### 9.8. Nhóm Sơ Đồ Thành Phần & Triển Khai Hạ Tầng (Component & Deployment Diagrams)

#### Hình 9.8.1: Sơ đồ Thành Phần Phần Mềm (Software Component Diagram)
```mermaid
flowchart TB
    subgraph UI_Components ["Tầng Giao Diện Người Dùng (UI Components)"]
        CMP_Dashboard["src/dashboard.py<br/>(Streamlit Web Main App & HCDC Dispatch)"]
        CMP_Sidebar["src/sidebar/ & src/ui_theme.py<br/>(Theme, Role Switcher & UI Widgets)"]
        CMP_ArcGIS["src/arcgis_component/index.html<br/>(ArcGIS Maps SDK 4.29 2D/3D)"]
        CMP_CrowdMap["src/map_component/index.html<br/>(Leaflet Interactive Map)"]
        CMP_Chatbot["src/chatbot/gemini_chat_engine.py<br/>(Streaming Chat Interface)"]
    end

    subgraph Service_Components ["Tầng Dịch Vụ Nghiệp Vụ (Service Components)"]
        CMP_CrowdSvc["src/map_pins_service.py<br/>(Pins Status & Cluster Actions)"]
        CMP_AuthSvc["src/booking/doctor_auth.py<br/>(SHA-256 HCDC Officer Auth)"]
        CMP_AIPredict["src/ai_prediction_service.py<br/>(Gemini Prediction Service)"]
        CMP_WeatherSvc["src/weather_service.py<br/>(Weather Client & Scheduler)"]
    end

    subgraph Core_Components ["Tầng Lõi Xử Lý Dữ Liệu & Học Máy (Core Processing Components)"]
        CMP_DataProc["src/data_processor.py<br/>(NLP Parser, Dedup, Aggregation)"]
        CMP_Model["src/model.py<br/>(XGBoost Province + HCMC District)"]
        CMP_GIS["src/gis_mapper.py<br/>(GeoPandas, HCMC Districts & Buffer)"]
        CMP_MongoSvc["src/mongo_data_service.py<br/>(MongoDB Persistence Layer)"]
        CMP_Paths["src/paths.py & src/config.py<br/>(Path Management & Env Settings)"]
    end

    subgraph External_Libraries ["Thư Viện Phụ Thuộc Ngoại Vi (External Libraries)"]
        LIB_XGB["xgboost"]
        LIB_SKL["scikit-learn"]
        LIB_PD["pandas & numpy"]
        LIB_GPD["geopandas & shapely"]
        LIB_GENAI["google-genai"]
        LIB_MONGO["pymongo"]
        LIB_APS["apscheduler"]
    end

    CMP_Dashboard --> CMP_ArcGIS & CMP_CrowdMap & CMP_CrowdSvc & CMP_AuthSvc & CMP_AIPredict & CMP_Chatbot & CMP_WeatherSvc & CMP_GIS & CMP_Sidebar
    CMP_CrowdSvc --> CMP_MongoSvc
    CMP_AIPredict --> CMP_MongoSvc
    CMP_WeatherSvc --> CMP_MongoSvc
    CMP_DataProc --> CMP_MongoSvc

    CMP_DataProc --> LIB_PD
    CMP_Model --> LIB_XGB & LIB_SKL & LIB_PD
    CMP_GIS --> LIB_GPD
    CMP_AIPredict & CMP_Chatbot --> LIB_GENAI
    CMP_MongoSvc --> LIB_MONGO
    CMP_WeatherSvc --> LIB_APS
```

---

#### Hình 9.8.2: Sơ đồ Triển Khai Hạ Tầng Hệ Thống (Infrastructure Deployment Diagram)
```mermaid
flowchart TB
    subgraph ClientDevices ["Tầng Thiết Bị Đầu Cuối (Client Devices)"]
        Dev_Citizen["Điện Thoại Thông Minh Người Dân<br/>(Ghim vị trí GPS & Bình luận thực địa)"]
        Dev_Officer["Trạm Giám Sát Cán Bộ Y Tế Dự Phòng (HCDC)<br/>(Workstation Màn Hình Lớn / Dashboard)"]
    end

    subgraph ProductionServer ["Máy Chủ Triển Khai Ứng Dụng (Application Host Server)"]
        subgraph WebProxy ["Cổng Mạng & Web Proxy"]
            Port_8501["Port 8501: Streamlit Main Application Service"]
        end

        subgraph VirtualEnv ["Môi Trường Thực Thi Python (.venv)"]
            Runtime_Python["Python 3.10 - 3.13 Runtime Engine"]
            subgraph AppProcesses ["Các Tiến Trình Ứng Dụng Đang Chạy"]
                PROC_Streamlit["Process: streamlit run src/dashboard.py"]
                PROC_Scheduler["Daemon Thread: APScheduler Background Worker"]
            end
        end

        subgraph LocalDiskStorage ["Ổ Đĩa Cục Bộ Tốc Độ Cao (Local NVMe Storage)"]
            DIR_Raw["data/raw/ (data2024.xlsx, data2025.xlsx)"]
            DIR_Proc["data/processed/ (*.csv, ai_cache.json)"]
            DIR_Out["outputs/ (dengue_model.pkl, *.geojson)"]
        end
    end

    subgraph CloudDatabases ["Cơ Sở Dữ Liệu Đám Mây (Cloud DBaaS)"]
        subgraph MongoAtlasCluster ["MongoDB Atlas Cloud Cluster (Primary Database)"]
            DB_Crowd[("dengue_prediction_db<br/>• citizen_reports, spatial_hotspots<br/>• intervention_logs, feedbacks")]
            DB_Datasets[("dengue_datasets<br/>• historical_cases, weather_cache")]
        end
    end

    subgraph ExternalAPIs ["Các Dịch Vụ API Đám Mây (External Cloud APIs)"]
        API_Gemini["Google Gemini AI Platform<br/>(gemini-2.5-flash / gemini-3.5-flash-lite)"]
        API_Weather["WeatherAPI.com Historical Service<br/>(Key: WEATHERAPI_KEY)"]
        API_Meteo["Open-Meteo Reanalysis API<br/>(Endpoint: archive-api.open-meteo.com)"]
        API_OpenAQ["OpenAQ Platform API<br/>(Ground Sensor Air Quality)"]
    end

    Dev_Citizen -->|HTTPS:8501 (Mobile Web)| Port_8501
    Dev_Officer -->|HTTPS:8501 (Dashboard)| Port_8501

    Port_8501 --> PROC_Streamlit
    PROC_Streamlit & PROC_Scheduler --> Runtime_Python
    Runtime_Python <-->|POSIX File I/O| LocalDiskStorage
    Runtime_Python <-->|TLS 1.3 / Port 27017 / SRV Protocol| MongoAtlasCluster
    Runtime_Python <-->|HTTPS REST API / gRPC| API_Gemini
    Runtime_Python <-->|HTTPS GET JSON| API_Weather & API_Meteo & API_OpenAQ
```
