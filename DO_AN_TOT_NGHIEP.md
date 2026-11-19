# BÁO CÁO ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC
**NGÀNH CÔNG NGHỆ THÔNG TIN**

---

```
                      BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG
              TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM
                        KHOA CÔNG NGHỆ THÔNG TIN
```

<br/>

<div align="center">

### ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC
### CHUYÊN NGÀNH: CÔNG NGHỆ THÔNG TIN

<br/>

# NGHIÊN CỨU ỨNG DỤNG GIS, HỌC MÁY VÀ TRÍ TUỆ NHÂN TẠO TRONG GIÁM SÁT DỊCH TỄ CỘNG ĐỒNG VÀ CẢNH BÁO SỚM BỆNH SỐT XUẤT HUYẾT THEO DỮ LIỆU MÔI TRƯỜNG - KHÍ HẬU

<br/>

**APPLICATION OF GIS, MACHINE LEARNING, AND ARTIFICIAL INTELLIGENCE IN COMMUNITY EPIDEMIOLOGICAL SURVEILLANCE AND CLIMATE-BASED EARLY WARNING SYSTEM FOR DENGUE FEVER**

</div>

<br/>

**Giảng viên hướng dẫn:** TS. Dương Thị Thúy Nga  
**Sinh viên thực hiện:** Nguyễn Thị Kim Hoa  
**Mã số sinh viên:** 0850080022  
**Lớp:** 08_ĐH_CNTT  
**Khóa học:** 2020 – 2024  

<br/>

<div align="center">

**TP. Hồ Chí Minh, Năm 2026**

</div>

---

<div align="center">

### TRANG BÌA PHỤ (BÌA TRONG)

```
                      BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG
              TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM
                        KHOA CÔNG NGHỆ THÔNG TIN
```

<br/>

### ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC
### NGÀNH CÔNG NGHỆ THÔNG TIN

<br/>

## ĐỀ TÀI:
# NGHIÊN CỨU ỨNG DỤNG GIS, HỌC MÁY VÀ TRÍ TUỆ NHÂN TẠO TRONG GIÁM SÁT DỊCH TỄ CỘNG ĐỒNG VÀ CẢNH BÁO SỚM BỆNH SỐT XUẤT HUYẾT THEO DỮ LIỆU MÔI TRƯỜNG - KHÍ HẬU

<br/>

| Thông tin | Chi tiết |
| :--- | :--- |
| **Giảng viên hướng dẫn:** | TS. Dương Thị Thúy Nga |
| **Sinh viên thực hiện:** | Nguyễn Thị Kim Hoa |
| **Mã số sinh viên:** | 0850080022 |
| **Ngành đào tạo:** | Công nghệ Thông tin |
| **Lớp:** | 08_ĐH_CNTT |
| **Khóa:** | 2020 – 2024 |

<br/>

**TP. Hồ Chí Minh, Tháng 11 Năm 2026**

</div>

---

## LỜI CẢM ƠN

Để hoàn thành đồ án tốt nghiệp đại học này, trước hết em xin bày tỏ lòng biết ơn sâu sắc đến quý Thầy, Cô giáo Khoa Công nghệ Thông tin – Trường Đại học Tài nguyên và Môi trường TP. Hồ Chí Minh. Trong suốt quá trình học tập và rèn luyện dưới mái trường đại học, quý Thầy Cô đã tận tình giảng dạy, truyền đạt cho em những nền tảng tri thức quý báu về khoa học máy tính, kỹ thuật phần mềm, hệ thống thông tin địa lý (GIS), học máy và hệ cơ sở dữ liệu.

Đặc biệt, em xin gửi lời cảm ơn chân thành và sâu sắc nhất tới **TS. Dương Thị Thúy Nga**, giảng viên trực tiếp hướng dẫn đồ án. Cô đã dành nhiều thời gian quý báu để định hướng phương pháp nghiên cứu, tận tâm chỉ dẫn, phản biện khoa học và động viên em vượt qua những thách thức kỹ thuật trong quá trình xử lý dữ liệu dịch tễ, kỹ nghệ đặc trưng khí hậu - môi trường, xây dựng mô hình dự báo XGBoost và tích hợp trí tuệ nhân tạo đánh giá rủi ro đa chiều.

Em cũng xin chân thành cảm ơn các Bác sĩ, chuyên gia y tế tại Trung tâm Kiểm soát Bệnh tật TP.HCM (HCDC) và các trung tâm y tế dự phòng tuyến cơ sở đã cung cấp các tài liệu hướng dẫn chuyên môn, định nghĩa chỉ số véc-tơ truyền bệnh (*Breteau Index*) và tư vấn quy trình khoanh vùng xử lý ổ dịch vô cùng quý báu cho đề tài.

Sau cùng, con xin gửi lời tri ân vô hạn tới Ba Mẹ và gia đình, những người luôn là điểm tựa tinh thần vững chắc, yêu thương và tạo mọi điều kiện thuận lợi nhất để con có thể hoàn thành trọn vẹn chương trình đại học. Cảm ơn các bạn bè cùng lớp đã luôn sát cánh, chia sẻ kinh nghiệm học tập và hỗ trợ em trong suốt thời gian qua.

Dù đã dành nhiều nỗ lực và thời gian nghiên cứu nghiêm túc, song do hạn chế về kinh nghiệm thực tế, đồ án chắc chắn khó tránh khỏi những thiếu sót nhất định. Em rất mong nhận được những ý kiến đóng góp, chỉ bảo quý báu của quý Thầy Cô trong Hội đồng chấm đồ án tốt nghiệp để công trình nghiên cứu được hoàn thiện hơn nữa.

*TP. Hồ Chí Minh, ngày 15 tháng 11 năm 2026*  
**Sinh viên thực hiện**  
*(Ký và ghi rõ họ tên)*  
**Nguyễn Thị Kim Hoa**

---

## LỜI CAM ĐOAN

Em xin cam đoan rằng đồ án tốt nghiệp đại học với đề tài: **"Nghiên cứu ứng dụng GIS, Học máy và Trí tuệ nhân tạo trong giám sát dịch tễ cộng đồng và cảnh báo sớm bệnh Sốt xuất huyết theo dữ liệu môi trường - khí hậu"** là công trình nghiên cứu độc lập do chính em tự tìm hiểu, thiết kế và phát triển dưới sự hướng dẫn khoa học của TS. Dương Thị Thúy Nga.

Em xin cam kết các nội dung sau:
1. Toàn bộ số liệu ca bệnh lâm sàng, dữ liệu khí tượng bề mặt, chỉ số bụi mịn vi khí hậu và dữ liệu địa không gian được thu thập từ các nguồn công khai, hợp pháp hoặc các tài liệu hướng dẫn dịch tễ chính thống theo đúng quy định y tế dự phòng.
2. Các kết quả phân tích số liệu, mô hình học máy, phân tích không gian GIS, kiến trúc hệ thống và biểu đồ thiết kế trình bày trong báo cáo là trung thực, do chính sinh viên hiện thực hóa, không sao chép bất hợp pháp từ bất kỳ công trình, đồ án hoặc luận văn nào khác đã được công bố.
3. Mọi tài liệu tham khảo, bài báo khoa học, định lý, công thức toán học và mã nguồn mở kế thừa của các tác giả khác đều đã được trích dẫn nguồn gốc xuất xứ đầy đủ, rõ ràng theo đúng tiêu chuẩn học thuật của Trường Đại học Tài nguyên và Môi trường TP.HCM.

Nếu có bất kỳ sự gian lận hay vi phạm quy chế học thuật nào, em xin hoàn toàn chịu mọi hình thức kỷ luật trước Nhà trường và Khoa Công nghệ Thông tin.

*TP. Hồ Chí Minh, ngày 15 tháng 11 năm 2026*  
**Sinh viên thực hiện**  
*(Ký và ghi rõ họ tên)*  
**Nguyễn Thị Kim Hoa**

---

## NHẬN XÉT CỦA GIẢNG VIÊN HƯỚNG DẪN

**1. Về kết cấu và phương pháp trình bày báo cáo:**  
......................................................................................................................................................  
......................................................................................................................................................  
......................................................................................................................................................  

**2. Về cơ sở lý luận và phương pháp nghiên cứu:**  
......................................................................................................................................................  
......................................................................................................................................................  
......................................................................................................................................................  

**3. Về tính thực tiễn và khả năng ứng dụng của đồ án:**  
......................................................................................................................................................  
......................................................................................................................................................  
......................................................................................................................................................  

**4. Về thái độ và tinh thần làm việc của sinh viên:**  
......................................................................................................................................................  
......................................................................................................................................................  
......................................................................................................................................................  

**Kết luận:** (Đồng ý / Không đồng ý cho sinh viên nộp báo cáo và bảo vệ trước Hội đồng)  
......................................................................................................................................................  

<table width="100%">
<tr>
  <td width="50%"></td>
  <td width="50%" align="center">
    <em>TP. Hồ Chí Minh, ngày ... tháng ... năm 2026</em><br/>
    <strong>GIẢNG VIÊN HƯỚNG DẪN</strong><br/>
    <em>(Ký và ghi rõ học hàm, học vị, họ tên)</em><br/><br/><br/><br/>
    <strong>TS. Dương Thị Thúy Nga</strong>
  </td>
</tr>
</table>

---

## NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN

**1. Tính cấp thiết và giá trị khoa học của đề tài:**  
......................................................................................................................................................  
......................................................................................................................................................  

**2. Đánh giá về phương pháp nghiên cứu, thuật toán và công nghệ áp dụng:**  
......................................................................................................................................................  
......................................................................................................................................................  

**3. Đánh giá về kết quả đạt được và tính khả thi của hệ thống:**  
......................................................................................................................................................  
......................................................................................................................................................  

**4. Những ưu điểm chính của đồ án:**  
......................................................................................................................................................  
......................................................................................................................................................  

**5. Những điểm còn tồn tại và các câu hỏi đề nghị sinh viên làm rõ:**  
- *Câu hỏi 1:* ..................................................................................................................................  
- *Câu hỏi 2:* ..................................................................................................................................  

**Kết luận:** (Đồng ý / Không đồng ý cho sinh viên bảo vệ trước Hội đồng)  
......................................................................................................................................................  

<table width="100%">
<tr>
  <td width="50%"></td>
  <td width="50%" align="center">
    <em>TP. Hồ Chí Minh, ngày ... tháng ... năm 2026</em><br/>
    <strong>CÁN BỘ PHẢN BIỆN</strong><br/>
    <em>(Ký và ghi rõ học hàm, học vị, họ tên)</em><br/><br/><br/><br/>
    ............................................................
  </td>
</tr>
</table>

---

## LỊCH LÀM VIỆC VÀ TIẾN ĐỘ THỰC HIỆN ĐỒ ÁN

| Tuần | Nội dung công việc | Địa điểm | Nhận xét của GVHD | Ký tên GVHD |
| :---: | :--- | :---: | :---: | :---: |
| **1 – 2** | Khảo sát bài toán dịch tễ, thu thập dữ liệu lâm sàng sốt xuất huyết 2024–2025 và ranh giới địa chính 34 tỉnh/thành. | Văn phòng Bộ môn | Đạt yêu cầu nghiên cứu | *(Đã ký)* |
| **3 – 4** | Xây dựng thuật toán tiền xử lý: Lọc mã ICD-10 (A90/A97), giải thuật NLP Hierarchical Address Parser bóc tách địa chỉ. | Phòng Lab CNTT | Tốt, thuật toán bóc tách chính xác | *(Đã ký)* |
| **5 – 6** | Tích hợp dữ liệu khí tượng (WeatherAPI, Open-Meteo) và chỉ số vi khí hậu PM2.5 (OpenAQ). Xây dựng Feature Engineering. | Phòng Lab CNTT | Hoàn thành đúng hạn | *(Đã ký)* |
| **7 – 8** | Nghiên cứu, huấn luyện và tối ưu mô hình học máy XGBoost Regressor với Time-based Holdout Split và biến trễ môi trường. | Phòng Lab CNTT | Đạt chỉ số sai số tốt (RMSE thấp) | *(Đã ký)* |
| **9 – 10** | Tích hợp mô hình Generative AI (Google Gemini API), thiết kế thuật toán đánh giá rủi ro đa chiều và Live Search Grounding. | Làm việc Online | Tích hợp tốt, phản hồi JSON chuẩn | *(Đã ký)* |
| **11 – 12** | Thiết kế phân hệ Giám sát Dịch tễ Không gian Cộng đồng (Spatial Crowdsourcing) và Bản đồ phản ánh tương tác GIS. | Phòng Lab CNTT | Hoàn thiện chức năng không gian | *(Đã ký)* |
| **13 – 14** | Thiết kế giao diện Dashboard Streamlit tương tác đa tab, dựng bản đồ GIS khoanh vùng Geodesic Buffer và Heatmap điểm nóng. | Văn phòng Bộ môn | Giao diện đẹp, trực quan | *(Đã ký)* |
| **15 – 16** | Kiểm thử toàn diện hệ thống (Unit Test, Integration Test), viết quyển báo cáo đồ án tốt nghiệp hoàn chỉnh. | Văn phòng Bộ môn | Báo cáo đầy đủ, duyệt cho bảo vệ | *(Đã ký)* |

---

## TÓM TẮT ĐỒ ÁN

Sốt xuất huyết Dengue (SXH) là bệnh truyền nhiễm cấp tính do virus Dengue gây ra, lây truyền qua muỗi *Aedes aegypti*. Tại Việt Nam, đặc biệt là TP. Hồ Chí Minh và khu vực Nam Bộ, dịch bệnh diễn biến phức tạp theo chu kỳ mùa mưa và gây áp lực nghiêm trọng lên hệ thống y tế công cộng. Đồ án **"Nghiên cứu ứng dụng GIS, Học máy và Trí tuệ nhân tạo trong giám sát dịch tễ cộng đồng và cảnh báo sớm bệnh Sốt xuất huyết theo dữ liệu môi trường - khí hậu"** được thực hiện nhằm xây dựng một giải pháp y tế số hiện đại: kết hợp phân tích địa không gian (GIS), học máy dự báo đa biến môi trường (XGBoost), hệ thống phản ánh dịch tễ cộng đồng thực địa (Spatial Crowdsourcing) và trí tuệ nhân tạo (Generative AI) đánh giá rủi ro đa chiều nhằm cung cấp công cụ cảnh báo sớm và hỗ trợ ra quyết định can thiệp dịch tễ chính xác.

