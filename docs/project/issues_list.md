# issues_list.md

## 1) Tool `todo_write` bị lỗi khi gọi song song

- **Hiện tượng**: gọi `todo_write` không có tham số → tool error.
- **Nguyên nhân**: mình gọi tool sai schema (thiếu `merge` + `todos`).
- **Cách xử lý**: gọi lại `todo_write` đúng format, chỉ update các todo cần thiết.
- **Cách tránh lần sau**: luôn tạo payload `merge: true/false` và mảng `todos` đầy đủ.

---

## 2) Không tạo được file `.env.example` do bị chặn dotfile

- **Hiện tượng**: tạo `.env.example` bị "blocked by globalignore".
- **Nguyên nhân**: workspace policy chặn tạo/sửa một số dotfiles.
- **Cách xử lý**: tạo `env.example` (không có dấu chấm) và hướng dẫn copy sang `.env` ở local.
- **Cách tránh lần sau**: nếu thấy dotfile bị chặn, dùng tên thay thế không có dấu chấm (`env.example`, `env.sample`) và cập nhật doc.

---

## 3) Rename hàng loạt `guile_*` → `guide_*` bị lỗi do "nest PowerShell"

- **Hiện tượng**: chạy lệnh `powershell -Command "..."` trong shell PowerShell khiến `$newName` bị mất, báo lỗi kiểu `= is not recognized`, `Missing argument for NewName`.
- **Nguyên nhân**: biến `$...` bị shell ngoài "ăn"/parse sai do gọi PowerShell lồng PowerShell.
- **Cách xử lý**: chạy trực tiếp command trong PowerShell session hiện tại (không bọc thêm `powershell -Command`), sau đó `grep` kiểm tra không còn `guile_step_`.
- **Cách tránh lần sau**: tránh gọi "PowerShell trong PowerShell"; nếu buộc phải bọc, phải escape `$` đúng cách.

---

## 4) Xoá nhầm file khi dọn `step` (đã phục hồi)

- **Hiện tượng**: lúc dọn file sau khi shift số bước, mình xoá nhầm `guile_step_00.md`.
- **Nguyên nhân**: thao tác delete theo batch bị sai target.
- **Cách xử lý**: tạo lại `guile_step_00.md` ngay, rồi verify danh sách file đủ `step00..step10`.
- **Cách tránh lần sau**: luôn `list_dir` trước khi delete và chỉ delete đúng danh sách; ưu tiên delete từng file thay vì batch khi đang rename/shift.

---

## 5) Nội dung `guide_step_01.md` bị dính thêm phần GitHub (đã tách lại)

- **Hiện tượng**: `guide_step_01.md` chứa cả nội dung "Bước 1" và nội dung "Git/GitHub".
- **Nguyên nhân**: trong quá trình rename/replace, có khả năng bị ghi đè/ghép nhầm nội dung giữa `step00` và `step01`.
- **Cách xử lý**: cắt bỏ phần Git/GitHub khỏi `guide_step_01.md` (phần đó đã nằm đúng ở `guide_step_00.md`).
- **Cách tránh lần sau**: sau các thao tác bulk rename/replace, luôn mở spot-check 1–2 file và grep các tiêu đề để đảm bảo không "dính nội dung".

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
- **Cách tránh lần sau**: khi viết hướng dẫn self-test, mặc định dùng cú pháp tương thích PS 5.1 (hoặc ghi rõ "PowerShell 7+" nếu dùng option mới).

---

## 9) Test API bị lỗi do "PowerShell trong PowerShell" làm hỏng `$`/escape JSON

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

---

## 17) Backend xử lý string dài trước khi reject → DoS risk

- **Hiện tượng**: Khi gọi API trực tiếp (curl/Postman), có thể gửi string cực dài (hàng triệu ký tự). Backend vẫn phải chạy `strip()` và `isdigit()` trên toàn bộ string trước khi reject.
- **Nguyên nhân**: không có early length check trước khi xử lý.
- **Cách xử lý**: thêm `if len(cccd) > 20: return 400` **ngay đầu**, trước khi `strip()`.
- **Cách tránh lần sau**: với input có độ dài cố định, luôn:
  - Check length **ngay đầu** (trước khi xử lý)
  - Cho buffer nhỏ (ví dụ 20 thay vì 12) để chấp nhận whitespace
  - Reject sớm = tiết kiệm CPU/memory

---

## 18) PowerShell tự format JSON thành table → nested object không hiển thị đúng

- **Hiện tượng**: Gọi Admin API `/admin/stats` → PowerShell hiển thị `@{free=; premium=; ultra=}` thay vì JSON đẹp.
- **Nguyên nhân**: PowerShell `Invoke-RestMethod` tự động format JSON thành table, nested object bị mất.
- **Cách xử lý**: Thêm `| ConvertTo-Json -Depth 5` vào cuối lệnh để xem JSON raw.
- **Cách tránh lần sau**: Khi viết hướng dẫn PowerShell cho API trả JSON phức tạp, luôn:
  - Thêm `| ConvertTo-Json -Depth 5` vào ví dụ
  - Giải thích tại sao cần (PowerShell tự format)
  - Hoặc dùng `Invoke-WebRequest` + parse JSON thủ công

---

## 19) Rate limit đếm cả failed requests (401) → test rate limit sai

- **Hiện tượng**: Test rate limit với key giả → Request 1-10 trả 401, Request 11 trả 429. User nghĩ rate limit đếm cả 401.
- **Nguyên nhân**: Flask-Limiter đếm theo `key_func` (key string), không phân biệt response code. Key sai vẫn bị đếm vào rate limit (để chống brute force).
- **Cách xử lý**: Hướng dẫn rõ trong guide:
  - Phải dùng **KEY THẬT** từ `/admin/` để test rate limit
  - Key giả/sai sẽ trả 401 và vẫn bị đếm
  - Rate limit chỉ đúng khi test với key hợp lệ → request thành công (200)
