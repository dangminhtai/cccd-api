# rules.md

## Mục tiêu

Tập hợp các **quy tắc thực hành** để hạn chế lỗi lặt vặt khi làm các step tiếp theo (Flask/Python, Windows/PowerShell, docs + code).

---

## 1) Quy tắc Git (bắt buộc)

- **Mỗi step = 1 commit + push**
  - Làm xong step nào thì commit/push step đó ngay.
  - Commit message rõ ràng: `step05: ...`, `fix: ...`, `docs: ...`, `feat: ...`.
- **Không dùng `git status` nếu không cần**
  - Chỉ dùng khi debug staging hoặc khi user yêu cầu.
- **PowerShell không dùng `&&`**
  - Dùng `;` hoặc chạy từng lệnh riêng.

Ví dụ:

```bash
git add -A
git commit -m "stepXX: ..."
git push
```

---

## 2) Quy tắc test (ưu tiên đơn giản)

- **Luôn có web demo để test nhanh**:
  - `GET /demo` (form nhập CCCD, hiển thị Status + JSON)
  - `POST /v1/cccd/parse` là API thật mà demo gọi vào
- **Định nghĩa “OK” rõ ràng**
  - Case đúng (12 số): Status 200 + `success=true` + `is_valid_format=true`
  - Case sai format: Status 400 + `success=false` + `is_valid_format=false`
  - Case “đúng format nhưng không hợp lý”: Status 200 + `is_plausible=false` + `warnings` có mã cảnh báo

---

## 3) Quy tắc PowerShell/Windows (để khỏi lỗi vặt)

- **Tránh “PowerShell trong PowerShell”**
  - Nếu đang ở PowerShell rồi thì chạy thẳng command, không bọc `powershell -Command "..."`.
- **Không phụ thuộc option chỉ có ở PowerShell 7**
  - Ví dụ `Invoke-WebRequest -SkipHttpErrorCheck` không có trên Windows PowerShell 5.1.
  - Nếu cần bắt lỗi HTTP 4xx/5xx → dùng `try/catch` + `-ErrorAction Stop`.

---

## 4) Quy tắc cấu trúc Flask

- App nằm trong package `app/` thì:
  - Template đặt ở **`app/templates/`** (vd: `app/templates/demo.html`)
  - Routes đặt ở `routes/`
  - Logic đặt ở `services/`
- Không để template ở root `templates/` trừ khi cấu hình `template_folder` khi tạo Flask app.

---

## 5) Quy tắc API contract (không phá client)

- Response luôn ổn định schema (không “lúc có lúc không”):
  - `success`, `is_valid_format`, `data`
  - thêm `is_plausible`, `warnings` nếu dùng cảnh báo
- Khi dữ liệu **đúng format nhưng không hợp lý**:
  - không đổi sang 400 (vì format vẫn đúng)
  - dùng `is_plausible=false` + `warnings=[...]`

---

## 6) Quy tắc tài liệu (docs)

- Mỗi `guide_step_xx.md` phải có:
  - **Tự test (Self-check)** (ưu tiên web `/demo`)
  - **Trạng thái** (DoD/Đã verify)
  - **Bước tiếp theo** (link sang step kế)
- Khi phát hiện lỗi/va vấp mới:
  - ghi vào `issues_list.md` (nguyên nhân + cách fix + cách tránh)

---

## 7) Checklist "trước khi push"

- [ ] Chạy test (ít nhất `py -m unittest discover -s tests -p "test_*.py"`)
- [ ] Mở `/demo` và test nhanh 2 case (đúng/sai)
- [ ] Không log dữ liệu nhạy cảm (không log CCCD full)
- [ ] Commit message đúng step + nội dung
- [ ] Push thành công

---

## 8) Checklist "sau khi push"

- [ ] **Kiểm tra có lỗi mới gặp không?**
  - Nếu có lỗi PowerShell/command → ghi vào `issues_list.md`
  - Nếu có lesson learned → ghi vào `lession_learn.md`
- [ ] **Kiểm tra có vấn đề cần document không?**
  - Cách fix mới, workaround, limitation
  - Best practice mới phát hiện
- [ ] **Cập nhật ngay sau khi push**, không để quên


