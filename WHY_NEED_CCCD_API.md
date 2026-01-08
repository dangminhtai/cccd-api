# WHY_NEED_CCCD_API.md

## Tại sao cần một API đọc CCCD?

Nhiều hệ thống chỉ cần “3 thông tin cơ bản” từ CCCD để làm việc trơn tru:

- **Tỉnh/Thành**
- **Giới tính**
- **Năm sinh**

Vấn đề là nếu **không có một API chung**, mỗi nơi sẽ tự xử lý theo cách riêng → phát sinh lỗi, tốn thời gian, tốn chi phí.

---

## Khi chưa có API: người dùng và đội vận hành đang gặp gì?

### Người dùng (khách hàng) gặp khó

- **Phải nhập tay nhiều trường** → dễ bỏ cuộc giữa chừng.
- **Nhập sai tỉnh/giới tính/năm sinh** → hồ sơ không khớp, bị yêu cầu nhập lại, trải nghiệm kém.
- **Mỗi kênh một kiểu**
  - App điền một kiểu, web điền một kiểu, đối tác điền một kiểu → người dùng thấy “rối” và thiếu tin tưởng.

### Vận hành/CSKH gặp khó

- **Tốn thời gian sửa dữ liệu**
  - Sai tỉnh/giới/năm sinh kéo theo: sửa hồ sơ, giải thích với khách, xử lý khiếu nại.
- **Tốn thời gian đối soát**
  - KYC/CRM/BI không đồng nhất → số liệu báo cáo lệch, tranh cãi “đúng sai” giữa các hệ thống.

### Kỹ thuật/IT gặp khó

- **Mỗi hệ thống tự làm một lần**
  - Cùng một logic nhưng bị viết lại nhiều lần → càng nhiều nơi càng dễ lỗi.
- **Khi có thay đổi (đặc biệt là tỉnh/thành sáp nhập/đổi tên)**
  - Phải đi sửa nhiều chỗ, dễ bỏ sót → hệ thống A đúng, hệ thống B sai.

---

## Khi có API: nó giải quyết được gì?

API đóng vai trò như “một điểm tra cứu chuẩn”:

- Nhập **CCCD** → trả về **Tỉnh/Thành + Giới tính + Năm sinh** theo cùng một cách.

### Lợi ích trực tiếp cho người dùng

- **Tự điền nhanh** → ít thao tác hơn → tăng tỷ lệ hoàn tất đăng ký/KYC.
- **Giảm sai sót** → giảm vòng lặp “nhập sai → bị từ chối → nhập lại”.

### Lợi ích cho vận hành/CSKH

- **Giảm chi phí sửa dữ liệu**
  - Ít case sai thông tin → CSKH đỡ phải gọi/nhắn xác minh, đỡ thao tác chỉnh sửa.
- **Dữ liệu đồng nhất**
  - Một CCCD ra một kết quả thống nhất ở mọi hệ thống → báo cáo ít lệch, ít tranh cãi.

### Lợi ích cho kỹ thuật/IT

- **Chỉ cập nhật một nơi**
  - Khi thay đổi quy tắc hoặc cập nhật tên tỉnh/thành, chỉ cần cập nhật API.
- **Tích hợp nhanh**
  - Ứng dụng/đối tác chỉ cần gọi API, không phải tự xây logic riêng.

---

## Vấn đề “tỉnh/thành sáp nhập (64 → 34)”: API giúp “không vỡ dữ liệu”

Thực tế có lúc **tên tỉnh/thành thay đổi** do sáp nhập/đổi tên. Nếu không có API:

- Mỗi hệ thống sẽ cập nhật tên theo lịch khác nhau → **cùng một người nhưng hiển thị tỉnh khác nhau** ở các nơi.
- Báo cáo theo tỉnh có thể bị **lệch số** vì mỗi hệ thống dùng một danh sách/đặt tên khác nhau.

Khi có API:

- **Bảng tên tỉnh/thành được cập nhật tập trung**.
- Các hệ thống khác chỉ “dùng kết quả từ API”, không phải tự cập nhật danh sách tỉnh/thành ở từng nơi.

---

## API trả về những gì? (đơn giản)

Input:

- `cccd`: chuỗi số CCCD

Output:

- `province_name`: Tỉnh/Thành
- `gender`: Giới tính
- `birth_year`: Năm sinh

> Có thể bổ sung thêm vài thông tin phụ để minh bạch hơn (nếu cần), nhưng phần cốt lõi vẫn là 3 trường trên.

---

## Tiết kiệm chi phí cụ thể ở đâu?

- **Tiết kiệm chi phí vận hành**
  - Giảm số lần CSKH phải hỗ trợ/sửa hồ sơ do sai thông tin cơ bản.
- **Tiết kiệm chi phí kỹ thuật**
  - Không phải duy trì “nhiều phiên bản xử lý CCCD” ở nhiều hệ thống.
  - Khi có thay đổi tỉnh/thành, chỉ cần sửa một chỗ (API) thay vì sửa nhiều chỗ.
- **Tăng doanh thu gián tiếp**
  - Ít bước hơn, ít lỗi hơn → tỷ lệ hoàn tất quy trình cao hơn.


---

## Ví dụ minh hoạ (dữ liệu giả, không dùng CCCD thật)

Input:

- `cccd`: `012345678901`

Output (minh hoạ):

- `province_name`: `TP. X`
- `gender`: `male`
- `birth_year`: `2001`

  ```
  json
{
  "success": true,
  "data": {
    "province_code": "079",
    "province_name": "Thành phố Hồ Chí Minh",
    "gender": "Nam",
    "birth_year": 1996,
    "century": "20",
    "age": 29
  },
  "is_valid_format": true
}

```

---

## Lưu ý an toàn dữ liệu (nói ngắn gọn)

- **Không log CCCD đầy đủ**; chỉ log dạng che (mask) nếu cần theo dõi lỗi.
- **Giới hạn truy cập và tần suất gọi** để tránh bị lạm dụng.