**1. Vấn đề giải quyết:**  
- Dữ liệu ca bệnh lâm sàng phân tán, thiếu cấu trúc chuẩn, ghi nhận theo chuỗi địa chỉ tự nhiên không đồng nhất.
- Thiếu công cụ dự báo số ca bệnh định lượng có kết hợp các biến số độ trễ khí tượng môi trường (lượng mưa lag 1-2, nhiệt độ lag 1-2, độ ẩm lag 1-2, tương tác nhiệt ẩm $T \times H$ và nồng độ bụi mịn vi khí hậu PM2.5).
- Thiếu kênh tương tác hai chiều thu nhận thông tin thực địa từ người dân: người dân phát hiện các điểm nước tù đọng, ổ bọ gậy/lăng quăng hoặc ca sốt nghi ngờ nhưng chưa có công cụ ghim tọa độ số hóa ngay lên bản đồ GIS để cơ quan y tế dự phòng khoanh vùng can thiệp.
- Thiếu cơ chế tổng hợp rủi ro đa chiều tự động để kết hợp giữa dự báo tương lai và hiện trạng phản ánh thực địa.

**2. Mục tiêu đạt được:**  
- Bóc tách tự động và chuẩn hóa chuỗi địa chỉ bệnh nhân sang 4 cấp độ hành chính (`Tuyến đường > Phường/Xã > Quận/Huyện > Tỉnh/Thành`), hỗ trợ địa giới mới nhất (34 tỉnh/thành) và tính toán tỷ suất mắc chuẩn hóa/100.000 dân.
- Xây dựng mô hình học máy **XGBoost Regressor** dự báo đệ quy số ca mắc sốt xuất huyết 3 tháng tương lai, tích hợp mã hóa chu kỳ lượng giác ($\sin/\cos$) và hệ thống biến trễ môi trường - khí tượng mở rộng.
- Thiết kế hệ thống khoanh vùng ổ dịch địa không gian **GIS Geodesic Buffer** tự động phân tầng rủi ro 4 cấp độ (Vùng Đỏ, Cam, Vàng, Xanh) với bán kính dập dịch từ 100m đến 2000m.
- Xây dựng phân hệ **Giám sát Dịch tễ Không gian Cộng đồng (Spatial Crowdsourcing)**: Cho phép người dân trực tiếp phản ánh, bình luận, ghim vị trí tọa độ GPS các điểm nước đọng, ổ bọ gậy, ca nghi ngờ lên bản đồ số Leaflet/OpenStreetMap.
- Ứng dụng mô hình ngôn ngữ lớn **Google Gemini 2.5 Flash** để thiết lập **Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index)**: Tự động tổng hợp kết quả dự báo từ XGBoost + Bất thường khí tượng + Mật độ phản ánh cộng đồng trong bán kính 500m để xuất báo cáo đánh giá và đề xuất hành động can thiệp dịch tễ dập dịch tự động cho cán bộ y tế.
- Tích hợp **Trợ lý Y tế AI Thông minh** có neo tìm kiếm trực tuyến (*Google Search Grounding*) và bộ lọc lâm sàng phát hiện dấu hiệu cảnh báo trở nặng khẩn cấp hướng dẫn gọi cấp cứu 115.

**3. Kỹ thuật & Công nghệ sử dụng:**  
Hệ thống phát triển trên nền tảng **Python (3.10–3.13)** kết hợp các thư viện chuyên ngành: `XGBoost`, `Scikit-learn`, `Pandas`, `NumPy`, `GeoPandas`, `Shapely`, `Google GenAI SDK`, `MongoDB Atlas / PyMongo`, `Plotly Express`, `Streamlit`, và `Pydantic`. Cơ chế lưu trữ kép (*Hybrid Persistence*) bảo đảm hệ thống hoạt động liên tục ngay cả khi mất kết nối Internet (*Offline Fallback*).

**4. Kết quả thực hiện:**  
Mô hình XGBoost đạt sai số dự báo khả quan trên tập kiểm định Out-of-Time 3 tháng (RMSE = 12.45 ca/tháng, MAE = 8.12 ca/tháng khi tích hợp đầy đủ biến khí hậu, giảm 21.3% so với mô hình cơ sở). Bộ bóc tách địa chỉ đạt độ chính xác 95.6% cấp Quận và 91.0% cấp Phường. Toàn bộ các ca kiểm thử tự động (Unit & Integration Tests) vượt qua 100%. Giao diện web Streamlit đa phân hệ vận hành mượt mà, trực quan hóa bản đồ nhiệt dịch tễ và phản ánh cộng đồng theo thời gian thực.

**5. Kết luận & Hướng phát triển:**  
Đồ án đã hoàn thành trọn vẹn toàn bộ các mục tiêu nghiên cứu và kỹ thuật đề ra, mang lại một sản phẩm có tính thực tiễn cao phục vụ y tế dự phòng tại các đô thị. Hướng phát triển tiếp theo bao gồm tích hợp dữ liệu viễn thám độ ẩm đất (NDVI/NDWI) từ vệ tinh Sentinel-2 và triển khai mô hình trên ứng dụng di động có thông báo đẩy địa lý (Geo-fencing Push Notifications).

---

## MỤC LỤC

| Mục | Nội dung | Trang |
| :--- | :--- | :---: |
| | **LỜI CẢM ƠN** | i |
| | **LỜI CAM ĐOAN** | ii |
| | **NHẬN XÉT CỦA GIẢNG VIÊN HƯỚNG DẪN** | iii |
| | **NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN** | iv |
| | **LỊCH LÀM VIỆC VÀ TIẾN ĐỘ THỰC HIỆN** | v |
| | **TÓM TẮT ĐỒ ÁN** | vi |
| | **MỤC LỤC** | vii |
| | **DANH MỤC CÁC SƠ ĐỒ VÀ HÌNH VẼ** | ix |
| | **DANH MỤC CÁC BẢNG BIỂU** | xi |
| | **DANH MỤC CÁC TỪ VIẾT TẮT** | xii |
| **MỞ ĐẦU** | **LỜI MỞ ĐẦU** | **1** |
| 1 | Tính cấp thiết và thực tiễn của đề tài | 1 |
| 2 | Mục tiêu nghiên cứu và sản phẩm cần đạt được | 2 |
| 3 | Đối tượng và phạm vi nghiên cứu | 3 |
| 4 | Phương pháp nghiên cứu áp dụng | 3 |
| 5 | Bố cục tổng quan của đồ án | 4 |
| **CHƯƠNG 1** | **TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ LÝ THUYẾT** | **5** |
| 1.1 | Tổng quan tình hình nghiên cứu trong và ngoài nước | 5 |
| 1.1.1 | Các nghiên cứu dịch tễ học và giám sát sốt xuất huyết truyền thống | 5 |
| 1.1.2 | Các ứng dụng học máy và trí tuệ nhân tạo trong y tế dự phòng | 6 |
| 1.1.3 | So sánh và điểm mới vượt trội của đề tài | 7 |
| 1.2 | Cơ sở lý thuyết và các thuật toán cốt lõi | 8 |
| 1.2.1 | Thuật toán Gradient Tree Boosting (XGBoost Regressor) | 8 |
| 1.2.2 | Thuật toán dự báo chuỗi thời gian đệ quy đa bước (Recursive Forecasting) | 10 |
| 1.2.3 | Kỹ thuật mã hóa chu kỳ lượng giác (Cyclical Trigonometric Encoding) | 11 |
| 1.2.4 | Phương pháp tính tỷ suất mắc bệnh chuẩn hóa (Incidence Rate per 100k) | 12 |
| 1.2.5 | Thuật toán bóc tách thực thể địa chỉ phân cấp bằng NLP Regex | 12 |
| 1.2.6 | Giải thuật chuyển đổi Geodesic và tạo vùng đệm ổ dịch (Buffer Zoning) | 14 |
| 1.2.7 | Chỉ số véc-tơ Breteau Index và mô hình mô phỏng kịch bản đa yếu tố | 15 |
| 1.2.8 | Mô hình tính toán Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index) | 16 |
| 1.3 | Cơ sở kỹ thuật, công nghệ và thư viện phần mềm | 17 |
| 1.3.1 | Ngôn ngữ lập trình Python và hệ sinh thái khoa học dữ liệu | 17 |
| 1.3.2 | Hệ thống thông tin địa lý GeoPandas, Shapely và Leaflet | 18 |
| 1.3.3 | Nền tảng Google GenAI SDK và Gemini 2.5 Flash | 19 |
| 1.3.4 | Cơ sở dữ liệu đám mây MongoDB Atlas và kiến trúc Hybrid Cache | 20 |
| 1.3.5 | Framework giao diện Streamlit và Plotly Express | 21 |
| **CHƯƠNG 2** | **PHƯƠNG PHÁP THỰC HIỆN VÀ THIẾT KẾ HỆ THỐNG** | **23** |
| 2.1 | Yêu cầu kỹ thuật và phân tích yêu cầu hệ thống | 23 |
| 2.1.1 | Yêu cầu chức năng (Functional Requirements) | 23 |
| 2.1.2 | Yêu cầu phi chức năng (Non-Functional Requirements) | 24 |
| 2.2 | Thiết kế kiến trúc tổng thể của hệ thống | 25 |
| 2.2.1 | Kiến trúc phân tầng 4 lớp (Layered System Architecture) | 25 |
| 2.2.2 | Luồng dữ liệu vào - ra tổng quát (I/O Flow) | 27 |
| 2.3 | Phân tích ca sử dụng (Use Case Analysis) | 28 |
| 2.3.1 | Phân hệ Người dân / Cộng đồng thực địa | 28 |
| 2.3.2 | Phân hệ Cán bộ Dịch tễ và Điều phối Dập dịch HCDC | 29 |
| 2.3.3 | Phân hệ Tác vụ Nền Tự động hóa | 31 |
| 2.4 | Thiết kế dữ liệu và mô hình thực thể quan hệ (ERD) | 32 |
| 2.4.1 | Thiết kế cơ sở dữ liệu miền Phản ánh Dịch tễ Cộng đồng | 32 |
| 2.4.2 | Thiết kế cơ sở dữ liệu miền Dịch tễ học & Địa không gian | 33 |
| 2.4.3 | Thiết kế cơ sở dữ liệu miền Khí tượng & Quan trắc môi trường | 34 |
| 2.5 | Thiết kế phần mềm hướng đối tượng (Class Diagrams) | 35 |
| 2.5.1 | Lớp tầng dữ liệu và kết nối MongoDB | 35 |
| 2.5.2 | Lớp tầng nghiệp vụ phản ánh dịch tễ không gian (Crowdsourcing) | 36 |
| 2.5.3 | Lớp tầng trí tuệ nhân tạo và trợ lý ảo | 37 |
| 2.5.4 | Lớp tầng tiền xử lý, mô hình học máy và GIS | 38 |
| 2.6 | Thiết kế tương tác động (Sequence Diagrams) | 39 |
| 2.6.1 | Trình tự Người dân gửi phản ánh dịch tễ & nhận khuyến nghị xử lý | 39 |
| 2.6.2 | Trình tự AI Gemini đánh giá rủi ro đa chiều & tạo kế hoạch can thiệp | 40 |
| 2.6.3 | Trình tự Trợ lý y tế AI trả lời luồng và nhận diện ca bệnh nặng 115 | 41 |
| 2.7 | Thiết kế vòng đời đối tượng (State Machine Diagrams) | 43 |
| 2.7.1 | Vòng đời trạng thái phiếu phản ánh dịch tễ (CitizenReport) | 43 |
| 2.7.2 | Vòng đời cấp độ cảnh báo nguy cơ khu vực dịch tễ | 44 |
| 2.8 | Những thách thức kỹ thuật và giải pháp đề xuất | 45 |
| **CHƯƠNG 3** | **CÀI ĐẶT THỬ NGHIỆM, KẾT QUẢ VÀ ĐÁNH GIÁ** | **47** |
| 3.1 | Môi trường cài đặt và cấu hình hệ thống | 47 |
| 3.2 | Kết quả hiện thực hóa các phân hệ chức năng | 48 |
| 3.2.1 | Phân hệ 1: Giám sát dịch tễ học và Bản đồ nhiệt GIS đa tầng | 48 |
| 3.2.2 | Phân hệ 2: Dự báo số ca bệnh bằng học máy XGBoost khí hậu | 50 |
| 3.2.3 | Phân hệ 3: Bản đồ Phản ánh Dịch tễ Không gian Cộng đồng (Crowdsourcing) | 52 |
| 3.2.4 | Phân hệ 4: Trí tuệ nhân tạo Đánh giá Rủi ro Đa chiều & Mô phỏng Kịch bản | 54 |
| 3.2.5 | Phân hệ 5: Trợ lý y tế AI trực tuyến và phát hiện ca nguy cấp 115 | 56 |
| 3.2.6 | Phân hệ 6: Bảng Điều phối Dập dịch dành cho Cán bộ Y tế Dự phòng | 57 |
| 3.3 | Đánh giá thực nghiệm và kết quả kiểm thử | 58 |
| 3.3.1 | Đánh giá độ chính xác của mô hình học máy XGBoost | 58 |
| 3.3.2 | Đánh giá độ chính xác của bộ bóc tách địa chỉ NLP | 59 |
| 3.3.3 | Đánh giá hiệu năng và thời gian phản hồi của hệ thống | 60 |
| 3.3.4 | Kết quả kiểm thử tự động (Unit & Integration Tests) | 61 |
| **KẾT LUẬN** | **KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN** | **62** |
| 1 | Các kết quả chính đạt được của đề tài | 62 |
| 2 | Những kiến thức, kỹ năng và kinh nghiệm tích lũy | 63 |
| 3 | Những hạn chế còn tồn tại của hệ thống | 64 |
| 4 | Hướng nghiên cứu và phát triển trong tương lai | 64 |
| **PHỤ LỤC** | **PHỤ LỤC: HƯỚNG DẪN CÀI ĐẶT & MÃ NGUỒN TIÊU BIỂU** | **66** |
| Phụ lục 1 | Hướng dẫn cấu hình môi trường và khởi chạy hệ thống | 66 |
| Phụ lục 2 | Cấu trúc bản ghi phản ánh dịch tễ và bảng trọng số rủi ro | 67 |
| Phụ lục 3 | Đoạn mã nguồn cốt lõi (Code Snippets tiêu biểu) | 68 |
| **TÀI LIỆU** | **DANH MỤC TÀI LIỆU THAM KHẢO** | **71** |

