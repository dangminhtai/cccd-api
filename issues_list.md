# issues_list.md

## 1) Tool `todo_write` bị lỗi khi gọi song song

- **Hiện tượng**: gọi `todo_write` không có tham số → tool error.
- **Nguyên nhân**: mình gọi tool sai schema (thiếu `merge` + `todos`).
- **Cách xử lý**: gọi lại `todo_write` đúng format, chỉ update các todo cần thiết.
- **Cách tránh lần sau**: luôn tạo payload `merge: true/false` và mảng `todos` đầy đủ.

---

## 2) Không tạo được file `.env.example` do bị chặn dotfile

- **Hiện tượng**: tạo `.env.example` bị “blocked by globalignore”.
- **Nguyên nhân**: workspace policy chặn tạo/sửa một số dotfiles.
- **Cách xử lý**: tạo `env.example` (không có dấu chấm) và hướng dẫn copy sang `.env` ở local.
- **Cách tránh lần sau**: nếu thấy dotfile bị chặn, dùng tên thay thế không có dấu chấm (`env.example`, `env.sample`) và cập nhật doc.

---

## 3) Rename hàng loạt `guile_*` → `guide_*` bị lỗi do “nest PowerShell”

- **Hiện tượng**: chạy lệnh `powershell -Command "..."` trong shell PowerShell khiến `$newName` bị mất, báo lỗi kiểu `= is not recognized`, `Missing argument for NewName`.
- **Nguyên nhân**: biến `$...` bị shell ngoài “ăn”/parse sai do gọi PowerShell lồng PowerShell.
- **Cách xử lý**: chạy trực tiếp command trong PowerShell session hiện tại (không bọc thêm `powershell -Command`), sau đó `grep` kiểm tra không còn `guile_step_`.
- **Cách tránh lần sau**: tránh gọi “PowerShell trong PowerShell”; nếu buộc phải bọc, phải escape `$` đúng cách.

---

## 4) Xoá nhầm file khi dọn `step` (đã phục hồi)

- **Hiện tượng**: lúc dọn file sau khi shift số bước, mình xoá nhầm `guile_step_00.md`.
- **Nguyên nhân**: thao tác delete theo batch bị sai target.
- **Cách xử lý**: tạo lại `guile_step_00.md` ngay, rồi verify danh sách file đủ `step00..step10`.
- **Cách tránh lần sau**: luôn `list_dir` trước khi delete và chỉ delete đúng danh sách; ưu tiên delete từng file thay vì batch khi đang rename/shift.

---

## 5) Nội dung `guide_step_01.md` bị dính thêm phần GitHub (đã tách lại)

- **Hiện tượng**: `guide_step_01.md` chứa cả nội dung “Bước 1” và nội dung “Git/GitHub”.
- **Nguyên nhân**: trong quá trình rename/replace, có khả năng bị ghi đè/ghép nhầm nội dung giữa `step00` và `step01`.
- **Cách xử lý**: cắt bỏ phần Git/GitHub khỏi `guide_step_01.md` (phần đó đã nằm đúng ở `guide_step_00.md`).
- **Cách tránh lần sau**: sau các thao tác bulk rename/replace, luôn mở spot-check 1–2 file và grep các tiêu đề để đảm bảo không “dính nội dung”.

---

## 6) Dừng server chạy nền: thử vài cách mới ra cách đúng

- **Hiện tượng**: lệnh stop process ban đầu bị lỗi cú pháp (`-not`/pipeline), và lệnh `cmd for /f` bị lỗi quoting.
- **Nguyên nhân**: copy lệnh dạng one-liner dễ sai cú pháp trong PowerShell/Windows quoting.
- **Cách xử lý**: dùng `Get-CimInstance Win32_Process` lọc `CommandLine` chứa `python run.py` rồi `Stop-Process`.
- **Cách tránh lần sau**: ưu tiên PowerShell thuần, viết rõ nhiều dòng thay vì one-liner phức tạp; verify bằng gọi lại `/health` để chắc đã stop.

---

## 7) PowerShell không hỗ trợ `&&` như bash (lỗi khi chain lệnh git)

- **Hiện tượng**: chạy `git add -A && git commit ... && git push` báo lỗi: `The token '&&' is not a valid statement separator in this version.`
- **Nguyên nhân**: PowerShell (đặc biệt Windows PowerShell 5.1) không dùng `&&` để nối lệnh như bash/zsh.
- **Cách xử lý**:
  - chạy từng lệnh riêng, hoặc
  - dùng `;` để tách lệnh trong PowerShell.
- **Cách tránh lần sau**: khi chạy trên Windows/PowerShell, mặc định dùng `;` hoặc tách từng command (đặc biệt cho các chuỗi git add/commit/push).

---

## 8) Windows PowerShell 5.1 không có `-SkipHttpErrorCheck` (Invoke-WebRequest)

- **Hiện tượng**: chạy lệnh self-test có `Invoke-WebRequest ... -SkipHttpErrorCheck` báo lỗi: `A parameter cannot be found that matches parameter name 'SkipHttpErrorCheck'.`
- **Nguyên nhân**: `-SkipHttpErrorCheck` chỉ có ở PowerShell 7+; Windows PowerShell 5.1 không hỗ trợ.
- **Cách xử lý**: dùng `try/catch` + `-ErrorAction Stop` để bắt HTTP 4xx/5xx và in status/content.
- **Cách tránh lần sau**: khi viết hướng dẫn self-test, mặc định dùng cú pháp tương thích PS 5.1 (hoặc ghi rõ “PowerShell 7+” nếu dùng option mới).

---

## 9) Test API bị lỗi do “PowerShell trong PowerShell” làm hỏng `$`/escape JSON

