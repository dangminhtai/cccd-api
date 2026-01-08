# guide_step_03.md — Bước 3: Validate đầu vào

## Mục tiêu

Chặn lỗi “ngay từ cửa” để giảm sai dữ liệu và giảm tải cho CSKH/vận hành.

## Việc cần làm

- Kiểm tra request có field `cccd`
- Ép kiểu: `cccd` phải là string
- Kiểm tra chỉ gồm chữ số (`0-9`)
- Kiểm tra độ dài (thường là 12)
- Nếu sai: trả HTTP 400 + message dễ hiểu

## Gợi ý tiêu chí trả lỗi (đơn giản)

- Input thiếu hoặc sai định dạng:
  - `success=false`
  - `is_valid_format=false`
  - `data=null`
  - `message`: giải thích ngắn gọn

## Hoàn thành khi

- [ ] Test case “thiếu `cccd` / không phải số / sai độ dài” đều trả 400 đúng format

## Tự test (Self-check)

Test bằng web local (không cần PowerShell):

1) Chạy server:

```bash
py .\run.py
```

2) Mở trình duyệt:

- `http://127.0.0.1:8000/demo`

3) Test các case sau và xem “OK” là gì:

- [ ] **Thiếu cccd**: xoá trắng ô CCCD rồi bấm **Parse**
  - OK khi thấy: `Status: 400` và JSON có `message: "Thiếu trường cccd."`
- [ ] **Có chữ**: nhập `0123ABC` rồi bấm **Parse**
  - OK khi thấy: `Status: 400`, `success: false`, `is_valid_format: false`
- [ ] **Sai độ dài**: nhập `123` rồi bấm **Parse**
  - OK khi thấy: `Status: 400`, `success: false`, `is_valid_format: false`

---

## Trạng thái

- **DoD**: ✅ Done
- **Đã verify**: ✅ Done (đã test case thiếu `cccd` trả 400 + message)

## Bước tiếp theo

Chuyển sang `guide_step_04.md` (Xử lý CCCD / parse).