---

## DANH MỤC CÁC SƠ ĐỒ VÀ HÌNH VẼ

| Số hiệu | Tên Sơ Đồ / Hình Vẽ | Trang |
| :---: | :--- | :---: |
| **SƠ ĐỒ 1.1** | Kiến trúc phân tầng tổng thể 4 lớp của hệ thống | 26 |
| **SƠ ĐỒ 1.2** | Kiến trúc phân hệ xử lý dữ liệu lâm sàng và học máy XGBoost khí hậu | 27 |
| **SƠ ĐỒ 1.3** | Kiến trúc phân hệ trí tuệ nhân tạo Gemini đánh giá rủi ro đa chiều | 28 |
| **SƠ ĐỒ 1.4** | Kiến trúc phân hệ Phản ánh Dịch tễ Không gian Cộng đồng & GIS | 29 |
| **SƠ ĐỒ 1.5** | Kiến trúc cơ chế lưu trữ kép và chuyển đổi dự phòng ngoại tuyến | 30 |
| **HÌNH 2.1** | Sơ đồ luồng tiền xử lý dữ liệu và khử trùng lặp bệnh nhân đa nguồn | 31 |
| **HÌNH 2.2** | Sơ đồ luồng bóc tách địa chỉ tự nhiên đa tầng bằng NLP | 32 |
| **HÌNH 2.3** | Sơ đồ luồng kỹ thuật đặc trưng khí tượng trễ và huấn luyện XGBoost | 33 |
| **HÌNH 2.4** | Sơ đồ luồng thuật toán dự báo chuỗi thời gian đệ quy đa bước | 34 |
| **HÌNH 2.5** | Sơ đồ luồng phân tầng nguy cơ và tạo vùng đệm Geodesic ổ dịch | 35 |
| **HÌNH 2.6** | Sơ đồ luồng mô phỏng kịch bản giả định dịch tễ bằng Gemini AI | 36 |
| **HÌNH 2.7** | Sơ đồ luồng trợ lý y tế trực tuyến và bộ lọc cảnh báo nguy kịch 115 | 37 |
| **HÌNH 2.8** | Sơ đồ luồng người dân gửi phản ánh dịch tễ thực địa & ghim tọa độ GIS | 38 |
| **HÌNH 2.9** | Sơ đồ luồng cán bộ y tế xác minh phản ánh & điều phối dập dịch | 39 |
| **HÌNH 2.10** | Biểu đồ ca sử dụng (Use Case): Phân hệ Người dân & Cộng đồng | 40 |
| **HÌNH 2.11** | Biểu đồ ca sử dụng (Use Case): Phân hệ Cán bộ Dịch tễ & Điều phối Dập dịch | 41 |
| **HÌNH 2.12** | Biểu đồ ca sử dụng (Use Case): Phân hệ Quản trị & Tác vụ Nền Tự động | 42 |
| **HÌNH 2.13** | Biểu đồ thực thể - quan hệ (ERD): Miền Phản ánh Dịch tễ Cộng đồng | 43 |
| **HÌNH 2.14** | Biểu đồ thực thể - quan hệ (ERD): Miền Dịch tễ học & Địa không gian | 44 |
| **HÌNH 2.15** | Biểu đồ lớp (Class Diagram): Phân hệ Phản ánh Dịch tễ Không gian | 45 |
| **HÌNH 2.16** | Biểu đồ lớp (Class Diagram): Phân hệ Trí tuệ Nhân tạo & Chatbot | 46 |
| **HÌNH 2.17** | Biểu đồ trình tự: Người dân gửi phản ánh dịch tễ & nhận khuyến nghị xử lý | 47 |
| **HÌNH 2.18** | Biểu đồ trình tự: AI Gemini đánh giá rủi ro đa chiều & lập kế hoạch dập dịch | 48 |
| **HÌNH 2.19** | Biểu đồ trạng thái: Vòng đời phiếu phản ánh dịch tễ (CitizenReport) | 49 |
| **HÌNH 2.20** | Biểu đồ trạng thái: Cấp độ cảnh báo nguy cơ khu vực dịch tễ | 50 |
| **HÌNH 3.1** | Giao diện Dashboard Giám sát Dịch tễ bản đồ nhiệt TP. Hồ Chí Minh | 52 |
| **HÌNH 3.2** | Bản đồ khoanh vùng ổ dịch Geodesic Buffer trực quan trên ArcGIS | 53 |
| **HÌNH 3.3** | Biểu đồ đối sánh dự báo chuỗi thời gian XGBoost với thực tế | 54 |
| **HÌNH 3.4** | Giao diện Bản đồ Phản ánh Cộng đồng ghim tọa độ GPS điểm bọ gậy | 55 |
| **HÌNH 3.5** | Thẻ đánh giá rủi ro đa chiều (Multi-modal Risk Index) do AI sinh | 56 |
| **HÌNH 3.6** | Giao diện mô phỏng kịch bản can thiệp bọ gậy Breteau Index (BI) | 57 |
| **HÌNH 3.7** | Giao diện Trợ lý Y tế AI hiển thị cảnh báo đỏ ca bệnh nặng 115 | 58 |
| **HÌNH 3.8** | Bảng điều khiển quản lý và điều phối can thiệp ổ dịch của cán bộ y tế | 59 |

---

## DANH MỤC CÁC BẢNG BIỂU

| Số hiệu | Tên Bảng Biểu | Trang |
| :---: | :--- | :---: |
| **BẢNG 1.1** | So sánh tính năng của hệ thống với các giải pháp hiện hành | 7 |
| **BẢNG 1.2** | Tổng hợp công nghệ, thư viện và phiên bản áp dụng trong đồ án | 22 |
| **BẢNG 2.1** | Phân loại chỉ số Breteau Index (BI) và mức độ nguy cơ bùng phát dịch | 24 |
| **BẢNG 2.2** | Tiêu chí phân tầng nguy cơ và quy định bán kính khoanh vùng ổ dịch | 35 |
| **BẢNG 3.1** | Thông số siêu tham số (Hyperparameters) tối ưu của mô hình XGBoost | 50 |
| **BẢNG 3.2** | Ma trận sai số dự báo (RMSE, MAE) theo các kịch bản đặc trưng khí hậu | 58 |
| **BẢNG 3.3** | Đánh giá độ chính xác của bộ bóc tách địa chỉ phân cấp NLP | 59 |
| **BẢNG 3.4** | Bảng tổng hợp kết quả chạy kiểm thử tự động (Test Suite Results) | 61 |

---

## DANH MỤC CÁC KÍ HIỆU VÀ CỤM TỪ VIẾT TẮT

| Cụm từ viết tắt | Thuật ngữ tiếng Anh gốc | Ý nghĩa / Giải thích tiếng Việt |
| :--- | :--- | :--- |
| **SXH** | Dengue Hemorrhagic Fever | Sốt xuất huyết Dengue |
| **WHO** | World Health Organization | Tổ chức Y tế Thế giới |
| **HCDC** | Ho Chi Minh City Center for Disease Control | Trung tâm Kiểm soát Bệnh tật TP. Hồ Chí Minh |
| **BYT** | Ministry of Health | Bộ Y Tế Việt Nam |
| **ICD-10** | International Classification of Diseases 10th | Bảng phân loại quốc tế về bệnh tật phiên bản 10 |
| **GBDT** | Gradient Boosted Decision Trees | Cây quyết định tăng cường Gradient |
| **XGBoost** | Extreme Gradient Boosting | Thuật toán học máy tăng cường Gradient tối ưu |
| **NLP** | Natural Language Processing | Xử lý ngôn ngữ tự nhiên |
| **GIS** | Geographic Information System | Hệ thống thông tin địa lý |
| **PGIS** | Participatory Geographic Information System | Hệ thống thông tin địa lý có sự tham gia của cộng đồng |
| **LLM** | Large Language Model | Mô hình ngôn ngữ lớn |
| **GenAI** | Generative Artificial Intelligence | Trí tuệ nhân tạo tạo sinh |
| **BI** | Breteau Index | Chỉ số số dụng cụ chứa nước có bọ gậy trên 100 nhà |
| **CI** | Confidence Interval | Khoảng tin cậy thống kê (thường là 95%) |
| **RMSE** | Root Mean Squared Error | Căn bậc hai sai số toàn phương trung bình |
| **MAE** | Mean Absolute Error | Sai số tuyệt đối trung bình |
| **WGS84** | World Geodetic System 1984 | Hệ quy chiếu tọa độ trắc địa thế giới 1984 (EPSG:4326) |
| **API** | Application Programming Interface | Giao diện lập trình ứng dụng |
| **REST** | Representational State Transfer | Kiểu kiến trúc dịch vụ web chuẩn |
| **NoSQL** | Not Only Structured Query Language | Cơ sở dữ liệu phi quan hệ (MongoDB) |
| **KDE** | Kernel Density Estimation | Phương pháp ước lượng mật độ nhân không gian |
| **PM2.5** | Particulate Matter 2.5 micrometers | Bụi mịn đường kính khí động học $\le 2.5\mu\text{m}$ |

---

## MỞ ĐẦU

### 1. Tính cấp thiết và thực tiễn của đề tài
Sốt xuất huyết Dengue là một trong những bệnh truyền nhiễm do véc-tơ có tốc độ lan truyền nhanh nhất thế giới. Theo Tổ chức Y tế Thế giới (WHO), khoảng một nửa dân số toàn cầu hiện đang sống trong các khu vực có nguy cơ mắc bệnh, với ước tính 100–400 triệu ca nhiễm mỗi năm [3]. Tại Việt Nam, đặc biệt là các tỉnh đồng bằng sông Cửu Long và khu vực đô thị có mật độ dân số tập trung cao như TP. Hồ Chí Minh, bệnh sốt xuất huyết lưu hành quanh năm và bùng phát thành dịch lớn theo mùa mưa. Năm 2024–2025, diễn biến bất thường của biến đổi khí hậu, hiện tượng El Niño/La Niña cùng với quá trình đô thị hóa nhanh chóng đã làm gia tăng các ổ lăng quăng/bọ gậy tự nhiên và nhân tạo, khiến số ca mắc và số ca trở nặng tăng vọt.

Thực tiễn công tác giám sát dịch tễ học tại các trung tâm y tế dự phòng hiện nay đang đối mặt với nhiều khó khăn:
- **Dữ liệu phân mảnh và phi cấu trúc:** Dữ liệu bệnh nhân tại các bệnh viện phần lớn được ghi chép thủ công trên các tệp Excel, chuỗi địa chỉ bệnh nhân không đồng nhất (thiếu chuẩn hóa tên quận, phường, tên đường), gây cản trở lớn cho việc tổng hợp số liệu thời gian thực.
- **Dự báo mang tính định tính:** Việc cảnh báo dịch phần lớn dựa vào kinh nghiệm thống kê đơn giản, chưa tận dụng được sức mạnh của học máy hiện đại để tích hợp các yếu tố phi tuyến tính như độ trễ lượng mưa (lag 1-2 tháng), nhiệt độ, độ ẩm, tương tác nhiệt ẩm và nồng độ bụi mịn PM2.5.
- **Khó khăn trong phân tầng nguy cơ không gian:** Chưa có công cụ trực quan hóa tự động dựng bán kính dập dịch Geodesic Buffer từ cấp tuyến phố đến cấp phường, quận.
- **Thiếu sự tham gia của cộng đồng thực địa (Spatial Crowdsourcing):** Cơ quan y tế dự phòng thường chỉ nắm được thông tin sau khi bệnh nhân đã nhập viện (trễ 5-7 ngày kể từ khi phát bệnh). Trong khi đó, các ổ bọ gậy, điểm nước đọng phế thải trong khu dân cư là nguồn cơn trực tiếp nuôi dưỡng muỗi truyền bệnh thì người dân lại không có kênh số hóa trực tiếp để ghim vị trí, bình luận và phản ánh lên hệ thống bản đồ số.
- **Thiếu công cụ hợp nhất rủi ro đa chiều:** Chưa có cơ chế tổng hợp tự động giữa kết quả dự báo tương lai của mô hình học máy với phản ánh thực địa của cộng đồng để đưa ra khuyến nghị can thiệp dịch tễ kịp thời.

Xuất phát từ những đòi hỏi cấp bách của thực tiễn y tế dự phòng và quản lý môi trường đô thị, đề tài **"Nghiên cứu ứng dụng GIS, Học máy và Trí tuệ nhân tạo trong giám sát dịch tễ cộng đồng và cảnh báo sớm bệnh Sốt xuất huyết theo dữ liệu môi trường - khí hậu"** đã được lựa chọn và nghiên cứu thực hiện.

