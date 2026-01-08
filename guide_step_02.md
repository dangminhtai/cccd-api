# guide_step_02.md — Bước 2: Thiết kế API & chuẩn response

## Mục tiêu

Chốt “hình dạng” API để tất cả hệ thống gọi đều **nhất quán** và dễ tích hợp.

## Việc cần làm

- Chốt endpoint: `POST /v1/cccd/parse`
- Chốt request body:
  - `cccd` (bắt buộc)
  - `province_version` (tuỳ chọn)
- Chốt response schema (giữ ổn định):
  - `success`
  - `is_valid_format`
  - `data`
  - `message` (nếu cần)
- Chốt format `gender`:
  - Chọn **một chuẩn** và dùng thống nhất (vd: `Nam`/`Nữ`)
- Chốt có trả thêm hay không:
  - `province_code`, `age`, `century`

## Output mong muốn

- [X] `requirement.md` phản ánh đúng request/response cuối cùng
- [X] Mọi ví dụ JSON trong tài liệu thống nhất cùng một format

## Tự test (Self-check)

- [ ] Mở `requirement.md` và xác nhận có đủ:
  - endpoint `POST /v1/cccd/parse`
  - request fields: `cccd`, `province_version`
  - response fields: `success`, `is_valid_format`, `data`, `message`
- [ ] Chọn 1 chuẩn `gender` và đảm bảo toàn bộ doc dùng đúng 1 chuẩn đó
- [ ] (Tuỳ chọn) dùng grep để rà nhanh:

```bash
git grep "/v1/cccd/parse"
```

Nếu đã implement endpoint, có thể test nhanh:

1) Chạy server:

```bash
py .\run.py
```

2) Test input sai (kỳ vọng 400):

```powershell
try {
  Invoke-WebRequest -Method Post -Uri http://127.0.0.1:8000/v1/cccd/parse -ContentType "application/json" -Body "{}" -ErrorAction Stop
} catch {
  $_.Exception.Response.StatusCode.value__
  $_.ErrorDetails.Message
}
```

3) Test input đúng (kỳ vọng 200):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/cccd/parse -ContentType "application/json" -Body "{\"cccd\":\"012345678901\"}"
```

---

## Trạng thái

- **DoD**: ✅ Done
- **Đã verify**: ✅ Done (đã test 400 cho input sai và 200 cho input đúng)

## Bước tiếp theo

Chuyển sang `guide_step_03.md` (Validate đầu vào).



