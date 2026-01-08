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

> Thực hiện được sau khi bạn đã implement endpoint `POST /v1/cccd/parse`.

- [ ] Test thiếu `cccd` (PowerShell):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/cccd/parse -ContentType "application/json" -Body "{}"
```

- [ ] Test `cccd` có chữ:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/cccd/parse -ContentType "application/json" -Body "{\"cccd\":\"0123ABC\"}"
```

- [ ] Kết quả đúng: HTTP 400 và response có `success=false`, `is_valid_format=false`, `data=null`.