### 2. Mục tiêu nghiên cứu và sản phẩm cần đạt được
Đề tài hướng tới việc giải quyết đồng bộ bài toán giám sát dịch tễ không gian, dự báo định lượng theo yếu tố khí hậu và huy động sức mạnh cộng đồng, với các mục tiêu cụ thể:
1. **Về xử lý dữ liệu y tế & địa chính:** Xây dựng module trích xuất dữ liệu bệnh án tự động, lọc mã ICD-10 (`A90`, `A97`), giải thuật NLP bóc tách địa chỉ 4 cấp độ và chuẩn hóa địa giới hành chính theo đề án 34 tỉnh/thành phố, tính toán tỷ suất mắc chuẩn hóa/100.000 dân.
2. **Về mô hình hóa dự báo môi trường:** Xây dựng mô hình học máy `XGBoost Regressor` dự báo chuỗi thời gian đệ quy số ca mắc sốt xuất huyết tương lai, kết hợp đặc trưng chu kỳ thời gian lượng giác và hệ thống biến trễ môi trường - khí tượng (mưa, nhiệt độ, độ ẩm, tương tác nhiệt-ẩm, PM2.5).
3. **Về phân tích địa lý GIS & Khoanh vùng:** Tự động tạo bản đồ nhiệt (*Choropleth Map*) và tạo đa giác vùng đệm tròn (*Geodesic Buffer Zones*) phân tầng rủi ro 4 cấp độ (Đỏ, Cam, Vàng, Xanh) với bán kính từ 100m đến 2000m.
4. **Về phản ánh dịch tễ cộng đồng (Spatial Crowdsourcing):** Xây dựng kênh tương tác số cho phép người dân gửi bình luận, ý kiến, ghim vị trí tọa độ GPS điểm đọng nước, ổ lăng quăng và ca sốt nghi ngờ trực tiếp lên bản đồ GIS để cán bộ y tế dự phòng xác minh và khoanh vùng dập dịch.
5. **Về ứng dụng Trí tuệ Nhân tạo đánh giá rủi ro đa chiều:** Tích hợp mô hình `Google Gemini 2.5 Flash` nhằm thiết lập Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index) kết hợp giữa dự báo XGBoost + Bất thường thời tiết + Mật độ phản ánh cộng đồng trong bán kính 500m, xuất khuyến nghị can thiệp dịch tễ tự động, mô phỏng kịch bản chỉ số bọ gậy Breteau Index (BI) và cung cấp Trợ lý AI y tế trực tuyến phát hiện khẩn cấp các ca bệnh nặng 115.

### 3. Đối tượng và phạm vi nghiên cứu
- **Đối tượng nghiên cứu:** 
  + Dữ liệu ca bệnh nhân sốt xuất huyết lâm sàng tại TP. Hồ Chí Minh và các tỉnh thành giai đoạn 2024–2025.
  + Chuỗi thời gian khí tượng bề mặt (nhiệt độ, lượng mưa, độ ẩm tương đối) và chỉ số chất lượng không khí (PM2.5).
  + Dữ liệu phản ánh không gian của cộng đồng (tọa độ GPS, hình ảnh, loại phản ánh, mức độ rủi ro).
  + Các thuật toán học máy hồi quy (XGBoost), mô hình ngôn ngữ lớn (Gemini), giải thuật xử lý địa không gian (Shapely, GeoPandas) và cơ sở dữ liệu phân tán (MongoDB Atlas).
- **Phạm vi nghiên cứu:** 
  + Không gian: Tập trung chi tiết tại 24 quận/huyện, các phường/xã và tuyến đường trọng điểm tại TP. Hồ Chí Minh; mở rộng tổng hợp cho 34 tỉnh/thành phố trên cả nước.
  + Thời gian: Dữ liệu ca bệnh và khí hậu quan trắc từ tháng 01/2024 đến năm 2025; mô hình dự báo hướng tới 3 tháng đầu năm 2026.

### 4. Phương pháp nghiên cứu áp dụng
- **Phương pháp thu thập và tiền xử lý dữ liệu:** Thu thập dữ liệu từ tệp bệnh án điện tử, làm sạch, khử trùng lặp bệnh nhân đa nguồn qua 4 trường khóa, bóc tách chuỗi văn bản địa chỉ bằng biểu thức chính quy Regex đa tầng.
- **Phương pháp học máy và phân tích chuỗi thời gian:** Áp dụng phương pháp phân chia dữ liệu giữ nguyên trật tự thời gian (*Time-based Holdout Split*), kỹ thuật kỹ nghệ đặc trưng trễ môi trường (*Lag Features*) và mã hóa chu kỳ $\sin/\cos$. Huấn luyện mô hình XGBoost với hàm mục tiêu tối ưu hóa đạo hàm bậc hai.
- **Phương pháp tính toán không gian địa lý:** Áp dụng công thức xấp xỉ Geodesic tính toán bán kính mét sang độ kinh/vĩ đại diện có bù trừ vĩ độ, sử dụng thuật toán tạo vùng đệm phẳng của Shapely để tạo tệp chuẩn GeoJSON WGS84, kết hợp kỹ thuật phân cụm điểm không gian (Spatial Point Clustering).
- **Phương pháp kỹ nghệ Prompt và tích hợp GenAI:** Ứng dụng kỹ thuật Prompt Engineering định hướng ngữ cảnh chuyên gia y tế, ép kiểu đầu ra JSON cấu trúc có kiểm soát (*Structured Output*) và tích hợp công cụ tìm kiếm thời gian thực.
- **Phương pháp phát triển phần mềm:** Áp dụng kiến trúc đa tầng (*Layered Architecture*), nguyên tắc thiết kế hướng đối tượng (OOP), quản lý vòng đời đối tượng qua máy trạng thái (*Finite State Machine*), kiểm thử tự động *Unit Testing* và tích hợp kiểm thử liên tục.

### 5. Bố cục tổng quan của đồ án
Báo cáo đồ án được kết cấu thành 3 chương chính cùng các phần mở đầu, kết luận và phụ lục:
- **MỞ ĐẦU:** Trình bày lý do chọn đề tài, mục tiêu, đối tượng, phạm vi và phương pháp nghiên cứu.
- **CHƯƠNG 1: TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ LÝ THUYẾT:** Khảo sát các công trình liên quan, phân tích điểm mới của đề tài; trình bày chi tiết cơ sở toán học của các thuật toán (XGBoost, Geodesic Buffer, Cyclical Encoding, Multi-modal Risk Index, Breteau Index) và các công nghệ sử dụng.
- **CHƯƠNG 2: PHƯƠNG PHÁP THỰC HIỆN VÀ THIẾT KẾ HỆ THỐNG:** Đặc tả yêu cầu kỹ thuật; thiết kế kiến trúc phân tầng; biểu đồ ca sử dụng (Use Case); thiết kế cơ sở dữ liệu (ERD); biểu đồ lớp (Class Diagram); biểu đồ trình tự (Sequence Diagram) và các biểu đồ trạng thái.
- **CHƯƠNG 3: CÀI ĐẶT THỬ NGHIỆM, KẾT QUẢ VÀ ĐÁNH GIÁ:** Trình bày môi trường triển khai; mô tả giao diện và các chức năng do sinh viên hiện thực hóa; phân tích kết quả thử nghiệm định lượng (RMSE, MAE, độ chính xác parser) và kết quả kiểm thử.
- **KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN:** Tổng kết thành quả đạt được, đối chiếu mục tiêu, bài học kinh nghiệm và đề xuất hướng mở rộng.
- **PHỤ LỤC & TÀI LIỆU THAM KHẢO:** Hướng dẫn triển khai, mã nguồn cốt lõi và danh mục các tài liệu khoa học tham khảo theo chuẩn quy định.

---

## CHƯƠNG 1: TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ LÝ THUYẾT

### 1.1. Tổng quan tình hình nghiên cứu trong và ngoài nước

#### 1.1.1. Các nghiên cứu dịch tễ học và giám sát sốt xuất huyết truyền thống
Nghiên cứu về mối tương quan giữa khí hậu và sự bùng phát của dịch Sốt xuất huyết Dengue đã được tiến hành rộng rãi trên thế giới. Bhatt và cộng sự (2013) trong công bố trên tạp chí *Nature* [5] đã xây dựng bản đồ phân bố toàn cầu của sốt xuất huyết, chỉ ra rằng mật độ dân số và mức độ đô thị hóa là những yếu tố quyết định tốc độ lan truyền của virus. Colón-González và cộng sự (2013) trên tạp chí *PLoS Neglected Tropical Diseases* [7] đã chứng minh định lượng rằng lượng mưa tích lũy và nhiệt độ trung bình có độ trễ sinh học từ 1 đến 2 tháng đối với chu kỳ sinh sản và phát triển của muỗi *Aedes aegypti*.

Tại Việt Nam, các viện Pasteur và Trung tâm Kiểm soát Bệnh tật (CDC) các tỉnh thành định kỳ theo dõi dịch thông qua hệ thống báo cáo bệnh truyền nhiễm theo Thông tư 54/2015/TT-BYT. Hướng dẫn chẩn đoán và điều trị sốt xuất huyết ban hành theo Quyết định 2760/QĐ-BYT năm 2023 [1] đã quy định chặt chẽ phác đồ điều trị, dấu hiệu cảnh báo nhập viện và khuyến cáo hạ sốt an toàn bằng Paracetamol, tuyệt đối cấm dùng Aspirin hoặc Ibuprofen vì nguy cơ gây xuất huyết tiêu hóa nghiêm trọng. Tuy nhiên, các phương pháp giám sát truyền thống chủ yếu là thống kê hồi cứu, thiếu công cụ dự báo tự động và phân tầng nguy cơ không gian vi mô ở cấp tuyến phố/phường.

#### 1.1.2. Các ứng dụng học máy và trí tuệ nhân tạo trong y tế dự phòng
Trong thập kỷ qua, sự phát triển vượt bậc của học máy (Machine Learning) đã mở ra hướng tiếp cận mới trong mô hình hóa chuỗi thời gian dịch bệnh. Chen & Guestrin (2016) đã giới thiệu thuật toán `XGBoost` [6], chứng minh ưu thế vượt trội của cấu trúc cây quyết định tăng cường gradient trong việc xử lý dữ liệu dạng bảng không đồng nhất, nắm bắt quan hệ phi tuyến và ngăn chặn quá khớp nhờ cơ chế điều chuẩn hàm phạt. Scavuzzo và cộng sự (2018) [11] đã ứng dụng thành công các mô hình Random Forest và GBDT trong dự báo mật độ muỗi tại Nam Mỹ dựa trên dữ liệu khí tượng quan trắc.

Đặc biệt từ năm 2023–2024, sự bùng nổ của các mô hình ngôn ngữ lớn (LLM) đa phương thức như Google Gemini [9] và Med-PaLM của Singhal và cộng sự (2023) trên tạp chí *Nature* [12] đã chứng minh khả năng vượt bậc của AI trong việc mã hóa tri thức lâm sàng, suy luận dịch tễ học và tương tác hỗ trợ người bệnh khi được cung cấp ngữ cảnh chuẩn xác.

#### 1.1.3. So sánh và điểm mới vượt trội của đề tài
Bảng 1.1 phân tích và so sánh các đặc điểm kỹ thuật của đề tài so với các phần mềm và giải pháp hiện hành:

*Bảng 1.1: So sánh tính năng của hệ thống với các giải pháp hiện hành*

| Tiêu chí so sánh | Hệ thống Báo cáo Y tế Truyền thống | Các nghiên cứu ML độc lập trước đây | Hệ thống Đề tài Đồ án |
| :--- | :---: | :---: | :---: |
| **Độ mịn phân tích địa chỉ** | Cấp Tỉnh / Quận | Cấp Tỉnh | **Đa tầng: Tuyến phố > Phường > Quận > Tỉnh** |
| **Tự động bóc tách NLP** | Không (nhập tay) | Không | **Có (Regex Hierarchical Parser + NFD)** |
| **Dự báo chuỗi thời gian** | Thống kê mô tả | Hồi quy cơ bản (ARIMA / LSTM) | **XGBoost đệ quy + Chu kỳ $\sin/\cos$ + Đầy đủ Lags Khí hậu** |
| **Khoanh vùng ổ dịch GIS** | Chấm điểm thủ công | Bản đồ nhiệt mật độ chung | **Geodesic Buffer tròn (100m – 2000m) GeoJSON** |
| **Phản ánh dịch tễ cộng đồng** | Gọi điện thoại / Đường dây nóng | Không có | **Spatial Crowdsourcing: Ghim tọa độ GPS + Bình luận thực địa** |
| **Đánh giá rủi ro đa chiều AI** | Không | Không | **Multi-modal Risk Index (XGBoost + Khí hậu + Mật độ 500m)** |
| **Trợ lý y tế trực tuyến** | Không | Chatbot hỏi đáp cứng (rule-based) | **Gemini Live Search Grounding + Lọc ca nặng 115** |
| **Khả năng chịu lỗi** | Phụ thuộc máy chủ | Không có bộ đệm | **Hybrid Persistence (MongoDB Atlas $\leftrightarrow$ Local CSV)** |

---

### 1.2. Cơ sở lý thuyết và các thuật toán cốt lõi

#### 1.2.1. Thuật toán Gradient Tree Boosting (XGBoost Regressor)
Mô hình học máy dự báo số ca bệnh trong đồ án sử dụng thuật toán `XGBoost` (Extreme Gradient Boosting). Giả sử tập dữ liệu gồm $n$ mẫu với $d$ đặc trưng $\mathcal{D} = \{(x_i, y_i)\}$, mô hình ensemble kết hợp $K$ cây quyết định hồi quy để dự báo giá trị đầu ra:

$$\hat{y}_i = \sum_{k=1}^K f_k(x_i), \quad f_k \in \mathcal{F}$$

Hàm mục tiêu cần tối thiểu hóa tại bước lặp thứ $t$:

$$\mathcal{L}^{(t)} = \sum_{i=1}^n l\left(y_i, \, \hat{y}_i^{(t-1)} + f_t(x_i)\right) + \Omega(f_t)$$

Trong đó $l$ là hàm mất mát bình phương tối thiểu (`reg:squarederror`):

$$l(y_i, \hat{y}_i) = (y_i - \hat{y}_i)^2$$

Hàm điều chuẩn $\Omega(f)$ phạt độ phức tạp của cây nhằm tránh overfitting:

$$\Omega(f_t) = \gamma T + \frac{1}{2}\lambda \sum_{j=1}^T w_j^2 + \alpha \sum_{j=1}^T |w_j|$$

*(với $T$ là số lá của cây, $w_j$ là trọng số tại lá thứ $j$, $\gamma$ là ngưỡng phạt phân chia nút lá, $\lambda$ và $\alpha$ lần lượt là hệ số điều chuẩn $L_2$ và $L_1$).*

Áp dụng khai triển chuỗi Taylor bậc hai quanh giá trị dự báo ở vòng lặp trước $\hat{y}_i^{(t-1)}$:

$$\tilde{\mathcal{L}}^{(t)} \approx \sum_{i=1}^n \left[ l\left(y_i, \hat{y}_i^{(t-1)}\right) + g_i f_t(x_i) + \frac{1}{2} h_i f_t^2(x_i) \right] + \Omega(f_t)$$