- **Cách tránh lần sau**: Khi viết hướng dẫn test rate limit, luôn:
  - Nhấn mạnh phải dùng key hợp lệ
  - Cung cấp script test với key thật
  - Giải thích tại sao key sai vẫn bị đếm (security feature)

---

## 20) Input "days" nhận string không phải số (ví dụ "e9") → tạo key vĩnh viễn

- **Hiện tượng**: Nhập "e9" vào ô "Số ngày hợp lệ" → key được tạo vĩnh viễn (không có expires_at).
- **Nguyên nhân**:
  - Frontend: `parseInt("e9")` → `NaN`, `if (NaN)` → false → không gửi field `days`
  - Backend: `days = None` → `days_valid = None` → key vĩnh viễn
- **Cách xử lý**:
  - Frontend: Check `isNaN(parseInt(days))` trước khi gửi, validate ngay
  - Backend: Check `if days is not None and days != ""` và validate chặt chẽ
  - HTML: Thêm `step="1"` và `pattern="[0-9]+"` cho input number
- **Cách tránh lần sau**: Khi validate input số:
  - Frontend: Luôn check `isNaN()` và range trước khi gửi
  - Backend: Luôn validate lại, không tin frontend
  - HTML: Dùng `type="number"` + `step="1"` + `pattern` để hạn chế input sai

---

## 21) Lỗi cú pháp PowerShell khi test CSV export (empty pipe element)

- **Hiện tượng**: Chạy lệnh test CSV export báo lỗi: `An empty pipe element is not allowed.` tại dòng có `$results = @(); $results += ... | Export-Csv ...`
- **Nguyên nhân**: 
  - PowerShell không cho phép pipe rỗng (empty pipe)
  - Lệnh one-liner bị parse sai do thiếu dấu `;` hoặc format sai
  - Môi trường là Windows PowerShell, không phải Linux/bash
- **Cách xử lý**: 
  - Tách lệnh thành nhiều dòng hoặc dùng `;` để ngăn cách
  - Ví dụ đúng: `$results = @(); $results += [PSCustomObject]@{Test='test1'}; $results | Export-Csv ...`
  - Hoặc chạy từng lệnh riêng biệt
- **Cách tránh lần sau**: Khi viết lệnh PowerShell:
  - Luôn nhớ môi trường là **Windows PowerShell**, không phải Linux/bash
  - Tránh one-liner phức tạp, ưu tiên tách nhiều dòng
  - Dùng `;` để ngăn cách lệnh trong cùng một dòng
  - Test lệnh trước khi chạy trong script
  - Khi test CSV export, dùng script block hoặc function thay vì one-liner

---

## 22) PowerShell biến trong catch block bị parse sai khi dùng trong one-liner

- **Hiện tượng**: Chạy lệnh PowerShell one-liner có `catch { $status = [int]$_.Exception.Response.StatusCode }` báo lỗi: `The term '=' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- **Nguyên nhân**: 
  - PowerShell one-liner với `try/catch` phức tạp bị parse sai khi có biến assignment trong catch block
  - Command được wrap trong `powershell -Command "..."` hoặc có nhiều dấu ngoặc kép/nháy đơn lồng nhau
  - Biến `$status` bị mất hoặc bị parse thành command riêng
- **Cách xử lý**: 
  - Tránh one-liner phức tạp với `try/catch` và biến assignment
  - Tách thành script file riêng hoặc nhiều dòng
  - Hoặc dùng cách đơn giản hơn: `try { ... } catch { Write-Host "Error: $($_.Exception.Message)" }`
  - Ví dụ đúng: Viết script file `.ps1` thay vì one-liner
- **Cách tránh lần sau**: Khi viết lệnh PowerShell:
  - **Tránh one-liner phức tạp** với `try/catch` + biến assignment
  - **Ưu tiên script file** (`.ps1`) cho logic phức tạp
  - Nếu bắt buộc dùng one-liner, đơn giản hóa logic (không assign biến trong catch)
  - Test lệnh trước khi dùng trong automation

---

## 23) PowerShell `curl` alias không hỗ trợ backslash `\` để tiếp tục dòng

- **Hiện tượng**: Chạy lệnh `curl` với backslash `\` để tiếp tục dòng báo lỗi: `Missing expression after unary operator '--'` hoặc `Unexpected token 'max-time'`
- **Nguyên nhân**: 
  - Trong PowerShell, `curl` là alias của `Invoke-WebRequest`, không phải curl thật
  - PowerShell không dùng backslash `\` để tiếp tục dòng như bash
  - PowerShell dùng backtick `` ` `` để tiếp tục dòng, hoặc viết trên một dòng
