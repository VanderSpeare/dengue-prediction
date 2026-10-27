# Hệ Thống Đặt Lịch Khám & Cổng Dành Riêng Cho Bác Sĩ

Ứng dụng web đặt lịch khám bệnh trực tuyến và Cổng làm việc độc quyền của Bác sĩ:
- **Xác thực Bác sĩ**: 4 tài khoản Bác sĩ được cấu hình sẵn với **mật khẩu mã hóa SHA-256** (chỉ Đăng nhập, không Đăng ký).
- **Trang Bác Sĩ Độc Quyền**: Gọi khám bệnh nhân, cập nhật tiến độ (`WAITING` -> `IN_PROGRESS` -> `COMPLETED` / `NO_SHOW`), ghi chú hồ sơ bệnh án lâm sàng & chẩn đoán, khóa/mở ca khám.
- **Lưu trữ MongoDB Atlas**: Toàn bộ dữ liệu đặt lịch, tài khoản bác sĩ, hồ sơ bệnh án và thời gian biểu được lưu trữ bền vững.

---

## 👨‍⚕️ 4 Tài Khoản Bác Sĩ Mặc Định (Mã Hóa SHA-256)

> **Mật khẩu chung:** `Bacsi@123` (Được băm SHA-256 lưu trữ an toàn trong MongoDB `doctors`)

| STT | Username | Họ và Tên | Chuyên Khoa | Phòng Khám | Mật Khẩu Mẫu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `bs_nguyenvana` | **BS. CKI Nguyễn Văn A** | Bệnh Truyền Nhiễm & Sốt Xuất Huyết | Phòng 302, Tầng 3 | `Bacsi@123` |
| **2** | `bs_tranthib` | **BS. CKII Trần Thị B** | Truyền Nhiễm & Dịch Tễ Học Lâm Sàng | Phòng 304, Tầng 3 | `Bacsi@123` |
| **3** | `bs_lehoangc` | **ThS. BS Lê Hoàng C** | Hồi Sức Cấp Cứu Nhi & SXH Nặng | Phòng 306, Tầng 3 | `Bacsi@123` |
| **4** | `bs_phamminhd` | **BS. CKI Phạm Minh D** | Nội Tổng Quát & Chẩn Đoán Sớm | Phòng 308, Tầng 3 | `Bacsi@123` |

*Giao diện đăng nhập có sẵn bảng danh sách tài khoản kèm nút **"Chọn nhanh"** để người dùng đăng nhập ngay lập tức chỉ với 1 click.*

---

## 🩺 Các Chức Năng Độc Quyền Dành Cho Bác Sĩ

1. **Quản lý Hàng Đợi & Gọi Khám Bệnh Nhân**:
   - Theo dõi danh sách bệnh nhân theo STT thời gian thực trong ngày.
   - Nút **"Khám"**: Chuyển trạng thái sang `IN_PROGRESS` (Đang khám).
   - Nút **"Báo Vắng Mặt"**: Chuyển sang `NO_SHOW` khi bệnh nhân không có mặt.
2. **Ghi Bệnh Án & Chẩn Đoán Lâm Sàng**:
   - Nhập chẩn đoán chuyên môn (ví dụ: *Theo dõi Sốt xuất huyết Dengue ngày 3*).
   - Chỉ định xét nghiệm cận lâm sàng (*Test nhanh NS1Ag, Công thức máu CBC...*).
   - Kê đơn thuốc & lời dặn điều trị (*Paracetamol, bù điện giải Oresol...*).
   - Bấm **"Lưu Bệnh Án & Hoàn Thành Ca"** -> Tự động cập nhật `COMPLETED` và lưu vào MongoDB.
3. **Chủ Động Khóa / Mở Ca Khám**:
   - Bác sĩ có thể bấm **"Khóa ca"** (chuyển sang `BLOCKED_BY_DOCTOR`) khi bận họp hoặc trực cấp cứu đột xuất.

---

## 🚀 Hướng Dẫn Khởi Chạy

```powershell
cd d:\ProJect\dengue-prediction\dengue-prediction\booking_demo
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Truy cập: **`http://127.0.0.1:8000`**

### Chạy Toàn Bộ Kiểm Thử (Unit & Integration Tests)
```powershell
python -m unittest discover -s . -p "test_*.py"
```
*(13/13 test cases đều vượt qua thành công 100%)*