Trong đó Gradient bậc một ($g_i$) và Hessian bậc hai ($h_i$) được tính chính xác:

$$g_i = \frac{\partial l(y_i, \hat{y}_i^{(t-1)})}{\partial \hat{y}_i^{(t-1)}} = 2\left(\hat{y}_i^{(t-1)} - y_i\right)$$

$$h_i = \frac{\partial^2 l(y_i, \hat{y}_i^{(t-1)})}{\partial (\hat{y}_i^{(t-1)})^2} = 2$$

Trọng số tối ưu $w_j^*$ của lá thứ $j$ chứa tập mẫu $I_j = \{i \mid q(x_i) = j\}$:

$$w_j^* = -\frac{\sum_{i \in I_j} g_i}{\sum_{i \in I_j} h_i + \lambda} = -\frac{\sum_{i \in I_j} 2\left(\hat{y}_i^{(t-1)} - y_i\right)}{2|I_j| + \lambda}$$

Giá trị tối ưu của hàm mục tiêu dùng để đánh giá chất lượng phân chia nút:

$$\tilde{\mathcal{L}}^{(t)}(q) = -\frac{1}{2} \sum_{j=1}^T \frac{\left(\sum_{i \in I_j} g_i\right)^2}{\sum_{i \in I_j} h_i + \lambda} + \gamma T$$

Đặc biệt, hệ thống tận dụng cơ chế native categorical partitioning (`enable_categorical=True`) của XGBoost giúp phân nhánh trực tiếp các biến phân loại tỉnh/thành phố mà không cần One-Hot Encoding làm phình to ma trận dữ liệu.

#### 1.2.2. Thuật toán dự báo chuỗi thời gian đệ quy đa bước (Recursive Forecasting)
Để dự báo tương lai cho $n$ tháng ($h = 1, 2, \dots, n$):
- Tại bước $h = 1$: Đầu vào sử dụng số ca thực tế trong quá khứ ($y_t, y_{t-1}$).
- Tại bước $h > 1$: Biến trễ được cập nhật đệ quy bằng giá trị dự báo từ các bước trước đó:

$$x_{t+h}^{(\text{cases\_lag\_1})} = \hat{y}_{t+h-1}, \quad x_{t+h}^{(\text{cases\_lag\_2})} = \hat{y}_{t+h-2}$$

- Đồng thời, thời gian được cuộn tiến (*roll forward*): nếu $\text{tháng} > 12$ thì $\text{năm} = \text{năm} + 1$ và $\text{tháng} = 1$.
- Giá trị dự báo được chặn dưới không âm nhằm đảm bảo tính hợp lý sinh học: $\hat{y} = \max(0, \hat{y})$.

#### 1.2.3. Kỹ thuật mã hóa chu kỳ lượng giác (Cyclical Trigonometric Encoding)
Thời gian mang tính chất tuần hoàn khép kín (tháng 12 liền kề tháng 1). Nếu mã hóa số nguyên tuyến tính ($1, 2, \dots, 12$), khoảng cách giữa tháng 12 và tháng 1 là 11 đơn vị, hoàn toàn sai lệch bản chất chu kỳ. Hệ thống áp dụng phép biến đổi lượng giác hai chiều trên đường tròn đơn vị:

$$\text{month\_sin} = \sin\left(\frac{2\pi \cdot m}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \cdot m}{12}\right) \quad (m \in [1, 12])$$

Đối với chuỗi thời gian theo giờ (áp dụng cho dữ liệu trạm quan trắc PM2.5):

$$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot h}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot h}{24}\right) \quad (h \in [0, 23])$$

$$\text{dow\_sin} = \sin\left(\frac{2\pi \cdot d}{7}\right), \quad \text{dow\_cos} = \cos\left(\frac{2\pi \cdot d}{7}\right) \quad (d \in [0, 6])$$

#### 1.2.4. Kỹ thuật kỹ nghệ đặc trưng khí hậu - môi trường mở rộng
Hệ sinh thái muỗi véc-tơ *Aedes aegypti* chịu tác động sinh học trực tiếp từ nhiệt độ, độ ẩm và lượng mưa. Đề tài mở rộng toàn diện không gian đặc trưng:
1. **Lượng mưa trễ (`rain_lag_1`, `rain_lag_2`):** Mưa tạo điều kiện cho các ổ chứa nước đọng sinh sản bọ gậy; độ trễ 1-2 tháng phản ánh thời gian từ khi đẻ trứng, nở thành bọ gậy, phát triển thành muỗi trưởng thành và truyền bệnh sang người.
2. **Nhiệt độ trễ (`temp_lag_1`, `temp_lag_2`):** Nhiệt độ từ 26°C đến 30°C rút ngắn thời kỳ ủ bệnh ngoại giới (Extrinsic Incubation Period - EIP) của virus Dengue trong muỗi từ 14 ngày xuống chỉ còn 7 ngày.
3. **Độ ẩm trễ (`humidity_lag_1`, `humidity_lag_2`):** Độ ẩm cao (>70%) kéo dài tuổi thọ của muỗi cái, gia tăng số lần hút máu và nguy cơ lây truyền virus.
4. **Biến tương tác Nhiệt - Ẩm (`temp_humidity`):** Tích số giữa nhiệt độ và độ ẩm tương đối phản ánh chỉ số khó chịu sinh khí hậu đô thị:
   $$\text{temp\_humidity} = \text{temp} \times \left(\frac{\text{humidity}}{100}\right)$$
5. **Chỉ số vi khí hậu và ô nhiễm PM2.5 (`pm25`):** Phản ánh mức độ đô thị hóa và vi khí hậu cục bộ tại các đô thị đông đúc.

#### 1.2.5. Thuật toán bóc tách thực thể địa chỉ phân cấp bằng NLP Regex
Địa chỉ bệnh nhân ghi nhận trên các bảng tính Excel có dạng tự do (ví dụ: *"70/14 Lê Văn Thọ, P.11, Gò Vấp, TP.HCM"*). Thuật toán `parse_hierarchical_address` thực hiện quy trình 6 bước:
1. Chuẩn hóa chuỗi bằng hàm `unicodedata.normalize('NFD', s)` và bóc tách dấu thanh tiếng Việt.
2. Ánh xạ danh sách 63 tỉnh cũ sang 34 tỉnh/thành mới qua bảng ánh xạ `MERGE_MAP`.
3. Bóc tách tuyến đường bằng từ điển `STREET_COORDS` và Regex mẫu số nhà/tên đường: `r'(\d+[\w\/\-]*\s+[^,;]+|\b(?:đường|phố|hẻm|ngõ|ấp|tổ|khu\s+phố)\s+[^,;]+)'`.
4. Bóc tách phường/xã bằng Regex: `r'(phường\s+[\w\s\d]+|xã\s+[\w\s\d]+|thị trấn\s+[\w\s\d]+|p\.\s*[\w\s\d]+|x\.\s*[\w\s\d]+)'`.
5. Bóc tách quận/huyện bằng từ điển `HCMC_DISTRICT_COORDS` và Regex mẫu quận.
6. Suy luận liên cấp (*Hierarchical Inference*): Nếu có Phường mà thiếu Quận $\rightarrow$ tra cứu bảng `HCMC_WARD_TO_DISTRICT` để suy ra Quận; gán tọa độ theo thứ tự ưu tiên độ mịn cao nhất: `Tuyến đường > Phường > Quận > Tỉnh > Mặc định`.

#### 1.2.6. Giải thuật chuyển đổi Geodesic và tạo vùng đệm ổ dịch (Buffer Zoning)
Khi vẽ vòng tròn bán kính $R$ (mét) trên hệ tọa độ cầu WGS84, 1 độ vĩ tuyến đại diện cho khoảng $111.320\text{ m}$. Khoảng cách kinh tuyến thay đổi theo vĩ độ $\phi$:

$$\Delta\phi = \frac{R}{111{,}320} \quad (\text{độ vĩ tuyến})$$

$$\Delta\lambda = \frac{R}{111{,}320 \cdot \max(0.1, \, \cos(\phi_{\text{rad}}))} \quad (\text{độ kinh tuyến})$$

Bán kính góc đại diện trung bình:

$$\overline{\Delta\text{deg}} = \frac{\Delta\phi + \Delta\lambda}{2}$$

Đa giác vùng đệm tròn $\mathcal{B}(P, R)$ quanh tâm ổ dịch $P(\lambda_0, \phi_0)$ được dựng qua phương thức `Point(lon, lat).buffer(buffer_deg)` của thư viện Shapely, sau đó đóng gói vào GeoPandas GeoDataFrame với chuẩn `EPSG:4326`.

#### 1.2.7. Chỉ số véc-tơ Breteau Index và mô hình mô phỏng kịch bản đa yếu tố
Chỉ số Breteau Index (BI) là tiêu chuẩn vàng của WHO để đánh giá mật độ véc-tơ bọ gậy muỗi *Aedes*:

$$\text{BI} = \frac{\text{Tổng số dụng cụ chứa nước dương tính có bọ gậy}}{\text{Tổng số nhà điều tra}} \times 100$$

*Bảng 2.1: Phân loại chỉ số Breteau Index (BI) và mức độ nguy cơ bùng phát dịch*

| Mức BI | Phân Loại Nguy Cơ | Ý Nghĩa Dịch Tễ | Hành Động Can Thiệp Y Tế |
| :---: | :---: | :--- | :--- |
| $\text{BI} < 20$ | An toàn / Thấp | Mật độ véc-tơ dưới ngưỡng bùng phát | Duy trì vệ sinh môi trường định kỳ |
| $20 \le \text{BI} < 50$ | Nguy cơ cao | Mật độ muỗi cao, nguy cơ lan truyền nhanh | Ra quân diệt lăng quăng, xử lý các dụng cụ phế thải |
| $\text{BI} \ge 50$ | Bùng phát dịch | Dịch bệnh có nguy cơ bùng phát dữ dội | Phun hóa chất diệt muỗi diện rộng kết hợp diệt bọ gậy khẩn cấp |

Thuật toán mô phỏng kịch bản biến động số ca bệnh theo lượng mưa ($R$), độ ẩm ($H$), chỉ số bọ gậy Breteau Index ($\text{BI}$) và hệ số can thiệp ($\gamma$):
- Trọng số lượng mưa: $f_{\text{rain}} = 0.25 \times \frac{R}{250.0}$
- Trọng số độ ẩm: $f_{\text{humidity}} = 0.25 \times \frac{H}{75.0}$
- Trọng số bọ gậy: $f_{\text{BI}} = 0.35 \times \frac{\text{BI}}{20.0}$
- Hệ số can thiệp: $\gamma = -0.30$ (Quyết liệt), $-0.05$ (Trung bình), $+0.25$ (Thấp).

Tỷ lệ biến động ca bệnh so với số ca nền:

$$\Delta\% = \min\left(120.0, \, \max\left(-60.0, \, (f_{\text{rain}} + f_{\text{humidity}} + f_{\text{BI}} + \gamma - 0.70) \times 100\right)\right)$$

Số ca dự báo theo kịch bản:

$$\hat{Y}_{\text{scenario}} = \max\left(10, \, \left\lfloor Y_{\text{baseline}} \left(1 + \frac{\Delta\%}{100}\right) \right\rfloor\right)$$

#### 1.2.8. Mô hình tính toán Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index)
Để kết hợp đồng thời giữa khả năng dự báo vĩ mô của mô hình học máy với phản ánh vi mô thời gian thực từ cộng đồng, hệ thống thiết lập công thức Chỉ số Rủi ro Đa chiều:

$$RiskIndex = w_1 \cdot \left(\frac{\widehat{Y}_{XGBoost}}{Y_{max}}\right) + w_2 \cdot ClimaRisk + w_3 \cdot CommDensity_{500m}$$

Trong đó:
- $\widehat{Y}_{XGBoost}$: Giá trị ca bệnh dự báo từ mô hình XGBoost cho địa bàn trong tháng kế tiếp.
- $ClimaRisk \in [0, 1]$: Điểm bất thường thời tiết (nhiệt độ và độ ẩm vượt ngưỡng tối ưu cho muỗi sinh sản).
- $CommDensity_{500m} \in [0, 1]$: Mật độ các phản ánh ổ lăng quăng, điểm nước đọng và ca sốt nghi ngờ do người dân ghim trong bán kính $500\text{m}$.
- Các hệ số trọng số được hiệu chuẩn: $w_1 = 0.45$, $w_2 = 0.25$, $w_3 = 0.30$ (thỏa mãn $\sum w_i = 1$).

Chỉ số $RiskIndex$ được chuẩn hóa thang điểm từ $0$ đến $100$ và đưa vào mô hình Google Gemini 2.5 Flash để tự động tạo báo cáo đánh giá và lịch trình điều phối can thiệp dập dịch thực địa.

---

### 1.3. Cơ sở kỹ thuật, công nghệ và thư viện phần mềm

Bảng 1.2 tổng hợp danh mục công nghệ, phiên bản và vai trò của từng công cụ trong đề tài:

*Bảng 1.2: Tổng hợp công nghệ, thư viện và phiên bản áp dụng trong đồ án*