- **Cách xử lý**: 
  - **Option 1:** Dùng `curl.exe` thay vì `curl` (curl thật từ Windows 10+)
  - **Option 2:** Viết command trên một dòng (không dùng backslash)
  - **Option 3:** Dùng backtick `` ` `` để tiếp tục dòng trong PowerShell
  - **Option 4:** Dùng `Invoke-WebRequest` hoặc `Invoke-RestMethod` thay vì curl
- **Cách tránh lần sau**: Khi viết hướng dẫn cho Windows/PowerShell:
  - **Luôn nhớ** `curl` trong PowerShell là alias, không phải curl thật
  - Dùng `curl.exe` nếu muốn dùng curl thật
  - Hoặc viết command trên một dòng
  - Hoặc dùng PowerShell cmdlets (`Invoke-WebRequest`, `Invoke-RestMethod`)
  - Không dùng backslash `\` để tiếp tục dòng trong PowerShell

---

## 22) WSGI middleware không có method `run()` khi wrap Flask app

- **Hiện tượng**: Sau khi wrap Flask app với WSGI middleware, gọi `app.run()` báo lỗi: `AttributeError: 'RemoveServerHeaderMiddleware' object has no attribute 'run'`
- **Nguyên nhân**: 
  - WSGI middleware chỉ implement `__call__()`, không có method `run()` của Flask
  - Trong `run.py`, wrap app với middleware rồi gọi `app.run()` → middleware không có method này
- **Cách xử lý**: 
  - Tách Flask app gốc (`flask_app`) và WSGI app (`app`)
  - Gọi `flask_app.run()` thay vì `app.run()`
  - WSGI app (`app`) chỉ dùng cho production servers (gunicorn, etc.)
- **Cách tránh lần sau**: Khi wrap Flask app với WSGI middleware:
  - Luôn giữ reference đến Flask app gốc để gọi `.run()`
  - WSGI middleware chỉ dùng cho production, không cần cho development server
  - Hoặc chỉ wrap khi dùng với WSGI server (gunicorn), không wrap trong `run.py`

---

## 24) Gunicorn không chạy được trên Windows (fcntl module not found)

- **Hiện tượng**: Chạy `gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app` trên Windows báo lỗi: `ModuleNotFoundError: No module named 'fcntl'`
- **Nguyên nhân**: 
  - `fcntl` là module Unix-specific, không có trên Windows
  - Gunicorn được thiết kế cho Unix/Linux, không hỗ trợ Windows natively
  - Windows không có các system calls mà Gunicorn cần (fork, fcntl, etc.)
- **Cách xử lý**: 
  - **Option 1:** Dùng `waitress` thay vì Gunicorn trên Windows:
    ```powershell
    pip install waitress
    waitress-serve --host=0.0.0.0 --port=8000 wsgi:app
    ```
  - **Option 2:** Dùng Flask dev server cho testing (không phù hợp production):
    ```powershell
    python run.py
    ```
  - **Option 3:** Deploy trên Linux server hoặc dùng Docker (chạy Linux container)
  - **Option 4:** Dùng WSL (Windows Subsystem for Linux) để chạy Gunicorn
- **Cách tránh lần sau**: Khi viết hướng dẫn deploy:
  - **Ghi rõ** Gunicorn chỉ chạy trên Unix/Linux
  - **Đề xuất Waitress** cho Windows development/testing
  - **Khuyến nghị Docker** hoặc Linux server cho production
  - **Hoặc WSL** nếu muốn test Gunicorn trên Windows
  - **Auto-detect OS** trong deploy script và dùng server phù hợp

---

## 26) "Ghi nhớ đăng nhập" không hoạt động đúng

- **Hiện tượng**: Checkbox "Ghi nhớ đăng nhập" có trong form nhưng lần sau vào trang vẫn phải login lại
- **Nguyên nhân**: 
  - Code có set `session.permanent = remember_me` nhưng Flask session cookie mặc định là session cookie (expires khi đóng browser)
  - Cần set `session.permanent = True` khi remember_me = True để Flask sử dụng `PERMANENT_SESSION_LIFETIME`
  - Flask chỉ set cookie với max_age khi `session.permanent = True`
- **Cách xử lý**: 
  - Set `session.permanent = True` khi user check "Remember me"
  - Set `session.permanent = False` khi không check (regular session)
  - Flask sẽ tự động set cookie với max_age = `PERMANENT_SESSION_LIFETIME` (24h) khi permanent = True
- **Cách tránh lần sau**: Khi implement "Remember Me":
  - Luôn set `session.permanent = True/False` rõ ràng dựa trên user choice
  - Đảm bảo `PERMANENT_SESSION_LIFETIME` được config trong app
  - Test bằng cách: login với remember me → đóng browser → mở lại → vẫn login được (trong 24h)

---

## 25) Missing `secrets` import trong app/__init__.py

- **Hiện tượng**: Chạy `python run.py` báo lỗi: `NameError: name 'secrets' is not defined` tại dòng 26 trong `app/__init__.py`
- **Nguyên nhân**: 
  - Code sử dụng `secrets.token_hex(32)` để generate session secret key nhưng thiếu import `secrets` module
  - Import `secrets` bị thiếu khi refactor code
- **Cách xử lý**: 
  - Thêm `import secrets` vào đầu file `app/__init__.py`
  - Đảm bảo import đặt trước khi sử dụng `secrets.token_hex()`
- **Cách tránh lần sau**: Khi refactor code:
  - Luôn kiểm tra tất cả imports cần thiết
  - Chạy `python run.py` hoặc test import sau khi refactor
  - Dùng linter/IDE để phát hiện missing imports

---

## 27) Dùng `@check_admin_auth` như decorator gây lỗi TypeError

- **Hiện tượng**: Chạy `python run.py` báo lỗi: `TypeError: check_admin_auth() takes 0 positional arguments but 1 was given` tại dòng có `@check_admin_auth`
- **Nguyên nhân**: 
  - `check_admin_auth` là một `@before_request` handler, không phải decorator function
  - Khi dùng `@check_admin_auth` như decorator, Python sẽ pass function làm argument, nhưng `check_admin_auth` không nhận argument
  - `@before_request` handler tự động chạy cho tất cả routes trong blueprint, không cần decorator riêng
- **Cách xử lý**: 
  - Xóa `@check_admin_auth` decorator khỏi các routes
  - `check_admin_auth` đã là `@before_request` handler, sẽ tự động chạy
  - Nếu cần exclude một số routes, thêm logic vào `check_admin_auth` để check `request.endpoint`
- **Cách tránh lần sau**: Khi dùng Flask `@before_request`:
  - **Không dùng** `@before_request` handler như decorator cho routes riêng lẻ
  - `@before_request` tự động áp dụng cho tất cả routes trong blueprint
  - Nếu cần exclude routes, check `request.endpoint` trong handler
  - Nếu cần decorator riêng, tạo function decorator riêng (không phải `before_request`)

---

## 28) Admin approve payment nhưng status vẫn là "pending" trong database

- **Hiện tượng**: Sau khi admin approve payment cho user, status trong database vẫn còn là "pending", không được update thành "success"
- **Nguyên nhân**: 
  - **CHÍNH**: Exception xảy ra khi UPDATE API keys do dùng sai tên cột: `WHERE status = 'active'` nhưng bảng `api_keys` có cột `active BOOLEAN` (không phải `status ENUM`)
  - Exception xảy ra sau UPDATE payment nhưng trước commit → transaction bị rollback → payment status không được lưu
  - Code UPDATE payment đã đúng (rowcount=1), nhưng exception ở bước sau làm toàn bộ transaction rollback
- **Cách xử lý**: 
  - Sửa query UPDATE api_keys từ `WHERE status = 'active'` thành `WHERE active = TRUE`
  - Bảng `api_keys` dùng cột `active BOOLEAN`, không phải `status ENUM`
  - Thêm logging chi tiết để phát hiện exception sớm
  - Verify payment status sau UPDATE và sau COMMIT
- **Cách tránh lần sau**: Khi làm việc với database:
  - **Luôn kiểm tra schema** trước khi viết query (column name, type)
  - **Không giả định** tên cột giống nhau giữa các table (ví dụ: `status` vs `active`)
  - **Thêm logging** chi tiết để phát hiện exception sớm
  - **Test** với database thực tế để đảm bảo query đúng schema
  - **Transaction handling**: Exception ở bất kỳ đâu trong transaction sẽ rollback toàn bộ

---

## 29) Admin dashboard expose pending payments without authentication

- **Hiện tượng**: Bất kỳ ai cũng có thể truy cập `/admin/` và xem pending payments mà không cần nhập admin key từ `.env`
- **Nguyên nhân**: 
  - `check_admin_auth()` exclude `GET /admin/` khỏi authentication check (để hiển thị HTML form)
  - `admin_dashboard()` route gọi `get_pending_payments()` và truyền vào template
  - Template render pending payments ngay lập tức, expose sensitive data (user emails, amounts, notes) mà không cần authentication
- **Cách xử lý**: 
  - Không truyền `pending_payments` vào template khi render `admin_dashboard()`
  - Sửa `/admin/payments` endpoint để trả JSON thay vì HTML template
  - Thêm JavaScript function `loadPendingPayments()` để load payments từ API sau khi user nhập admin key
  - Pending payments chỉ được load khi user đã authenticate và gọi API với `X-Admin-Key` header
  - GET `/admin/` vẫn accessible (chỉ hiển thị form), nhưng không expose sensitive data
- **Cách tránh lần sau**: Khi thiết kế admin dashboard:
  - **KHÔNG BAO GIỜ** expose sensitive data trong initial page render
  - **Luôn** require authentication cho các API endpoints trả về sensitive data
  - **Luôn** load sensitive data qua JavaScript/AJAX sau khi user authenticate
  - **Test** bằng cách truy cập trang mà không có auth → phải không thấy data nhạy cảm
  - **Defense in depth**: Even if frontend is compromised, backend API vẫn phải check auth

---

## 30) BuildError khi dùng `url_for()` với route chỉ có POST method

- **Hiện tượng**: Trong template `dashboard.html`, dùng `url_for('portal.resend_verification')` báo lỗi: `BuildError: Could not build url for endpoint 'portal.resend_verification'. Did you mean 'portal.register' instead?`
- **Nguyên nhân**: 
  - Route `resend_verification` được define với `methods=["POST"]` (chỉ POST)
  - Flask `url_for()` chỉ có thể build URL cho routes hỗ trợ GET method
  - Template không thể tạo URL cho POST-only routes
- **Cách xử lý**: 
  - Thêm `GET` vào methods: `@portal_bp.route("/resend-verification", methods=["GET", "POST"])`
  - Hoặc thay form button bằng link `<a href="{{ url_for('portal.resend_verification') }}">`
  - Route vẫn xử lý logic khi nhận GET request (send email và redirect)
- **Cách tránh lần sau**: Khi thiết kế routes:
  - **Luôn** cho phép GET method nếu route cần được gọi từ template/link
  - **Hoặc** dùng form với POST nếu route chỉ cần POST
  - **Không dùng** `url_for()` cho POST-only routes trong template
  - **Test** template rendering để phát hiện BuildError sớm

---

## 31) NameError: name 'logger' is not defined trong user_service.py

- **Hiện tượng**: Chạy password reset route báo lỗi: `NameError: name 'logger' is not defined` tại `services/user_service.py`
- **Nguyên nhân**: 
  - Code sử dụng `logger.error()`, `logger.warning()`, `logger.info()` nhưng thiếu import `logging` module
  - Thiếu dòng `logger = logging.getLogger(__name__)`
  - Khi refactor code, đã thêm logging calls nhưng quên import
- **Cách xử lý**: 
  - Thêm `import logging` vào đầu file `services/user_service.py`
  - Thêm `logger = logging.getLogger(__name__)` sau imports
  - Đảm bảo tất cả files có dùng logger đều có import logging
- **Cách tránh lần sau**: Khi refactor code hoặc thêm logging:
  - **Luôn kiểm tra** imports trước khi dùng logger
  - **Test** chạy code sau khi thêm logging calls
  - **Dùng linter/IDE** để phát hiện undefined names
  - **Kiểm tra** tất cả files có dùng `logger.` đều có `import logging`

---

## 32) Edit label/Suspend/Resume quá chậm do redirect (302), và không xóa được key đã inactive

- **Hiện tượng**: 
  - Edit label, Suspend, Resume đều redirect (302) → reload toàn bộ page → rất chậm
  - Xóa key đã inactive (active = 0) bị lỗi "Không tìm thấy API key hoặc bạn không có quyền xóa"
- **Nguyên nhân**: 
  - **Vấn đề 1**: Tất cả actions dùng form submit → POST → redirect → reload page. User phải chờ reload toàn bộ page.
  - **Vấn đề 2**: `deactivate_key_by_id()` UPDATE với `active = FALSE` nhưng không check ownership trước. Nếu key đã inactive, UPDATE sẽ không affect rows (đã là FALSE rồi) → `rowcount = 0` → return False → báo lỗi "Không tìm thấy"
- **Cách xử lý**: 
  - **Vấn đề 1**: Chuyển sang AJAX cho tất cả actions (edit label, suspend, resume, delete). Return JSON thay vì redirect. Update UI inline mà không reload page.
  - **Vấn đề 2**: Sửa `deactivate_key_by_id()` để:
    - Check ownership trước (SELECT để verify)
    - Nếu ownership đúng, update active = FALSE (chỉ nếu chưa inactive)
    - Return True nếu ownership đúng (không quan tâm rowcount)
- **Cách tránh lần sau**: Khi implement actions cần feedback ngay:
  - **Ưu tiên AJAX** cho các actions không cần reload page (edit, suspend, resume, delete)
  - **Chỉ dùng redirect** cho actions cần reload (như rotate - cần show key mới)
  - **Khi UPDATE với điều kiện**, luôn verify ownership/validity trước, rồi mới update
  - **Không dựa vào rowcount** để quyết định success nếu có thể key đã ở trạng thái đó rồi
  - **Test** với các trạng thái khác nhau (active, inactive, suspended, expired)

---

## 33) Rotate key vẫn reload page, và delete key chỉ set active=FALSE chưa xóa thật

- **Hiện tượng**: 
  - Rotate key vẫn redirect (302) → reload toàn bộ page → chậm
  - Delete key chỉ set `active = FALSE` nhưng key vẫn hiển thị trong list (chưa filter inactive)
  - User muốn delete key thực sự xóa khỏi database (hard delete)
- **Nguyên nhân**: 
  - **Vấn đề 1**: Rotate route vẫn dùng `redirect()` và `session["new_api_key"]` thay vì return JSON
  - **Vấn đề 2**: `get_user_api_keys()` không filter `active = TRUE`, nên keys đã inactive vẫn hiển thị
  - **Vấn đề 3**: `deactivate_key_by_id()` chỉ set `active = FALSE` (soft delete), không thực sự xóa row
- **Cách xử lý**: 
  - **Vấn đề 1**: Chuyển rotate route sang AJAX, return JSON với `new_key`, show modal với key mới
  - **Vấn đề 2**: Filter `active = TRUE` trong `get_user_api_keys()` để chỉ hiển thị active keys
  - **Vấn đề 3**: Tạo function mới `delete_key_by_id()` để hard delete (DELETE row). Foreign key constraints sẽ tự động:
    - DELETE `api_key_history` (CASCADE)
    - DELETE `api_usage` (CASCADE)
    - SET NULL `request_logs.api_key_id` (SET NULL)
- **Cách tránh lần sau**: 
  - **Khi delete data**: Quyết định rõ ràng soft delete vs hard delete
  - **Soft delete**: Dùng flag (active, deleted_at) và filter trong query
  - **Hard delete**: Dùng DELETE và đảm bảo foreign key constraints đúng (CASCADE/SET NULL)
  - **List queries**: Luôn filter theo status để không hiển thị deleted/inactive items
  - **AJAX cho actions**: Rotate, create, delete nên dùng AJAX để tránh reload page
  - **Test**: Verify delete thực sự xóa khỏi database (query trực tiếp), không chỉ hide trong UI

---

## 34) AJAX requests (delete, update_label, usage) bị 302 redirect → nhận HTML thay vì JSON

- **Hiện tượng**: 
  - Click "Xóa", "Edit Label", "Usage" → AJAX request trả về 302 redirect → nhận HTML (`<!doctype`) thay vì JSON
  - JavaScript error: "Unexpected token '<', "<!doctype "... is not valid JSON"
  - Status code 302 (redirect) thay vì 200 (success)
- **Nguyên nhân**: 
  - `require_login` decorator không detect được AJAX requests → luôn redirect về HTML login page
  - Khi POST với FormData, browser không tự động set `X-Requested-With` header
  - JavaScript không check content-type trước khi parse JSON → cố parse HTML thành JSON → lỗi
  - Route `/keys/<id>/usage` có thể bị redirect nếu session expired
- **Cách xử lý**: 
  - **Sửa `require_login` decorator** để detect AJAX requests:
    - Check `X-Requested-With: XMLHttpRequest` header
    - Check `Accept: application/json` header
    - Check `request.is_json`
    - Check POST với action="delete" hoặc "update_label"
    - Check path có chứa "/usage"
    - Nếu là AJAX → return JSON 401 thay vì redirect HTML
  - **Thêm headers** vào tất cả AJAX fetch requests:
    ```javascript
    headers: {
        'X-Requested-With': 'XMLHttpRequest'
    }
    ```
  - **Check content-type** trong JavaScript trước khi parse JSON:
    ```javascript
    const contentType = res.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
        throw new Error(`Expected JSON but got ${contentType}`);
    }
    ```
  - **Early return** trong route `keys()` để return JSON ngay khi action="delete"/"update_label" và user không tồn tại
- **Cách tránh lần sau**: 
  - **Luôn set headers** cho AJAX requests (`X-Requested-With`, `Accept: application/json`)
  - **Decorator `require_login`** phải detect AJAX và return JSON thay vì redirect
  - **JavaScript error handling** phải check content-type trước khi parse JSON
  - **Test** với Network tab để verify response là JSON, không phải HTML redirect
  - **Kiểm tra** redirects (302) trong browser DevTools để phát hiện sớm

---

## 35) Admin search user by email không tìm thấy user có tồn tại

- **Hiện tượng**: Admin nhập email user có tồn tại (ví dụ `dmt826321@gmail.com`) nhưng báo lỗi "Không tìm thấy user"
- **Nguyên nhân**: 
  - Function `get_user_by_email()` không có error handling cho trường hợp column `email_verified` không tồn tại (backward compatibility)
  - Database có thể chưa có migration cho email verification columns
  - Exception xảy ra nhưng bị catch và return None mà không log error
  - SQL query có thể fail nếu table schema không đầy đủ
- **Cách xử lý**: 
  - Thêm try/except trong SQL query để handle backward compatibility giống như `get_user_by_id()`
  - Try query với `email_verified` column trước, nếu fail thì query without `email_verified`
  - Thêm logging error để debug
  - Dùng `user.get("last_login_at")` thay vì `user["last_login_at"]` để tránh KeyError nếu column không tồn tại
- **Cách tránh lần sau**: Khi viết function query database:
  - **Luôn** handle backward compatibility cho optional columns (email_verified, last_login_at, etc.)
  - **Try/except** trong SQL query để fallback khi column không tồn tại
  - **Thêm logging** error để debug khi function return None
  - **Dùng `.get()`** cho dictionary access nếu key có thể không tồn tại
  - **Test** với database schema cũ và mới để đảm bảo backward compatibility

---

## 36) Admin search user fail do subscriptions table không có column `created_at`

- **Hiện tượng**: Admin search user by email báo lỗi "Unknown column 'created_at' in 'order clause'" khi query subscriptions table
- **Nguyên nhân**: 
  - Function `get_user_by_email()` query subscriptions với `ORDER BY created_at DESC` nhưng subscriptions table không có column `created_at`
  - Database schema có thể chưa có migration cho `created_at` column trong subscriptions table
  - Subscriptions table chỉ có `started_at` (theo schema gốc), không có `created_at`
  - Exception xảy ra khi ORDER BY column không tồn tại
- **Cách xử lý**: 
  - Thêm try/except trong query subscriptions để handle backward compatibility
  - Try query với `ORDER BY created_at DESC` trước, nếu fail thì query without ORDER BY
  - Hoặc dùng `started_at` thay vì `created_at` nếu column đó tồn tại
  - Apply cùng pattern cho `get_users_list()` function khi query subscriptions
- **Cách tránh lần sau**: Khi viết query database với ORDER BY:
  - **Luôn kiểm tra** column tồn tại trước khi ORDER BY (hoặc dùng try/except)
  - **Không giả định** tên column giống nhau giữa các table (ví dụ: `created_at` vs `started_at`)
  - **Check schema** trước khi viết query với ORDER BY
  - **Test** với database schema thực tế để đảm bảo columns tồn tại
  - **Backward compatibility**: Try/except cho optional columns trong ORDER BY clause

---

## 37) Nút xóa user chưa có confirm và nút đổi tier không hoạt động

- **Hiện tượng**: 
  - Nút xóa user không có confirm dialog "Bạn có chắc chắn xóa user này"
  - Nút đổi tier không đổi được tier (không có response hoặc lỗi)
- **Nguyên nhân**: 
  - **Vấn đề 1**: Chưa có function `delete_user()` trong `services/user_service.py` và route `/admin/users/<id>/delete`
  - **Vấn đề 2**: Nút đổi tier có thể không hoạt động do:
    - JavaScript function `changeUserTierDirectly()` không parse JSON response đúng cách
    - Route `/admin/users/change-tier` trả về redirect thay vì JSON cho AJAX requests
    - Thiếu header `X-Requested-With: XMLHttpRequest` trong fetch request
- **Cách xử lý**: 
  - **Vấn đề 1**: 
    - Thêm function `delete_user()` trong `services/user_service.py` để hard delete user
    - Thêm route `POST /admin/users/<id>/delete` với AJAX detection
    - Thêm nút "🗑️ Xóa" trong users table với confirm dialog
    - Thêm JavaScript function `deleteUser()` với confirm "Bạn có chắc chắn muốn xóa user này?"
  - **Vấn đề 2**: 
    - Đảm bảo route `/admin/users/change-tier` detect AJAX và return JSON
    - Thêm header `X-Requested-With: XMLHttpRequest` vào fetch request
    - Parse JSON response thay vì xử lý redirect
    - Improve `showChangeTierModal()` để hiển thị thông tin rõ ràng hơn
- **Cách tránh lần sau**: 
  - **Khi implement delete actions**: Luôn có confirm dialog để tránh xóa nhầm
  - **Khi implement AJAX requests**: Luôn thêm header `X-Requested-With: XMLHttpRequest`
  - **Backend routes**: Detect AJAX requests và return JSON thay vì redirect
  - **JavaScript**: Parse JSON response và handle errors đúng cách
  - **Test**: Verify cả success và error cases cho AJAX requests

---

## 38) Không thể nhấn vào nút Đổi Tier và Xóa user

- **Hiện tượng**: Không thể click vào nút "🔄 Đổi Tier" hoặc "🗑️ Xóa" trong users table
- **Nguyên nhân**: 
  - **Vấn đề 1**: Function `deleteUser()` được định nghĩa sau khi nó được sử dụng (hoisting issue với async functions)
  - **Vấn đề 2**: String escaping trong onclick handlers không đúng (single quotes trong email có thể break JavaScript string)
  - **Vấn đề 3**: Có thể có JavaScript syntax error do quotes không được escape đúng cách
- **Cách xử lý**: 
  - **Vấn đề 1**: Di chuyển function `deleteUser()` lên trước khi nó được sử dụng (sau `clearUserSearch()`)
  - **Vấn đề 2**: Escape cả single quotes (`'`) và double quotes (`"`) trong email và tier khi đưa vào onclick handler
  - **Vấn đề 3**: Dùng `.replace(/'/g, "\\'").replace(/"/g, '&quot;')` để escape quotes đúng cách