- **Hiện tượng**: khi chạy `powershell -Command "..."` bên trong PowerShell để test API:
  - biểu thức có `$_...` bị mất `$` → lỗi parse kiểu `Unexpected token '.Exception...'`
  - body JSON bị escape sai → API nhận sai/thiếu field → trả 400 dù tưởng là request đúng
- **Nguyên nhân**: biến `$...` và escape `\"` bị shell ngoài parse sai do gọi PowerShell lồng PowerShell.
- **Cách xử lý**: chạy lệnh test **trực tiếp** trong session PowerShell hiện tại (không bọc `powershell -Command`).
- **Cách tránh lần sau**: tránh lồng PowerShell; nếu bắt buộc phải bọc, cần escape `$`/quotes đúng cách (dễ sai) → ưu tiên không bọc.

---

## 10) `TemplateNotFound` khi đặt `templates/` sai vị trí (Flask app nằm trong package `app/`)

- **Hiện tượng**: mở `/demo` báo `jinja2.exceptions.TemplateNotFound: demo.html`.
- **Nguyên nhân**: Flask được tạo từ module `app` (`Flask(__name__)` trong `app/__init__.py`), nên thư mục template mặc định phải nằm ở **`app/templates/`** (không phải `templates/` ở root).
- **Cách xử lý**: chuyển template sang `app/templates/demo.html`.
- **Cách tránh lần sau**:
  - đặt template trong `app/templates/` khi app nằm trong package `app/`, hoặc
  - nếu muốn template ở root thì phải cấu hình `template_folder` khi tạo Flask app.

---

## 11) Sai mapping mã giới tính/thế kỷ cho digit 8/9 (theo tài liệu CCCD)

- **Hiện tượng**: digit 8/9 bị map sai thế kỷ (dẫn tới `century` và `birth_year` sai).
- **Nguyên nhân**: mình nhầm quy ước; theo tài liệu bạn đưa:
  - 0/1: thế kỷ 20 (1900–1999)
  - 2/3: thế kỷ 21 (2000–2099)
  - 4/5: thế kỷ 22 (2100–2199)
  - 6/7: thế kỷ 23 (2200–2299)
  - 8/9: thế kỷ 24 (2300–2399)
- **Cách xử lý**: cập nhật map 8/9 → century=24 và bổ sung unit test.
- **Cách tránh lần sau**: luôn đối chiếu với bảng quy ước và có test cho tất cả digit 0–9.

---

## 12) Demo page không hiển thị trạng thái "API Key bật/tắt" gây khó test

- **Hiện tượng**: người dùng test bước 6 (Security) mà status luôn 200, không biết tại sao.
- **Nguyên nhân**: mặc định `.env` chưa cấu hình `API_KEY`, nên server không yêu cầu key → luôn 200; nhưng trang `/demo` không nói rõ điều này.
- **Cách xử lý**: hiển thị trạng thái "🔐 API Key đang BẬT" (kèm key cần nhập) hoặc "🔓 API Key đang TẮT" (kèm hướng dẫn bật) ngay trên `/demo`.
- **Cách tránh lần sau**: khi viết demo page cho feature có cấu hình on/off, luôn hiển thị trạng thái hiện tại để người test biết phải làm gì.

---

## 13) Flask-Limiter trả HTML thay vì JSON khi rate limit (429)

- **Hiện tượng**: khi bị rate limit, response trả về `<!doctype html><title>429 Too Many Requests</title>...` thay vì JSON.
- **Nguyên nhân**: Flask-Limiter mặc định dùng template HTML cho error 429.
- **Cách xử lý**: thêm `@app.errorhandler(429)` trong `create_app()` để trả JSON theo chuẩn API.
- **Cách tránh lần sau**: khi dùng extension có error handler mặc định (limiter, auth...), luôn kiểm tra response format và override nếu cần để đảm bảo API trả JSON nhất quán.

---

## 14) Handler `Exception` bắt luôn 404 → trả 500 sai

- **Hiện tượng**: truy cập URL không tồn tại (ví dụ `/demoss`) → trả 500 thay vì 404.
- **Nguyên nhân**: `@app.errorhandler(Exception)` bắt tất cả exception, kể cả `werkzeug.exceptions.NotFound` (404).
- **Cách xử lý**: trong handler, kiểm tra `isinstance(e, HTTPException)` và `return e` để Flask xử lý mặc định.
- **Cách tránh lần sau**: khi viết catch-all exception handler, luôn exclude HTTP exceptions.

---

## 15) JSON response escape tiếng Việt thành `\uXXXX`

- **Hiện tượng**: message tiếng Việt hiển thị `L\u1ed7i h\u1ec7 th\u1ed1ng` thay vì `Lỗi hệ thống`.
- **Nguyên nhân**: Flask mặc định `ensure_ascii=True` trong JSON encoder.
- **Cách xử lý**: set `app.json.ensure_ascii = False` trong `create_app()`.
- **Cách tránh lần sau**: với API có message tiếng Việt, luôn set `ensure_ascii=False` ngay từ đầu.

---

## 16) Input CCCD không giới hạn độ dài ở frontend (security risk)

- **Hiện tượng**: ô nhập CCCD cho phép nhập quá 12 ký tự, tiềm ẩn rủi ro injection/bypass.
- **Nguyên nhân**: thiếu `maxlength` và `pattern` validation ở HTML input.
- **Cách xử lý**: thêm `maxlength="12" pattern="[0-9]{12}" inputmode="numeric"` vào input field.
- **Cách tránh lần sau**: với input có định dạng cố định (CCCD, SĐT, mã OTP...), luôn:
  - Giới hạn `maxlength` ở frontend
  - Thêm `pattern` regex
  - Dùng `inputmode="numeric"` cho mobile
  - Backend vẫn phải validate (defense in depth)