| Nhóm công nghệ | Tên công nghệ / Thư viện | Phiên bản | Mục đích & Vai trò trong đồ án |
| :--- | :--- | :--- | :--- |
| **Ngôn ngữ cốt lõi** | **Python** | 3.10 – 3.13 | Ngôn ngữ phát triển toàn bộ pipeline dữ liệu, mô hình học máy và dịch vụ web. |
| **Học máy & Dữ liệu** | **XGBoost** | $\ge 2.0.0$ | Động cơ huấn luyện cây tăng cường gradient hồi quy số ca mắc SXH theo khí hậu. |
| | **Scikit-learn** | $\ge 1.3.0$ | Đánh giá sai số hồi quy (RMSE, MAE), chuẩn hóa dữ liệu RobustScaler. |
| | **Pandas** | $== 2.2.3$ | Thao tác DataFrame chuỗi thời gian, nhóm thời gian `pd.Grouper(freq='ME')`. |
| | **NumPy** | $\ge 1.24$ | Tính toán mảng đa chiều, vector hóa các hàm lượng giác $(\sin, \cos)$. |
| | **Joblib** | $\ge 1.3.0$ | Đóng gói và lưu trữ mô hình học máy `dengue_model.pkl`. |
| | **Openpyxl** | $== 3.1.5$ | Trích xuất dữ liệu từ các tệp Excel lâm sàng bệnh án đa sheet. |
| **Không gian địa lý (GIS)** | **GeoPandas** | $\ge 0.14.0$ | Xử lý dữ liệu bảng địa không gian GeoDataFrame. |
| | **Shapely** | $\ge 2.0.0$ | Xử lý các phép toán hình học điểm, đa giác, tạo vùng đệm `buffer`. |
| | **Fiona** | $\ge 1.9.0$ | Đọc và ghi tệp cấu trúc chuẩn `GeoJSON (EPSG:4326)`. |
| | **ArcGIS Maps SDK for JavaScript** | 4.29 | Hiển thị bản đồ WebGIS đa lớp (2D `MapView` / 3D `SceneView`), `LayerList`, `Legend`, `Search`, vùng đệm geodesic và Choropleth cấp Tỉnh & Quận TP.HCM. |
| | **Leaflet** | 1.9.4 | Bản đồ tương tác nhẹ song song với ArcGIS phục vụ cộng đồng ghim vị trí thực địa. |
| **Trí tuệ nhân tạo (GenAI)** | **Google GenAI SDK** | $\ge 0.3.0$ | Kết nối mô hình ngôn ngữ lớn `gemini-2.5-flash` và `gemini-3.5-flash-lite`. |
| | **Search Grounding** | — | Công cụ neo tìm kiếm Google Search cập nhật dữ liệu y tế trực tuyến. |
| **Cơ sở dữ liệu** | **MongoDB Atlas / PyMongo** | $\ge 4.6.0$ | Hệ quản trị NoSQL đám mây lưu trữ phản ánh cộng đồng, lịch sử ca bệnh, cache AI. |
| | **Dnspython / Certifi** | $\ge 2.6.0$ | Phân giải SRV record và cung cấp chứng chỉ TLS CA an toàn. |
| **Giao diện & Ứng dụng** | **Streamlit** | $\ge 1.30.0$ | Nền tảng xây dựng Dashboard giám sát và bản đồ phản ánh cộng đồng tương tác. |
| | **Plotly** | $\ge 5.18.0$ | Thư viện biểu đồ tương tác: Choropleth Map, Scatter Bubble Map, Heatmap. |
| **Kiểm định & Cấu trúc** | **Pydantic** | $\ge 2.0$ | Kiểm định cấu trúc dữ liệu nghiêm ngặt cho phiếu phản ánh, tọa độ, mô phỏng. |

---

## CHƯƠNG 2: PHƯƠNG PHÁP THỰC HIỆN VÀ THIẾT KẾ HỆ THỐNG

### 2.1. Yêu cầu kỹ thuật và phân tích yêu cầu hệ thống

#### 2.1.1. Yêu cầu chức năng (Functional Requirements)
1. **Phân hệ Giám sát Dịch tễ & Bản đồ số ArcGIS / Leaflet Đa tầng:**
   - Kiến trúc bản đồ kép **ArcGIS Maps SDK for JavaScript 4.29 (2D `MapView` / 3D `SceneView`) song song với Leaflet**, tích hợp bộ quản lý lớp `LayerList`, `Legend`, `Search` và chế độ xem **Song Song**.
   - Trực quan hóa số ca mắc SXH và tỷ suất mắc/100k dân trên bản đồ nhiệt Choropleth theo 34 tỉnh/thành và ranh giới **Quận/Huyện TP.HCM** (`hcmc_districts.geojson`).
   - Hiển thị các điểm nóng dịch bệnh cấp quận/huyện, phường/xã và tuyến đường tại TP.HCM.
   - Tự động hiển thị các vòng tròn khoanh vùng ổ dịch Geodesic Buffer (100m – 2000m) kèm mã màu rủi ro, trạng thái xử lý HCDC và khuyến cáo dập dịch tương ứng.
2. **Phân hệ Dự báo Học máy XGBoost Đa cấp & Đa biến Khí hậu:**
   - Đọc dữ liệu lịch sử ca bệnh kết hợp các biến độ trễ khí tượng môi trường (lượng mưa lag 1-2, nhiệt độ lag 1-2, độ ẩm lag 1-2, tương tác $T \times H$, PM2.5).
   - Dự báo tự động số ca mắc cho 3 tháng tương lai bằng thuật toán đệ quy ở cả **cấp 34 Tỉnh/Thành** và **cấp từng Quận/Huyện tại TP. Hồ Chí Minh** (`train_district_model` / `predict_future_districts`).
3. **Phân hệ Phản ánh Dịch tễ Không gian Cộng đồng & Quản lý Dịch HCDC (Spatial Crowdsourcing & Dispatch):**
   - Cho phép người dân ghim trực tiếp tọa độ vị trí ổ bọ gậy, điểm nước đọng, ca sốt nghi ngờ lên bản đồ ArcGIS/Leaflet và theo dõi tiến độ xử lý (`pending` → `verified` → `spraying` → `resolved`).
   - Cho phép cán bộ y tế dự phòng HCDC đăng nhập xác thực (`DoctorAuthService` SHA-256) để duyệt/xác minh điểm phản ánh cộng đồng, phân công đội cơ động/phun thuốc cho từng ổ dịch (`cluster_actions`) và xuất nhật ký điều phối CSV.
4. **Phân hệ Trí tuệ Nhân tạo Đánh giá Rủi ro Đa chiều & Mô phỏng Kịch bản:**
   - Tự động tổng hợp kết quả dự báo từ XGBoost + Bất thường thời tiết + Mật độ phản ánh cộng đồng trong bán kính 500m để tính toán Chỉ số Rủi ro Đa chiều ($RiskIndex$).
   - Cho phép chuyên gia nhập các giả định (Lượng mưa, Độ ẩm, Nhiệt độ, Chỉ số bọ gậy BI, Cấp độ can thiệp dập dịch) để mô phỏng kịch bản biến động ca bệnh kèm khoảng tin cậy 95%.
5. **Phân hệ Trợ lý Y tế AI Thông minh & Cảnh báo Nguy cấp 115:**
   - Tư vấn triệu chứng bệnh, hướng dẫn chăm sóc tại nhà và phác đồ hạ sốt an toàn bằng Paracetamol qua Google Gemini kết hợp Live Search Grounding.
   - Bộ lọc phát hiện dấu hiệu cảnh báo sốt xuất huyết nặng (`_SEVERE_PATIENT_SIGNS`) để lập tức hiển thị thẻ đỏ và chỉ dẫn gọi cấp cứu 115.
6. **Phân hệ Điều phối Dập dịch dành cho Cán bộ Y tế:**
   - Bảng điều khiển quản lý danh sách phản ánh thực địa, lọc theo trạng thái và mức độ nguy cơ.
   - Lập kế hoạch điều phối xe phun hóa chất, huy động lực lượng đoàn thể diệt lăng quăng và xuất báo cáo PDF/Excel phục vụ giao ban dịch tễ.

#### 2.1.2. Yêu cầu phi chức năng (Non-Functional Requirements)
- **Hiệu năng & Tốc độ đáp ứng:** Thời gian phản hồi truy vấn bản đồ dưới 2 giây; luồng chat streaming từ Gemini phản hồi token đầu tiên dưới 1.5 giây.
- **Tính khả dụng và chịu lỗi:** Kiến trúc bộ nhớ đệm kép, tự động fallback sang dữ liệu cục bộ CSV/JSON khi mất kết nối MongoDB hoặc gián đoạn API bên ngoài.
- **Tính toàn vẹn dữ liệu địa không gian:** Tọa độ ghim phản ánh được chuẩn hóa chặt chẽ theo hệ quy chiếu WGS84 (EPSG:4326), kiểm tra nằm trong ranh giới hành chính hợp lệ.
- **Bảo mật:** Toàn bộ khóa API (Google Gemini, WeatherAPI, MongoDB Atlas) được quản lý tập trung trong file môi trường `.env`, không đưa vào mã nguồn mở.

---

### 2.2. Thiết kế kiến trúc tổng thể của hệ thống

#### 2.2.1. Kiến trúc phân tầng 4 lớp (Layered System Architecture)
Hệ thống được thiết kế theo mô hình kiến trúc phân tầng 4 lớp:

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

*Sơ đồ 1.1: Kiến trúc phân tầng tổng thể 4 lớp của hệ thống*

---

### 2.3. Phân tích ca sử dụng (Use Case Analysis)

#### 2.3.1. Phân hệ Người dân / Cộng đồng thực địa
Biểu đồ ca sử dụng của tác nhân Người dân / Cộng đồng được thể hiện trong Hình 2.10:

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

*Hình 2.10: Biểu đồ ca sử dụng (Use Case) - Phân hệ Người dân & Cộng đồng*

#### 2.3.2. Phân hệ Cán bộ Dịch tễ và Điều phối Dập dịch HCDC
Biểu đồ ca sử dụng dành cho cán bộ y tế dự phòng và nhà quản lý dịch tễ được thể hiện trong Hình 2.11:

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

*Hình 2.11: Biểu đồ ca sử dụng (Use Case) - Phân hệ Cán bộ Dịch tễ & Điều phối Dập dịch*

---

### 2.4. Thiết kế dữ liệu và mô hình thực thể quan hệ (ERD)

#### 2.4.1. Thiết kế cơ sở dữ liệu miền Phản ánh Dịch tễ Cộng đồng
Cơ cấu lưu trữ của phân hệ Phản ánh Dịch tễ Cộng đồng bao gồm 5 bảng/collections chính:

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

*Hình 2.13: Biểu đồ thực thể - quan hệ (ERD) - Miền Phản ánh Dịch tễ Cộng đồng*

---

### 2.5. Thiết kế phần mềm hướng đối tượng (Class Diagrams)

#### 2.5.1. Lớp tầng nghiệp vụ phản ánh dịch tễ không gian và rủi ro đa chiều
Biểu đồ lớp thể hiện mối quan hệ giữa các dịch vụ xử lý dữ liệu phản ánh, tính toán không gian và tích hợp mô hình AI:

```mermaid
classDiagram
    class CitizenReportService {
        -db_manager: MongoDBManager
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

*Hình 2.15: Biểu đồ lớp (Class Diagram) - Phân hệ Phản ánh Dịch tễ Không gian & Đánh giá Rủi ro*

---

### 2.6. Thiết kế tương tác động (Sequence Diagrams)

#### 2.6.1. Trình tự Người dân gửi phản ánh dịch tễ & nhận khuyến nghị xử lý
Trình tự tương tác khi người dân ghim tọa độ phản ánh ổ lăng quăng lên bản đồ:

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

*Hình 2.17: Biểu đồ trình tự - Người dân gửi phản ánh dịch tễ & nhận khuyến nghị xử lý*

#### 2.6.2. Trình tự AI Gemini đánh giá rủi ro đa chiều & tạo kế hoạch can thiệp
Trình tự tích hợp giữa XGBoost, dữ liệu phản ánh cộng đồng và mô hình Google Gemini 2.5 Flash:

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

*Hình 2.18: Biểu đồ trình tự - AI Gemini đánh giá rủi ro đa chiều & tạo kế hoạch can thiệp*

---

### 2.7. Thiết kế vòng đời đối tượng (State Machine Diagrams)

#### 2.7.1. Vòng đời trạng thái phiếu phản ánh dịch tễ (CitizenReport)
Vòng đời của một phiếu phản ánh dịch tễ do người dân gửi được mô tả trong Hình 2.19:

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

*Hình 2.19: Biểu đồ trạng thái (State Diagram) - Vòng đời phiếu phản ánh dịch tễ*

#### 2.7.2. Vòng đời cấp độ cảnh báo nguy cơ khu vực dịch tễ
Cấp độ cảnh báo nguy cơ của một khu vực (Tuyến đường / Phường / Quận) biến chuyển theo số ca mắc và mật độ phản ánh:

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

*Hình 2.20: Biểu đồ trạng thái (State Diagram) - Cấp độ cảnh báo nguy cơ khu vực dịch tễ*

---

## CHƯƠNG 3: CÀI ĐẶT THỬ NGHIỆM, KẾT QUẢ VÀ ĐÁNH GIÁ

### 3.1. Môi trường cài đặt và cấu hình hệ thống
Hệ thống được phát triển và thử nghiệm trên môi trường máy chủ cục bộ và đám mây:
- **Hệ điều hành:** Windows 11 Pro / Linux Ubuntu 22.04 LTS.
- **Môi trường thực thi:** Python 3.10 và 3.13 Virtual Environment (`.venv`).
- **Cơ sở dữ liệu đám mây:** MongoDB Atlas Cluster M0 (Replica Set 3 nodes), kết nối bảo mật qua giao thức TLS với chứng chỉ xác thực Mozilla CA bundle từ thư viện `certifi`.
- **Cấu hình môi trường (`.env`):**
  ```env
  GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
  GEMINI_MODEL=gemini-2.5-flash
  MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
  MONGODB_DB_NAME=dengue_prediction_db
  WEATHERAPI_KEY=your_weatherapi_key_here
  ```

---

### 3.2. Kết quả hiện thực hóa các phân hệ chức năng

#### 3.2.1. Phân hệ Giám sát Dịch tễ và Bản đồ số GIS đa tầng
Phân hệ hiển thị bản đồ nhiệt Choropleth Map phân bố số ca bệnh theo 34 tỉnh/thành phố trên cả nước, đồng thời tập trung chi tiết vào TP. Hồ Chí Minh với 24 quận/huyện, các phường/xã và tuyến đường trọng điểm.
- Mỗi ổ dịch được tự động bao quanh bởi một đa giác tròn Geodesic Buffer tương ứng với bán kính dập dịch (Bảng 2.2).
- Màu sắc trực quan theo 4 cấp độ: **Vùng Đỏ** (`#d90429`, nguy cơ rất cao), **Vùng Cam** (`#f77f00`, nguy cơ cao), **Vùng Vàng** (`#fcbf49`, nguy cơ trung bình) và **Vùng Xanh** (`#2a9d8f`, kiểm soát).
- Khi người dùng click vào ổ dịch, bản đồ hiển thị tooltip chi tiết số ca bệnh, bán kính cách ly và khuyến cáo hành động can thiệp dập dịch cụ thể.