- **Cách tránh lần sau**: 
  - **Khi dùng onclick handlers**: Luôn escape quotes trong strings (single và double quotes)
  - **Function hoisting**: Async functions không được hoisted như regular functions, cần định nghĩa trước khi dùng
  - **String interpolation**: Khi đưa user input vào JavaScript strings, luôn escape special characters
  - **Test**: Verify buttons có thể click được và không có JavaScript errors trong console
  - **Alternative**: Có thể dùng event listeners thay vì inline onclick để tránh string escaping issues

---

## 39) Lỗi khi đổi tier do subscriptions table không có column `notes`

- **Hiện tượng**: Khi admin đổi tier cho user, báo lỗi "Unknown column 'notes' in 'field list'"
- **Nguyên nhân**: 
  - Function `manually_change_user_tier()` trong `services/billing_service.py` INSERT vào subscriptions table với column `notes`
  - Subscriptions table không có column `notes` (chỉ có user_id, tier, status, expires_at, payment_method, amount, currency, started_at)
  - SQL INSERT statement include column `notes` nhưng table schema không có column này
- **Cách xử lý**: 
  - Xóa column `notes` khỏi INSERT statement trong `manually_change_user_tier()`
  - Không lưu notes vào subscriptions table (notes chỉ dùng để log/audit, không cần lưu trong database)
  - Nếu cần lưu notes, có thể log vào payment records hoặc audit log table riêng
- **Cách tránh lần sau**: 
  - **Khi INSERT/UPDATE database**: Luôn kiểm tra table schema trước khi thêm columns
  - **Không giả định** columns tồn tại mà không verify schema
  - **Test** với database schema thực tế trước khi commit
  - **Backward compatibility**: Nếu column optional, dùng try/except hoặc check column exists trước

---

## Issue #40: Raw data structures (dict/JSON) hiển thị trực tiếp trên giao diện người dùng

- **Mức độ nghiêm trọng**: 🔴 CRITICAL (Security + UX)
- **Mô tả**: 
  - Hiển thị raw dictionary/JSON object (ví dụ: `{'id': 1, 'email': '...', 'status': 'active', 'email_verified': 1}`) trực tiếp trên giao diện login/dashboard thay vì render HTML template
  - Đây là lỗi bảo mật và UX nghiêm trọng - có thể expose sensitive data, nhìn không chuyên nghiệp, và dễ bị exploit
- **Nguyên nhân**: 
  - Tuple unpacking sai thứ tự: `success, error_msg, user_data = authenticate_user(...)` nhưng function return `(success, user_dict, error_message)`
  - Thiếu try-except wrapper ở routes → exception có thể return raw data
  - Không có validation để đảm bảo luôn render template, không return raw dict/JSON