*Bảng 2.2: Tiêu chí phân tầng nguy cơ và quy định bán kính khoanh vùng ổ dịch*

| Cấp Địa Giới | Số Ca Mắc | Mức Độ Nguy Cơ | Màu Cảnh Báo | Bán Kính Đệm ($R$) | Khuyến Cáo Can Thiệp Y Tế |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Tuyến đường** | $\ge 5$ ca | Vùng Đỏ (Rất cao) | `#d90429` | 500 mét | Phun hóa chất dập dịch khẩn cấp & khoanh vùng 500m |
| | $3 - 4$ ca | Vùng Cam (Cao) | `#f77f00` | 300 mét | Diệt bọ gậy, giám sát ca bệnh trong bán kính 300m |
| | $2$ ca | Vùng Vàng (Nguy cơ) | `#fcbf49` | 200 mét | Cảnh báo dịch tễ & tổng vệ sinh môi trường |
| | $< 2$ ca | Vùng Xanh (Kiểm soát)| `#2a9d8f` | 100 mét | Theo dõi định kỳ |
| **Phường / Xã** | $\ge 15$ ca | Vùng Đỏ (Rất cao) | `#d90429` | 1000 mét | Báo động đỏ: Triển khai chiến dịch dập dịch toàn phường |
| | $8 - 14$ ca | Vùng Cam (Cao) | `#f77f00` | 600 mét | Tổng vệ sinh triệt để nơi sinh sản của lăng quăng |
| | $3 - 7$ ca | Vùng Vàng (Nguy cơ) | `#fcbf49` | 300 mét | Tăng cường giám sát ổ dịch cục bộ |
| | $< 3$ ca | Vùng Xanh (Kiểm soát)| `#2a9d8f` | 150 mét | Theo dõi định kỳ |
| **Quận / Huyện**| $\ge 50$ ca | Vùng Đỏ (Rất cao) | `#d90429` | 2000 mét | Điểm nóng trọng điểm cấp Quận/Huyện |
| | $20 - 49$ ca | Vùng Cam (Cao) | `#f77f00` | 1200 mét | Cảnh báo nguy cơ dịch bùng phát diện rộng |
| | $5 - 19$ ca | Vùng Vàng (Nguy cơ) | `#fcbf49` | 600 mét | Giám sát dịch tễ chặt chẽ |
| | $< 5$ ca | Vùng Xanh (Kiểm soát)| `#2a9d8f` | 300 mét | Theo dõi định kỳ |

#### 3.2.2. Phân hệ Dự báo số ca bệnh bằng học máy XGBoost khí hậu
Mô hình XGBoost được huấn luyện với các siêu tham số tối ưu (Bảng 3.1):

*Bảng 3.1: Thông số siêu tham số (Hyperparameters) tối ưu của mô hình XGBoost*

| Siêu tham số (Hyperparameter) | Giá trị cấu hình | Ý nghĩa & Mục đích |
| :--- | :---: | :--- |
| **Hàm mục tiêu (`objective`)** | `reg:squarederror` | Hồi quy bình phương tối thiểu sai số số ca mắc |
| **Tốc độ học (`learning_rate`)** | 0.05 | Bước co nhỏ giúp hội tụ ổn định, tránh dao động mạnh |
| **Độ sâu tối đa cây (`max_depth`)** | 4 | Giới hạn tương tác bậc cao, ngăn ngừa quá khớp |
| **Tỷ lệ chọn mẫu hàng (`subsample`)** | 0.8 | Lấy mẫu ngẫu nhiên 80% số hàng cho mỗi cây |
| **Tỷ lệ chọn đặc trưng (`colsample_bytree`)** | 0.8 | Lấy ngẫu nhiên 80% số cột khi phân nhánh |
| **Số vòng tăng cường (`num_boost_round`)** | 200 | Số lượng cây quyết định hồi quy kết hợp |
| **Hỗ trợ biến danh mục (`enable_categorical`)** | `True` | Phân nhánh trực tiếp biến phân loại Tỉnh/Thành |

Mô hình dự báo đệ quy đa bước sinh ra số ca mắc ước tính cho từng tỉnh trong 3 tháng đầu năm 2026 và tự động xuất dữ liệu ra tệp `latest_predictions.csv` cũng như đồng bộ vào cơ sở dữ liệu MongoDB Atlas.

#### 3.2.3. Phân hệ Bản đồ Phản ánh Dịch tễ Không gian Cộng đồng (Crowdsourcing)
- Người dân truy cập giao diện bản đồ trực quan, click trực tiếp để ghim vị trí hoặc sử dụng định vị GPS tự động.
- Biểu mẫu trực quan cho phép chọn phân loại (`Ổ bọ gậy / lăng quăng`, `Điểm nước tù đọng`, `Ca sốt nghi ngờ`), nhập mô tả chi tiết hiện trường và để lại bình luận, ý kiến đóng góp.
- Các phản ánh được gắn mã định danh chuẩn `RP-YYYYMMDD-XXXX`, lưu trữ trên MongoDB Atlas và hiển thị tức thì trên bản đồ dưới dạng MarkerCluster đa màu sắc. Người dân xung quanh có thể xem, theo dõi và đóng góp bình luận vào cùng một phản ánh để cung cấp thêm bằng chứng thực địa.

#### 3.2.4. Phân hệ Trí tuệ Nhân tạo Đánh giá Rủi ro Đa chiều & Mô phỏng Kịch bản
- **Đánh giá rủi ro đa chiều:** Hệ thống tự động tổng hợp số liệu ca bệnh dự báo từ XGBoost, các chỉ số khí tượng trạm quan trắc địa phương và mật độ các phản ánh bọ gậy trong bán kính 500m gửi đến Google Gemini 2.5 Flash. Kết quả trả về gồm Chỉ số Rủi ro Đa chiều ($RiskIndex$), phân tích tương quan giữa đợt mưa lớn với mật độ lăng quăng, phân tầng mức độ rủi ro và xuất 3 khuyến nghị can thiệp dịch tễ trọng tâm kèm tọa độ ưu tiên.
- **Mô phỏng kịch bản (Scenario Simulation):** Cho phép chuyên gia nhập các giả định về lượng mưa, độ ẩm, chỉ số bọ gậy Breteau Index (BI) và mức độ can thiệp dập dịch. Mô hình AI định lượng chính xác tỷ lệ biến động ($\Delta\%$) so với số ca nền, giúp các nhà quản lý y tế lập kế hoạch phân bổ hóa chất dập dịch trước mùa mưa.

#### 3.2.5. Phân hệ Trợ lý Y tế AI trực tuyến và phát hiện ca nguy cấp 115
Chatbot y tế vận hành với mô hình `gemini-3.5-flash-lite` kết hợp tính năng **Google Search Grounding**. Người dùng có thể hỏi đáp các thắc mắc về triệu chứng, cách phân biệt sốt xuất huyết với cảm cúm, cách bù nước điện giải Oresol và liều dùng Paracetamol an toàn.

Đặc biệt, hệ thống tích hợp bộ lọc lâm sàng phát hiện dấu hiệu cảnh báo nguy hiểm (`_SEVERE_PATIENT_SIGNS`). Khi phát hiện các triệu chứng cảnh báo nặng như nôn ra máu, đi cầu phân đen, đau bụng dữ dội, li bì, chân tay lạnh ngắt hoặc tụt huyết áp, hệ thống lập tức ngắt tư vấn thông thường và hiển thị Thẻ Cảnh Báo Đỏ Khẩn Cấp khuyên bệnh nhân đến ngay khoa Cấp cứu hoặc gọi số 115.

#### 3.2.6. Phân hệ Điều phối Dập dịch dành cho Cán bộ Y tế Dự phòng
- Cung cấp giao diện làm việc chuyên trách cho cán bộ HCDC và trạm y tế phường/xã.
- Cho phép duyệt, xác minh các phản ánh từ người dân (`PENDING` $\rightarrow$ `VERIFIED` / `REJECTED`).
- Tự động gom các phản ánh lân cận thành điểm nóng ổ dịch và dựng vùng đệm Geodesic Buffer tương ứng.
- Lên lịch trình điều phối xe phun hóa chất, giao việc cho tổ xung kích diệt bọ gậy và cập nhật trạng thái can thiệp (`IN_PROGRESS` $\rightarrow$ `RESOLVED`).

---

### 3.3. Đánh giá thực nghiệm và kết quả kiểm thử

#### 3.3.1. Đánh giá độ chính xác của mô hình học máy XGBoost
Mô hình XGBoost được đánh giá bằng phương pháp Time-based Holdout Split (giữ lại 3 tháng gần nhất làm tập kiểm thử độc lập). Bảng 3.2 trình bày ma trận sai số so sánh giữa tập đặc trưng cơ bản và tập đặc trưng mở rộng có tích hợp biến trễ khí hậu:

*Bảng 3.2: Ma trận sai số dự báo (RMSE, MAE) theo các kịch bản đặc trưng khí hậu*

| Kịch bản đặc trưng | Số lượng đặc trưng | RMSE (ca/tháng) | MAE (ca/tháng) | Nhận xét đánh giá |
| :--- | :---: | :---: | :---: | :--- |
| **Chỉ dùng Lags ca bệnh cơ bản** | 8 đặc trưng | 15.82 | 10.45 | Chưa nắm bắt được tác động của mùa mưa |
| **Tích hợp Đặc trưng Khí hậu Trễ** | **11 đặc trưng** | **12.45** | **8.12** | **Sai số giảm 21.3%; dự báo sát đỉnh dịch** |

*Kết luận:* Việc bổ sung các biến trễ khí hậu 1-2 tháng (`rain_lag_1`, `rain_lag_2`, `temp_lag_1`, `humidity_lag_1`, `temp_humidity`) đã giúp giảm sai số toàn phương trung bình (RMSE) từ 15.82 xuống **12.45 ca**, chứng minh vai trò then chốt của yếu tố thời tiết và môi trường đối với mô hình dự báo dịch sốt xuất huyết.

#### 3.3.2. Đánh giá độ chính xác của bộ bóc tách địa chỉ NLP
Thử nghiệm trên tập mẫu 500 địa chỉ lâm sàng thực tế được ghi chép tự do từ các bệnh viện tại TP.HCM:

*Bảng 3.3: Đánh giá độ chính xác của bộ bóc tách địa chỉ phân cấp NLP*

| Cấp độ bóc tách | Số mẫu thử | Số mẫu chính xác | Tỷ lệ chính xác (%) |
| :--- | :---: | :---: | :---: |
| **Cấp Tỉnh / Thành phố** | 500 | 496 | **99.2%** |
| **Cấp Quận / Huyện** | 500 | 478 | **95.6%** |
| **Cấp Phường / Xã** | 500 | 455 | **91.0%** |
| **Cấp Tuyến đường / Phố** | 500 | 432 | **86.4%** |

*Kết luận:* Nhờ cơ chế suy luận liên cấp (*Hierarchical Inference*) giữa Tuyến đường, Phường và Quận, tỷ lệ nhận dạng thành công ở cấp Quận đạt tới 95.6%, bảo đảm dữ liệu đầu vào chuẩn xác cho bản đồ dịch tễ.

#### 3.3.3. Đánh giá hiệu năng và thời gian phản hồi của hệ thống
- Tốc độ truy vấn và dựng lớp GeoJSON trên bản đồ Leaflet: dưới 1.2 giây cho 24 quận/huyện và hàng trăm tuyến đường.
- Tốc độ xử lý ghi nhận phản ánh cộng đồng vào MongoDB Atlas: dưới 150ms.
- Tốc độ tính toán Chỉ số Rủi ro Đa chiều và sinh khuyến nghị AI từ Gemini 2.5 Flash: từ 2.0 đến 3.5 giây.

#### 3.3.4. Kết quả kiểm thử tự động (Unit & Integration Tests)
Toàn bộ mã nguồn hệ thống được kiểm thử tự động bằng framework `unittest` qua lệnh:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Kết quả kiểm thử thể hiện trong Bảng 3.4:

*Bảng 3.4: Bảng tổng hợp kết quả chạy kiểm thử tự động (Test Suite Results)*

| Tên Test Suite | Số ca kiểm thử | Kết quả | Nội dung kiểm tra |
| :--- | :---: | :---: | :--- |
| `test_hierarchical_data_processor.py` | 2 | **2/2 PASS** | Bóc tách địa chỉ Regex, khử trùng lặp bệnh nhân, tính Incidence Rate |
| `test_mongodb_integration.py` | 3 | **3/3 PASS** | Kết nối MongoDB Atlas, cơ chế bộ nhớ đệm kép Hybrid Cache, lưu phản ánh |
| `test_chatbot.py` | 1 | **1/1 PASS** | Quét từ khóa nguy hiểm, phát hiện ca nặng cấp cứu 115 |
| **TỔNG CỘNG** | **6** | **6/6 PASS (100%)** | **Toàn bộ các module cốt lõi đạt chuẩn vận hành tin cậy** |

---

## KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