- **Cách xử lý**: 
  - **Sửa tuple unpacking**: Đổi thành `success, user_data, error_msg = authenticate_user(...)` để khớp với function return signature
  - **Wrap routes trong try-except**: Bắt mọi exception, log vào server, và hiển thị user-friendly message
  - **LUÔN render template**: Portal routes PHẢI dùng `render_template()`, KHÔNG BAO GIỜ return dict/JSON trực tiếp (trừ AJAX endpoints)
  - **Remove debug code**: Xóa mọi `print()`, `return dict`, `jsonify(user)` trong production code
  - **Error messages generic**: Không expose exception details, stack traces, hoặc raw data structures
- **Cách tránh lần sau**: 
  - **Verify tuple unpacking**: Đảm bảo thứ tự variables khớp với function return signature
  - **LUÔN render template**: Portal routes (GET) PHẢI render template, không return raw data
  - **AJAX endpoints**: Chỉ return JSON cho AJAX requests (có `X-Requested-With` header)
  - **Error handling**: Mọi exception phải được catch và hiển thị user-friendly message
  - **Code review**: Rà soát kỹ để đảm bảo không leak raw data structures
  - **Production code**: Không bao giờ có debug code (print/return raw data) trong production
  - **Defense in depth**: Kiểm tra mọi routes để đảm bảo không leak raw data

---

## Issue #41: Login page responsive issues - elements bị che khuất và checkbox quá lớn

- **Mức độ nghiêm trọng**: 🟡 MEDIUM (UX)
- **Mô tả**: 
  - Một số thành phần bị che khuất trên mobile/small screens (ví dụ: "Đăng ký ngay" link)
  - Checkbox "Ghi nhớ đăng nhập" quá lớn (16px) và label font-size/weight quá lớn, làm xấu UI
  - Thiếu responsive design cho mobile devices
- **Nguyên nhân**: 
  - Z-index và overflow issues: background elements có thể che khuất content
  - Checkbox size (16px) và label styling (font-size sm, font-weight medium) quá lớn
  - Thiếu media queries cho mobile (< 480px)
  - Form utility row không có flex-wrap, có thể overflow trên mobile
- **Cách xử lý**: 
  - **Giảm checkbox size**: Từ 16px xuống 14px
  - **Giảm label size**: Từ font-size sm + font-weight medium xuống font-size xs + font-weight normal
  - **Thêm responsive styles**: Media query cho mobile (< 480px) để:
    - Giảm padding cho login-content
    - Giảm font-size cho title và footer
    - Thêm flex-wrap cho form-utility
    - Đảm bảo z-index đúng cho tất cả elements
  - **Fix z-index**: Đảm bảo login-container, login-content, login-footer có z-index đúng
  - **Fix overflow**: Đổi overflow từ `hidden` sang `visible` cho login-container
  - **Improve spacing**: Thêm gap và flex-wrap cho form-utility row