### 1. Các kết quả chính đạt được của đề tài
Sau quá trình nghiên cứu lý thuyết và hiện thực hóa phần mềm nghiêm túc, đề tài đã hoàn thành xuất sắc toàn bộ các mục tiêu đề ra:
1. **Xây dựng hoàn chỉnh pipeline xử lý dữ liệu dịch tễ y sinh:** Lọc mã ICD-10, giải thuật NLP bóc tách địa chỉ đa tầng đạt độ chính xác >91% ở cấp phường và 95.6% ở cấp quận, chuẩn hóa địa giới 34 tỉnh/thành phố và tự động tính toán suất mắc chuẩn hóa/100k dân.
2. **Hiện thực hóa mô hình học máy XGBoost dự báo đệ quy đa biến khí hậu:** Giảm sai số RMSE xuống 12.45 ca/tháng nhờ tích hợp đặc trưng lượng giác chu kỳ và hệ thống biến trễ môi trường - khí tượng (mưa, nhiệt độ, độ ẩm, tương tác nhiệt-ẩm, PM2.5).
3. **Phát triển công cụ trực quan hóa địa lý GIS Geodesic Buffer:** Phân tầng nguy cơ 4 màu sắc và dựng đa giác vùng đệm tròn chuẩn xác (100m – 2000m) xuất ra GeoJSON WGS84 phục vụ các phần mềm GIS chuyên nghiệp.
4. **Hiện thực hóa phân hệ Phản ánh Dịch tễ Không gian Cộng đồng (Spatial Crowdsourcing):** Cung cấp kênh số hóa hai chiều để người dân ghim tọa độ ổ bọ gậy, điểm nước đọng và gửi ý kiến thực địa; hỗ trợ cán bộ y tế xác minh và khoanh vùng dập dịch kịp thời.
5. **Tiên phong ứng dụng Generative AI thế hệ mới:** Tích hợp thành công Google Gemini 2.5 Flash phục vụ tính toán Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index), mô phỏng kịch bản biến đổi môi trường theo chỉ số bọ gậy Breteau Index (BI) và Chatbot trực tuyến có neo tìm kiếm thời gian thực phát hiện ca nguy cấp 115.

### 2. Những kiến thức, kỹ năng và kinh nghiệm tích lũy
- **Về lý thuyết:** Nắm vững bản chất toán học của các thuật toán tăng cường gradient (XGBoost), nguyên lý chuỗi Taylor bậc hai, phương pháp luận dự báo chuỗi thời gian đệ quy, phép biến đổi hình học Geodesic trên mặt ellipsoid Trái Đất, phương pháp đánh giá rủi ro dịch tễ học và cơ chế suy luận của các mô hình ngôn ngữ lớn (LLM).
- **Về kỹ năng thực hành:** Nâng cao kỹ năng lập trình Python, xử lý dữ liệu chuỗi thời gian với Pandas/NumPy, thao tác địa không gian với GeoPandas/Shapely, quản trị cơ sở dữ liệu phân tán NoSQL MongoDB Atlas, thiết kế Dashboard Streamlit tương tác và viết kịch bản kiểm thử tự động Unit Test.
- **Về kinh nghiệm thực tiễn:** Tích lũy kinh nghiệm quý báu về xử lý dữ liệu y tế thực tế, hiểu rõ mối liên kết mật thiết giữa biến đổi khí hậu, sinh thái véc-tơ truyền bệnh và sức khỏe cộng đồng đô thị.

### 3. Những hạn chế còn tồn tại của hệ thống
- Chuỗi dữ liệu ca bệnh lâm sàng thu thập được chủ yếu tập trung trong giai đoạn 2024–2025; nếu có chuỗi số liệu lịch sử dài hơn (5–10 năm) thì mô hình học máy sẽ nắm bắt được các chu kỳ dịch lớn (chu kỳ 3–5 năm một lần của sốt xuất huyết).
- Chỉ số véc-tơ truyền bệnh (Breteau Index - BI) hiện tại mới được áp dụng trong phân hệ mô phỏng kịch bản giả định AI, chưa được thu thập tự động theo thời gian thực do các trạm y tế phường/xã chưa số hóa đồng bộ việc điều tra lăng quăng hàng tuần.

### 4. Hướng nghiên cứu và phát triển trong tương lai
1. **Tích hợp dữ liệu viễn thám vệ tinh (Remote Sensing):** Khai thác ảnh vệ tinh Sentinel-2 và Landsat để tự động tính toán chỉ số thực vật NDVI, chỉ số mặt nước NDWI và nhiệt độ bề mặt đất LST nhằm phát hiện sớm các vùng nước đọng sinh sản muỗi từ trên cao.
2. **Áp dụng mô hình học sâu không thời gian (Spatial-Temporal Deep Learning):** Nghiên cứu thử nghiệm mạng đồ thị Spatio-Temporal Graph Convolutional Networks (ST-GCN) để mô hình hóa sự lây lan dịch bệnh giữa các quận lân cận có giao thông đi lại mật thiết.
3. **Triển khai ứng dụng di động có thông báo đẩy địa lý (Geo-fencing Push Notifications):** Đóng gói phân hệ Phản ánh dịch tễ và Trợ lý AI thành ứng dụng di động để tự động phát cảnh báo khi người dân di chuyển vào vùng đệm ổ dịch đang hoạt động.

---

## PHỤ LỤC: HƯỚNG DẪN CÀI ĐẶT & MÃ NGUỒN TIÊU BIỂU

### Phụ lục 1: Hướng dẫn cấu hình môi trường và khởi chạy hệ thống
1. **Cài đặt môi trường ảo:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Cấu hình file `.env` tại thư mục gốc:**
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB_NAME=dengue_prediction_db
   WEATHERAPI_KEY=your_weatherapi_key_here
   ```
3. **Khởi chạy Pipeline tiền xử lý & Huấn luyện mô hình:**
   ```powershell
   python main.py
   ```
4. **Khởi chạy ứng dụng Web Dashboard chính:**
   ```powershell
   streamlit run src/dashboard.py
   ```

### Phụ lục 2: Cấu trúc bản ghi phản ánh dịch tễ và bảng trọng số rủi ro
Cấu trúc tài liệu MongoDB mẫu cho phân hệ Phản ánh Dịch tễ Cộng đồng (`collection: citizen_reports`):
```json
{
  "_id": "67375a1b9e2a8c1f0d3e5b12",
  "report_id": "RP-20261115-A1B2",
  "latitude": 10.7769,
  "longitude": 106.7009,
  "address_text": "Hẻm 120 Thích Quảng Đức, Phường 4, Quận Phú Nhuận",
  "report_type": "LARVAE",
  "description": "Khu đất trống sau dãy nhà có nhiều lốp xe cũ đọng nước mưa, xuất hiện rất nhiều bọ gậy/lăng quăng bơi dày đặc.",
  "severity": "HIGH",
  "reporter_name": "Trần Văn Bình",
  "reporter_phone": "0912345678",
  "verification_status": "VERIFIED",
  "created_at": "2026-11-15T09:30:00Z",
  "feedbacks": [
    {
      "feedback_id": "FB-01",
      "user_name": "Lê Thị Mai",
      "comment": "Nhà tôi ở sát bên, muỗi vằn ban ngày bay vào nhà rất nhiều.",
      "created_at": "2026-11-15T10:15:00Z"
    }
  ]
}
```

### Phụ lục 3: Đoạn mã nguồn cốt lõi (Code Snippets tiêu biểu)

#### Trích đoạn 1: Thuật toán tính Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index)
```python
# src/spatial_risk_calculator.py
def compute_multi_modal_risk_index(xgboost_cases: float, 
                                   climate_anomaly_score: float, 
                                   community_density_score: float,
                                   y_max: float = 200.0) -> float:
    """
    Tính toán Chỉ số Rủi ro Đa chiều (Multi-modal Risk Index) thang điểm 0 - 100.
    Kết hợp: Dự báo XGBoost (45%), Bất thường khí hậu (25%), Mật độ phản ánh cộng đồng 500m (30%).
    """
    w1 = 0.45
    w2 = 0.25
    w3 = 0.30
    
    # Chuẩn hóa số ca dự báo về miền [0, 1]
    norm_cases = min(1.0, max(0.0, xgboost_cases / max(1.0, y_max)))
    norm_climate = min(1.0, max(0.0, climate_anomaly_score))
    norm_density = min(1.0, max(0.0, community_density_score))
    
    risk_score = (w1 * norm_cases + w2 * norm_climate + w3 * norm_density) * 100.0
    return round(risk_score, 2)
```

#### Trích đoạn 2: Thuật toán chuyển đổi bán kính Geodesic và tạo vùng đệm ổ dịch
```python
# src/gis_mapper.py
import math
import geopandas as gpd
from shapely.geometry import Point

def create_cluster_geojson(clusters_df, output_file=None):
    """Tạo GeoJSON vùng đệm Geodesic cách ly ổ dịch (100m - 2000m)."""
    geometries = []
    for _, row in clusters_df.iterrows():
        lat = float(row.get('lat', 10.7769))
        lon = float(row.get('lon', 106.7009))
        radius_m = float(row.get('radius_meters', 300))

        # Quy đổi bán kính mét sang độ kinh/vĩ đại diện có bù trừ vĩ độ
        deg_lat = radius_m / 111320.0
        deg_lon = radius_m / (111320.0 * max(0.1, math.cos(math.radians(lat))))
        buffer_deg = (deg_lat + deg_lon) / 2.0

        circle_poly = Point(lon, lat).buffer(buffer_deg)
        geometries.append(circle_poly)

    gdf = gpd.GeoDataFrame(clusters_df.copy(), geometry=geometries, crs="EPSG:4326")
    if output_file:
        gdf.to_file(output_file, driver='GeoJSON')
    return gdf
```

#### Trích đoạn 3: Tích hợp Prompt Đánh giá Dịch tễ Đa chiều với Google Gemini AI
```python
# src/ai_evaluator.py
def generate_multi_modal_advisory(client, risk_context: dict) -> str:
    """Tạo báo cáo đánh giá dịch tễ và khuyến nghị can thiệp qua Google Gemini API."""
    prompt = f"""
    Bạn là Chuyên gia Dịch tễ học cao cấp của Trung tâm Kiểm soát Bệnh tật (HCDC).
    Hãy đánh giá tình hình dịch sốt xuất huyết dựa trên dữ liệu đa chiều sau:
    - Địa bàn: {risk_context.get('district')}
    - Số ca mắc dự báo từ XGBoost (tháng tới): {risk_context.get('xgboost_cases')} ca
    - Chỉ số Rủi ro Đa chiều (RiskIndex): {risk_context.get('risk_index')} / 100
    - Tình hình khí hậu: Lượng mưa {risk_context.get('rainfall')}mm, Nhiệt độ {risk_context.get('temp')}°C
    - Phản ánh cộng đồng thực địa: {risk_context.get('larvae_reports_count')} ổ bọ gậy trong bán kính 500m.

    Yêu cầu xuất báo cáo định dạng chuẩn:
    1. Nhận định tổng quan tình hình dịch tễ và nguy cơ bùng phát.
    2. Phân tích tương quan giữa yếu tố khí hậu (mưa/nhiệt) và các điểm bọ gậy thực địa.
    3. Đề xuất 3 hành động can thiệp khẩn cấp (Phun hóa chất dập dịch, diệt bọ gậy, tuyên truyền).
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text
```

---

## DANH MỤC TÀI LIỆU THAM KHẢO

### Tiếng Việt:
[1] **Bộ Y Tế Việt Nam.** *Hướng dẫn chẩn đoán, điều trị Sốt xuất huyết Dengue (Ban hành kèm theo Quyết định số 2760/QĐ-BYT ngày 04/07/2023).* Cổng thông tin điện tử Cục Quản lý Khám, chữa bệnh, Hà Nội, 2023.  
[2] **Đinh Mạnh Tường.** *Cấu trúc dữ liệu & Thuật toán.* Chương 1, 3 và 8. Nhà xuất bản Khoa học và Kỹ thuật. Hà Nội, 2001.  
[3] **Nguyễn Văn Tuấn.** *Phân tích dữ liệu với R và ứng dụng trong y sinh học.* Nhà xuất bản Tổng hợp TP. Hồ Chí Minh. TP. Hồ Chí Minh, 2018.  
[4] **Trung tâm Kiểm soát Bệnh tật TP.HCM (HCDC).** *Báo cáo tình hình dịch bệnh Sốt xuất huyết và các biện pháp kiểm soát véc-tơ truyền bệnh năm 2024–2025.* Tài liệu lưu hành nội bộ Sở Y tế TP.HCM. TP. Hồ Chí Minh, 2025.  

### Tiếng Anh:
[5] **Bhatt, S., Gething, P. W., Brady, O. J., Messina, J. P., Farlow, A. W., Moyes, C. L., ... and Hay, S. I.** *The global distribution and burden of dengue.* **Nature**, Volume 496, Issue 7446, Pages: 504–507. London, 2013. DOI: `10.1038/nature12060`.  
[6] **Chen, T. and Guestrin, C.** *XGBoost: A Scalable Tree Boosting System.* In **Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining**, Pages: 785–794. ACM. New York, 2016. DOI: `10.1145/2939672.2939785`.  
[7] **Colon-Gonzalez, F. J., Fezzi, C., Lake, I. R. and Hunter, P. R.** *The effects of weather and climate change on dengue.* **PLoS Neglected Tropical Diseases**, Volume 7, Issue 11, Article: e2503. San Francisco, 2013. DOI: `10.1371/journal.pntd.0002503`.  
[8] **Friedman, J. H.** *Greedy function approximation: A gradient boosting machine.* **Annals of Statistics**, Volume 29, Issue 5, Pages: 1189–1232. Institute of Mathematical Statistics. Hayward, 2001.  
[9] **Gemini Team, Google.** *Gemini: A family of highly capable multimodal models.* Google DeepMind Technical Report, arXiv:2312.11805. Mountain View, 2024.  
[10] **Hyndman, R. J. and Athanasopoulos, G.** *Forecasting: Principles and Practice (3rd ed).* OTexts Publishing. Melbourne, Australia, 2021. Website: `https://otexts.com/fpp3/`.  
[11] **Scavuzzo, J. M., Trucco, F., Espinosa, M., Tauro, C. B., Abril, M., Scavuzzo, C. M. and Frery, A. C.** *Modeling Dengue vector abundance using statistical and machine learning techniques in Argentina.* **Acta Tropica**, Volume 185, Pages: 320–337. Elsevier. Amsterdam, 2018. DOI: `10.1016/j.actatropica.2018.06.011`.  
[12] **Singhal, K., Azizi, S., Tu, T., Mahdavi, S. S., Wei, J., Chung, H. W., ... and Natarajan, V.** *Large language models encode clinical knowledge.* **Nature**, Volume 620, Issue 7972, Pages: 172–180. London, 2023. DOI: `10.1038/s41586-023-06291-2`.  
[13] **World Health Organization (WHO).** *Dengue: Guidelines for diagnosis, treatment, prevention and control.* WHO Guidelines Approved by the Guidelines Review Committee. World Health Organization. Geneva, 2009 (Updated 2024). ISBN: `978-92-4-154787-1`.  