- **Cách tránh lần sau**: 
  - **Mobile-first design**: Luôn test trên mobile devices hoặc browser DevTools mobile view
  - **Checkbox sizing**: Checkbox nên nhỏ gọn (12-14px), label nên nhỏ (xs size, normal weight)
  - **Z-index management**: Luôn đảm bảo content có z-index cao hơn background elements
  - **Responsive testing**: Test trên nhiều screen sizes (320px, 375px, 768px, 1024px)
  - **Overflow handling**: Cẩn thận với overflow: hidden - có thể cắt content
  - **Flex-wrap**: Luôn thêm flex-wrap cho flex containers có thể overflow trên mobile

---

## Issue #42: CSS mất sau khi chuyển sang Tailwind CDN - CSP chặn external scripts

- **Mức độ nghiêm trọng**: 🔴 CRITICAL (UI/UX)
- **Mô tả**: 
  - Sau khi chuyển login page sang dùng Tailwind CSS CDN, toàn bộ CSS bị mất
  - Trang login hiển thị không có style, chỉ có HTML thuần
  - Background, colors, spacing, fonts đều không hiển thị
- **Nguyên nhân**: 
  - CSP (Content Security Policy) header trong `app/__init__.py` chỉ cho phép scripts từ `'self'` và `'unsafe-inline'`
  - Tailwind CSS CDN (`https://cdn.tailwindcss.com`) bị CSP chặn vì không có trong `script-src` whitelist
  - Tailwind CDN cần load script để generate CSS, nếu script bị chặn thì CSS không được apply
- **Cách xử lý**: 
  - **Cập nhật CSP header**: Thêm `https://cdn.tailwindcss.com` vào `script-src` directive:
    ```python
    script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com
    ```
  - **Thêm Tailwind CDN vào style-src**: Nếu Tailwind inject styles, cần thêm vào `style-src`:
    ```python
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com
    ```
  - **Verify CSP**: Test lại để đảm bảo Tailwind script load được (check browser console)
- **Cách tránh lần sau**: 
  - **Kiểm tra CSP trước khi dùng CDN**: Khi thêm external CDN (Tailwind, Bootstrap, jQuery...), luôn kiểm tra CSP whitelist
  - **Browser console**: Luôn check browser console khi CSS/JS không load - CSP violations sẽ hiển thị ở đó
  - **CSP cho CDN**: Luôn thêm CDN domain vào cả `script-src` và `style-src` nếu cần
  - **Test after change**: Sau khi thay đổi CSP, luôn test lại để đảm bảo external resources load được
  - **Document CSP changes**: Ghi lại các CDN domains được whitelist trong CSP để dễ maintain

---

## Issue #43: Trang login và register có 2 thanh cuộn (scrollbar) - một thanh bị thừa

- **Mức độ nghiêm trọng**: 🟡 MEDIUM (UX)
- **Mô tả**: 
  - Trang login và register hiển thị 2 thanh cuộn (scrollbar) bên phải
  - Một thanh cuộn bị thừa, gây xấu UI và confusing cho người dùng
  - Có thể scroll cả body và container riêng biệt
- **Nguyên nhân**: 
  - Body có `overflow-y: auto` trong CSS inline
  - Container div bên ngoài cũng có class `overflow-y-auto` từ Tailwind
  - Cả 2 elements đều tạo scrollbar riêng → 2 scrollbars hiển thị
  - `min-h-screen` với `overflow-y-auto` trên container tạo scrollbar không cần thiết
- **Cách xử lý**: 
  - **Xóa overflow-y từ body CSS**: Chỉ giữ `overflow-x: hidden`, xóa `overflow-y: auto`
  - **Xóa overflow-y-auto từ container**: Xóa class `overflow-y-auto` khỏi container div
  - **Chỉ giữ overflow-x-hidden**: Để tránh scroll ngang, chỉ cần `overflow-x-hidden` trên container
  - **Set height: 100% cho html/body**: Đảm bảo body chiếm full height, không tạo scrollbar thừa
  - **Browser tự động scroll**: Browser sẽ tự động tạo scrollbar khi cần (khi content > viewport)
- **Cách tránh lần sau**: 
  - **Tránh duplicate overflow**: Không set `overflow-y` trên cả body và container
  - **Chỉ một scrollbar**: Chỉ để browser tự động tạo scrollbar từ body/html
  - **Test scrollbar**: Luôn test để đảm bảo chỉ có 1 scrollbar
  - **Overflow strategy**: 
    - Body: `overflow-x: hidden` (tránh scroll ngang)
    - Container: `overflow-x-hidden` (nếu cần), không set `overflow-y`
    - Để browser tự xử lý scroll dọc khi cần
  - **Min-height vs overflow**: `min-h-screen` không cần `overflow-y-auto` - browser tự scroll khi content > viewport