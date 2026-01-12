# lession_learn.md

## 1) Khi làm bulk rename/replace trên Windows, phải kiểm tra lại bằng `list_dir` + `grep`

- Rename/replace hàng loạt rất nhanh nhưng dễ “lệch” 1 file.
- Sau khi chạy lệnh, luôn:
  - kiểm tra danh sách file có đúng tên chưa
  - grep chuỗi cũ để chắc không còn sót
  - mở 1–2 file bất kỳ để spot-check nội dung

---

## 2) Tránh “PowerShell trong PowerShell”

- Nếu đã đang ở PowerShell thì chạy thẳng command.
- Nếu lồng `powershell -Command`, biến `$var` có thể bị parse sai và gây lỗi khó hiểu.

---

## 3) Luôn ưu tiên thao tác an toàn khi xoá file

- Khi đang rename/shift bước, xoá nhầm rất dễ xảy ra.
- Nên:
  - delete từng file (hoặc xác nhận list file sẽ xoá)
  - tạo file mới trước, verify đủ, rồi mới xoá file cũ

---

## 4) Đừng giả định dotfile luôn tạo được

- Một số workspace có rule chặn dotfile.
- Nên có phương án dự phòng:
  - `env.example` thay cho `.env.example`
  - `.gitignore` vẫn ignore `.env` để bảo vệ secrets

---

## 5) Khi chạy service trong background, phải có “cách dừng” rõ ràng

- Start background dễ, nhưng dừng không đúng cách sẽ làm:
  - cổng bị chiếm
  - test sau bị sai
- Bài học: có 1 lệnh stop “chuẩn” (ví dụ kill theo `CommandLine` chứa `run.py`) và xác nhận bằng gọi endpoint.

---

## 6) Tài liệu cần khớp với người đọc mục tiêu

- Với file “WHY” thì ưu tiên:
  - vấn đề người dùng đang gặp
  - có API thì giải quyết gì, tiết kiệm chi phí ở đâu
  - tránh thuật ngữ khó
- Với file “requirement/checklist/guide_step” thì ưu tiên:
  - rõ đầu vào/đầu ra
  - tiêu chí nghiệm thu
  - task nhỏ, dễ tick

---

## 7) Sau mỗi bước phải commit + push (để dễ review và rollback)

- Làm xong **mỗi step** (vd: step 01, step 02...) thì:
  - `git add ...` (ưu tiên add đúng phần của step đó)
  - `git commit -m "..."`
  - `git push`
- Lợi ích:
  - Có “mốc” rõ ràng theo từng bước → dễ review, dễ quay lại nếu có lỗi.
  - Tránh dồn quá nhiều thay đổi vào 1 commit lớn khó kiểm tra.
- Quy ước commit message (gợi ý):
  - `step01: scaffold flask project`
  - `step02: define api contract docs`
  - `fix: adjust step numbering`


## 8) Hướng dẫn người dùng tự test ở mỗi bước ở mỗi guide_step_xx.md

 - Mỗi `guide_step_xx.md` nên có mục **“Tự test (Self-check)”** ở cuối file.
 - Nếu step chưa có code thì “tự test” là:
   - review doc theo checklist
   - grep các chuỗi quan trọng (endpoint/field) để đảm bảo thống nhất
 - Nếu step đã có code thì “tự test” là:
   - chạy server
   - gọi endpoint
   - hoặc chạy pytest

---

## 9) Tránh dùng `git status` nếu không cần (theo yêu cầu tối giản)

- Khi user muốn làm nhanh, **không chạy `git status` chỉ để “xem cho chắc”** nếu không được yêu cầu.
- Thay vào đó, có thể đi thẳng:
  - `git add -A`
  - `git commit -m "..."`
  - `git push`
- Chỉ dùng `git status` khi:
  - cần debug staging (quên add file / add nhầm file)
  - hoặc user yêu cầu kiểm tra trạng thái

## 10) Trong quá trình prompt nếu có lỗi nào thì hãy ghi nó vào issues_list.md để sau này không sai lại lỗi đó

---

## 11) Ưu tiên “test tối giản” bằng web local (ít command line nhất)

- Mục tiêu của self-test là để **người không rành terminal vẫn test được**.
- Quy ước khuyến nghị:
  - luôn có trang demo web: `GET /demo`
  - trang demo gọi API thật: `POST /v1/cccd/parse`
  - hiển thị rõ 2 thứ: **HTTP Status** và **JSON response**
- Tiêu chí “OK” nên viết ngắn gọn ngay trên trang demo và trong guide:
  - Case đúng (CCCD 12 số): Status **200**, `success=true`, `is_valid_format=true`
  - Case sai (CCCD sai độ dài/ký tự): Status **400**, `success=false`, `is_valid_format=false`
- Chỉ dùng PowerShell/curl khi:
  - debug sâu (headers/auth/rate limit), hoặc
  - tự động hoá test (pytest/CI)

---

## 12) Tránh lặp lại việc chạy `run.py` / kill process theo port nếu user đã tự test được

- Nếu user đã có thể tự chạy và tự test bằng `/demo` rồi thì:
  - **không cần** agent phải start/stop server lại sau mỗi step
  - **không cần** kill process theo port (tránh làm gián đoạn các process khác của user)
- Chỉ chạy smoke test khi:
  - user yêu cầu “hãy test giúp”
  - hoặc cần debug lỗi thật sự
  - hoặc có thay đổi lớn ở routing/template khiến dễ gãy
- Khi cần hướng dẫn dừng server:
  - ưu tiên “Ctrl + C” ở terminal đang chạy `run.py`
## 13) Đảm bảo tính nhất quán giữa tên file mapping và version name trong code/docs

- **Issue**: Khi đổi tên file `provinces_legacy_64.json` thành `provinces_legacy_63.json`, nếu không cập nhật đồng bộ các hằng số/literal `legacy_64` thành `legacy_63` trong code và tài liệu sẽ gây hiểu lầm cho người dùng.
- **Cách xử lý**:
  - Chuẩn hoá toàn bộ reference về tên mới (`legacy_63`).
  - Nếu cần tương thích ngược, hỗ trợ alias (`legacy_64`) trong code nhưng trả về kết quả kèm warning khuyến cáo dùng tên mới.
  - Cập nhật cả file `.md` hướng dẫn và `checklist.md`.
- **Bài học**: Khi thay đổi một định danh (identifier) mang tính toàn cục, hãy dùng `grep` để quét sạch và cập nhật tất cả các chỗ liên quan ngay lập tức.

---

## 14) Sai config `DEFAULT_PROVINCE_VERSION` sẽ silently fallback nếu không hỗ trợ alias

- **Issue**: Đặt `DEFAULT_PROVINCE_VERSION=current_63` (typo) làm API vẫn dùng mặc định `current_34`, gây nhầm lẫn.
- **Cách xử lý**:
  - Chuẩn hoá giá trị hợp lệ (`legacy_63`, `current_34`), cập nhật file `.env` mẫu.
  - Hỗ trợ alias (`current_63` → `current_34`, `legacy_64` → `legacy_63`) và thêm warning trong response khi nhận alias.
- **Bài học**: Với config dạng enum, luôn:
  - xác định tập giá trị hợp lệ, ghi rõ trong `.env.example`
  - chấp nhận alias an toàn + log/warning để người dùng sửa cấu hình

---

## 15) Demo page phải hiển thị trạng thái cấu hình (bật/tắt) của feature đang test

- **Issue**: Khi test feature "API Key", người dùng luôn thấy status 200, không biết tại sao không thể test trường hợp 401.
- **Nguyên nhân**: Server chưa cấu hình `API_KEY`, nhưng demo page không nói rõ điều này.
- **Cách xử lý**:
  - Trên `/demo`, hiển thị hộp trạng thái:
    - 🔐 Xanh lá: "API Key đang BẬT" + key cần nhập.
    - 🔓 Cam: "API Key đang TẮT" + hướng dẫn bật.
- **Bài học**: Khi tạo demo page cho feature có cấu hình on/off, luôn:
  - render trạng thái hiện tại (enabled/disabled)
  - hướng dẫn ngay trên trang cách bật/tắt nếu chưa đúng
  - đừng để người test đoán mò

---

## 16) Self-check là NGƯỜI test thủ công, không phải máy chạy pytest

- **Issue**: Viết "Self-check" chỉ có lệnh `python -m pytest` → người dùng không biết test thủ công như thế nào.
- **Nguyên nhân**: Nhầm lẫn giữa "automated test" và "manual self-check".
- **Cách xử lý**: Viết Self-check dạng bảng:
  - Cột 1: Nhập gì vào `/demo`
  - Cột 2: Kỳ vọng status/response là gì
  - Liệt kê từng case: validation, API key, parse, province version, plausibility
- **Bài học**: Self-check phải:
  - Dành cho người **không tin code** và muốn verify bằng tay
  - Dùng `/demo` page (ít command line nhất)
  - Có bảng input → expected output rõ ràng
  - Automated tests (pytest) chỉ là bonus ở cuối

---

## 17) Guide phải là checklist từng bước, KHÔNG PHẢI dump code

- **Issue**: Viết `guide_step_10.md` với hàng trăm dòng code Python/SQL → người đọc không biết bắt đầu từ đâu.
- **Nguyên nhân**: Nhầm lẫn giữa "tài liệu kỹ thuật" và "hướng dẫn từng bước".
- **Cách xử lý**: Viết guide dạng:
  - **Checklist nhỏ**: `- [ ] Đã tạo database`
  - **"Cách làm"**: 1-2-3 bước cụ thể
  - **Bảng kỳ vọng**: Input → Output
  - Code chỉ là **lệnh ngắn** để copy-paste, không phải file code dài
- **Bài học**: Guide file phải:
  - Dành cho người **không biết code** cũng làm theo được
  - Có checkbox để tick khi hoàn thành
  - Mỗi section có "Cách làm" rõ ràng
  - Code dài → để trong `scripts/` hoặc `services/`, guide chỉ gọi lệnh
  - Người đọc tư duy theo **quy trình**, không tư duy theo **code**

---

## 18) LUÔN push sau khi commit 
---

## 19) Werkzeug development server KHÔNG THỂ xóa Server header hoàn toàn

- **Issue**: Thử nhiều cách (WSGI middleware, `@app.after_request`, wrap `app.wsgi_app`) nhưng vẫn bị leak `Werkzeug/3.1.3 Python/3.12.4` trong development server.
- **Nguyên nhân**: 
  - Werkzeug development server (`app.run()`) tự động thêm Server header **SAU KHI** tất cả handlers (`after_request`, WSGI middleware) chạy
  - Header được thêm ở mức thấp nhất của Werkzeug, không thể can thiệp từ Flask app
- **Giải pháp đã thử nhưng KHÔNG thành công**:
  - ❌ `@app.after_request` - Werkzeug thêm header sau
  - ❌ WSGI middleware wrap toàn bộ app - không hoạt động với `app.run()`
  - ❌ Wrap `app.wsgi_app` - vẫn không hoạt động với dev server
- **Giải pháp đúng (theo best practice)**:
  - ✅ **Development/Local**: Chấp nhận Server header leak (low risk, chỉ là local/dev)
  - ✅ **Production**: Dùng Gunicorn + Nginx
    - Gunicorn: `@app.after_request` sẽ xóa Server header thành công
    - Nginx: Tự động xóa Server header (hoặc có thể config `server_tokens off;`)
  - ✅ Code vẫn giữ `@app.after_request` để xóa header trong production
- **Bài học**: 
  - **KHÔNG THỂ** xóa Server header hoàn toàn với Werkzeug development server
  - Development: Có thể chấp nhận leak (low risk)
  - Production: Luôn dùng Gunicorn + Nginx (Server header sẽ được xóa)
  - Đừng tốn thời gian cố fix điều không thể fix được
  - Ghi rõ trong code comment: "Werkzeug dev server adds header after after_request"

---

## 20) ĐỪNG BAO GIỜ TIN những gì người dùng nhập vào - Luôn validate đầu vào

- **Issue**: Người dùng có thể nhập bất kỳ thứ gì vào form/API, kể cả dữ liệu độc hại hoặc sai format.
- **Nguyên nhân**: 
  - Thiếu validation ở backend
  - Chỉ dựa vào frontend validation (có thể bypass)
  - Không kiểm tra độ dài đầu vào → DoS risk
- **Cách xử lý**:
  - **Luôn validate ở backend** (không tin frontend)
  - **Kiểm tra độ dài đầu vào** ngay từ đầu (trước khi xử lý)
  - **Validate format** (regex, type checking)
  - **Sanitize input** nếu cần (nhưng không thay thế validation)
  - **Reject sớm** nếu không hợp lệ (tiết kiệm CPU/memory)
- **Ví dụ**:
  - Email: Check format regex + độ dài tối đa (255 chars)
  - Password: Check độ dài tối thiểu (8 chars) + độ dài tối đa (100 chars)
  - CCCD: Check độ dài chính xác (12) + chỉ số (0-9)
  - Days valid: Check là số nguyên dương + không quá lớn (ví dụ max 3650 = 10 năm)
- **Bài học**: 
  - **Backend validation là bắt buộc**, frontend chỉ là UX
  - **Validate độ dài đầu vào** để tránh DoS với string cực dài
  - **Reject sớm** = tiết kiệm tài nguyên server
  - **Defense in depth**: Validate nhiều lớp (frontend + backend + database constraints)

---

## 21) Markdown files: Viết ngắn gọn, đừng giải thích dài dòng, đừng tạo quá nhiều file

- **Issue**: Tạo quá nhiều file markdown với nội dung dài dòng, giải thích chi tiết không cần thiết. User đọc mệt mỏi, khó tìm thông tin.
- **Nguyên nhân**: 
  - Giải thích quá nhiều thay vì làm luôn
  - Viết code/giải thích dài trong markdown
  - Tạo quá nhiều file riêng lẻ thay vì gom lại
- **Cách xử lý**:
  - **Markdown chỉ để document**, không phải để giải thích chi tiết
  - **Ngắn gọn**, đủ để người đọc hiểu được
  - **Gom các nội dung liên quan** vào 1 file thay vì tách nhiều file
  - **Không cần code examples dài** trong markdown (code thì để trong code files)
  - **Không giải thích "tại sao" quá nhiều** - chỉ ghi "làm gì" và "như thế nào"
- **Bài học**: 
  - **Ngắn gọn > Dài dòng**: Người đọc chỉ cần biết làm gì, không cần biết tại sao
  - **Ít file > Nhiều file**: Dễ tìm hơn, ít duplicate hơn
  - **Markdown là documentation**, không phải tutorial dài
  - **Lần sau đọc là hiểu** - đó là mục tiêu của documentation

---

## 22) Tuân thủ nguyên tắc DRY (Don't Repeat Yourself)

- **Issue**: Code trùng lặp ở nhiều nơi (ví dụ: navigation menu xuất hiện ở header và trong content của mỗi page).
- **Nguyên nhân**: 
  - Copy-paste code thay vì reuse component/template
  - Không nhận ra code đã có ở chỗ khác
- **Cách xử lý**:
  - **Định nghĩa 1 lần, dùng nhiều lần**: Navigation chỉ định nghĩa ở header, templates khác extend base.html
  - **Dùng template inheritance**: `{% extends "base.html" %}` thay vì copy code
  - **Dùng includes**: `{% include "component.html" %}` cho reusable components
  - **DRY check**: Trước khi thêm code mới, kiểm tra xem đã có chưa
- **Ví dụ**:
  - Navigation menu: Chỉ ở `portal/header.html`, không lặp lại ở dashboard/usage/billing
  - CSS classes: Dùng design system (variables.css) thay vì inline styles
  - Form validation: Dùng shared JavaScript (forms.js) thay vì copy code
- **Bài học**: 
  - **DRY = Don't Repeat Yourself**: Mỗi logic chỉ viết 1 lần
  - **Template inheritance** giúp tránh duplicate code
  - **Component-based**: Tách reusable parts thành components
  - **Code duplication = Maintenance nightmare**: Sửa 1 chỗ phải sửa nhiều chỗ

---

## 23) Prevent duplicate pending records - Kiểm tra trước khi tạo mới

- **Issue**: User có thể spam nút "nâng cấp gói" và tạo nhiều payment records với status "pending" cho cùng một gói. Không hợp lý - chỉ nên có 1 pending payment tại một thời điểm.
- **Nguyên nhân**: 
  - Thiếu validation trước khi tạo record mới
  - Không kiểm tra xem đã có pending record chưa
  - User có thể click nhiều lần (spam)
- **Cách xử lý**:
  - **Check trước khi create**: Kiểm tra xem user đã có pending payment chưa
  - **Prevent spam**: Chỉ cho phép 1 pending payment per user tại một thời điểm
  - **User-friendly message**: Hiển thị message rõ ràng thay vì tạo duplicate
  - **Database constraints**: Có thể thêm UNIQUE constraint nếu cần (nhưng phức tạp hơn)
- **Ví dụ**:
  - Upgrade payment: Check `has_pending_payment(user_id)` trước khi `create_payment()`
  - Subscription requests: Chỉ cho phép 1 pending request
  - Order creation: Kiểm tra xem đã có order pending chưa
- **Bài học**: 
  - **Luôn check trước khi create**: Tránh duplicate records
  - **Prevent spam**: User có thể click nhiều lần
  - **Business logic validation**: Không phải mọi thứ đều hợp lệ
  - **User experience**: Message rõ ràng hơn là tạo duplicate silently

---

## 24) Code files quá dài (>500 dòng) khó đọc và maintain - Cần clean code và module organization

- **Issue**: Một số file Python có >500-1000 dòng code (ví dụ: `user_service.py` 712 dòng, `billing_service.py` 556 dòng, `admin.html` 990 dòng). Rất khó đọc, khó maintain, khó test.
- **Nguyên nhân**: 
  - Tất cả logic đặt trong 1 file lớn
  - Không tách concerns (models, services, repositories, utils)
  - Không có module organization rõ ràng
  - Copy-paste thay vì reuse
- **Cách xử lý**:
  - **Giới hạn file size**: 1 file Python nên <= 300-500 dòng (best practice)
  - **Tách concerns**: Models, Services, Repositories, Utils, Validators
  - **Module organization**: Chia theo domain (user, billing, api_key) hoặc feature
  - **Single Responsibility Principle**: Mỗi module/class chỉ làm 1 việc
  - **DRY**: Tái sử dụng code thay vì duplicate
- **Ví dụ refactor**:
  - `user_service.py` (712 dòng) → tách thành:
    - `services/user/models.py` - User data models
    - `services/user/repository.py` - Database queries (raw SQL)
    - `services/user/service.py` - Business logic
    - `services/user/validators.py` - Input validation
    - `services/user/utils.py` - Helper functions (hash_password, etc.)
  - `billing_service.py` (556 dòng) → tách tương tự
  - `admin.html` (990 dòng) → tách thành components, dùng includes
- **Bài học**: 
  - **File size matters**: File >500 dòng = red flag, cần refactor
  - **Clean code = Professional**: Dự án chuyên nghiệp phải có code organization tốt
  - **Module organization**: Dễ đọc, dễ test, dễ maintain
  - **Tách concerns**: Mỗi file chỉ làm 1 việc, dễ hiểu hơn
  - **Refactor từng bước**: Không cần refactor hết cùng lúc, làm từng module một

---

## 25) KHÔNG BAO GIỜ hiển thị raw data structures (dict, JSON) ra giao diện người dùng

- **Issue**: Hiển thị raw dictionary/JSON object (ví dụ: `{'id': 1, 'email': '...', 'status': 'active'}`) trực tiếp trên giao diện login/dashboard thay vì render HTML template. Đây là lỗi bảo mật và UX nghiêm trọng - có thể expose sensitive data, nhìn không chuyên nghiệp, và dễ bị exploit.
- **Nguyên nhân**: 
  - Exception handler return raw data thay vì render template
  - Debug code còn sót lại (print/return dict trực tiếp)
  - Tuple unpacking sai thứ tự khiến variable assignment sai
  - Thiếu try-catch ở routes, exception được Flask handler catch và return raw data
- **Cách xử lý**:
  - **LUÔN render template**: Portal routes PHẢI dùng `render_template()`, KHÔNG BAO GIỜ return dict/JSON trực tiếp
  - **Wrap routes trong try-except**: Bắt mọi exception, log vào server, và hiển thị user-friendly message
  - **Verify tuple unpacking**: Đảm bảo thứ tự variables khớp với function return signature
  - **Remove debug code**: Xóa mọi `print()`, `return dict`, `jsonify(user)` trong production code
  - **Error messages generic**: Không expose exception details, stack traces, hoặc raw data structures
  - **Validate data trước khi pass to template**: Chỉ pass những gì cần thiết, không pass raw dict
- **Ví dụ**:
  - ❌ **SAI**: `return user_dict` hoặc `return jsonify(user)` trong portal route
  - ✅ **ĐÚNG**: `return render_template("portal/login.html")` với flash message
  - ❌ **SAI**: `except Exception as e: return str(e)` hoặc `return e`
  - ✅ **ĐÚNG**: `except Exception as e: logger.error(...); flash("Lỗi hệ thống"); return render_template(...)`
- **Bài học**: 
  - **Security first**: Raw data exposure = security vulnerability + bad UX
  - **Professional UI**: Người dùng chỉ thấy HTML đẹp, không thấy code/data structures
  - **Error handling**: Mọi exception phải được catch và hiển thị user-friendly message
  - **Production code**: Không bao giờ có debug code (print/return raw data) trong production
  - **Defense in depth**: Kiểm tra mọi routes để đảm bảo không leak raw data
  - **Code review critical**: Lỗi này rất dễ miss trong code review, cần rà soát kỹ

---

## 26) Overflow strategy cho decorative elements và flash messages - Ưu tiên decorative elements

- **Issue**: Khi fix flash message bị khuất, đổi card từ `overflow-hidden` sang `overflow-visible`, nhưng làm decorative top bar (gradient bar) không hiển thị đúng border-radius.
- **Nguyên nhân**: 
  - Decorative elements (bars, borders) cần card có `overflow-hidden` để border-radius hoạt động đúng
  - Flash messages cần không bị cắt, nhưng thực ra flash messages nằm trong padding area sẽ không bị cắt bởi `overflow-hidden`
  - Conflict giữa việc fix flash message (nghĩ cần overflow-visible) và decorative bar (cần overflow-hidden)
- **Cách xử lý**:
  - **Card overflow hidden**: Card phải có `overflow-hidden` để decorative elements hiển thị đúng border-radius
  - **Flash messages safe**: Flash messages nằm trong padding area (không phải edge) sẽ không bị cắt bởi `overflow-hidden`
  - **Word-wrap cho flash**: Thêm `word-wrap: break-word` và `overflow-wrap: break-word` cho flash message để text dài không bị overflow
  - **Decorative elements**: Không cần thêm `rounded-t-*` cho decorative bar nếu card đã có `rounded-*` và `overflow-hidden` (sẽ tự động clip)
- **Bài học**: 
  - **Overflow strategy**: Khi có decorative elements cần border-radius, card phải có `overflow-hidden`
  - **Flash messages**: Flash messages nằm trong padding area sẽ không bị cắt bởi `overflow-hidden`
  - **Conflict resolution**: Khi có conflict, ưu tiên decorative elements (dùng overflow-hidden) và đảm bảo flash message nằm trong safe area
  - **Test visual**: Luôn test để đảm bảo cả decorative elements và flash messages đều hiển thị đúng
  - **Don't overthink**: Flash messages trong padding area không cần `overflow-visible`, `overflow-hidden` vẫn hoạt động tốt

---

## 27) Custom scrollbar design và overflow strategy - Chỉ có 1 thanh cuộn, đẹp như usage.html

- **Issue**: Trang login và các trang khác có 2 thanh cuộn (scrollbar) - một từ html, một từ body hoặc container. Scrollbar mặc định của browser trông phèn, không đẹp như `usage.html`.
- **Nguyên nhân**: 
  - Thiếu custom scrollbar CSS styling
  - Có nhiều elements cùng set `overflow-y: auto` (html, body, container) → tạo nhiều scrollbars
  - Dùng inline style `overflow-y: auto; height: calc(100vh - 80px)` trên main tag tạo scrollbar riêng
- **Cách xử lý**:
  - **Custom scrollbar CSS**: Thêm CSS giống `usage.html`:
    ```css
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a; /* hoặc #0B1120 cho login/register */
    }
    ::-webkit-scrollbar-thumb {
        background: #334155; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569; 
    }
    ```
  - **Overflow strategy**: 
    - `html`: Chỉ `overflow-x: hidden` (không set `overflow-y`)
    - `body`: Chỉ `overflow-x: hidden` và `min-height: 100vh` (không set `overflow-y`, không set `height: 100vh`)
    - Container: Không set `overflow-y-auto` nếu không cần thiết
    - Main: Xóa inline style `overflow-y: auto; height: calc(100vh - 80px)` → để body tự scroll
  - **Chỉ 1 scrollbar**: Browser tự tạo scrollbar từ body khi content vượt quá viewport
- **Bài học**: 
  - **Custom scrollbar**: Luôn thêm custom scrollbar CSS cho dark theme (đẹp hơn, nhất quán)
  - **Overflow strategy**: Chỉ để body scroll tự nhiên, không set overflow-y trên nhiều elements
  - **Chỉ 1 scrollbar source**: Browser tự tạo scrollbar từ body, không cần force trên html/container/main
  - **Học từ usage.html**: `usage.html` làm đúng - chỉ có custom scrollbar CSS, body scroll tự nhiên
  - **Test visual**: Luôn test để đảm bảo chỉ có 1 scrollbar đẹp, không có scrollbar thừa

---

## 28) Fix 2 scrollbars trên login/register - Container không được scroll, chỉ body scroll

- **Issue**: Trang login và register vẫn hiển thị 2 thanh cuộn dù đã thêm custom scrollbar CSS. Một từ body, một từ container div.
- **Nguyên nhân**: 
  - Container div có `min-h-screen` và có thể tạo scrollbar riêng khi content vượt quá viewport
  - Body có `min-height: 100vh` cũng có thể tạo scrollbar
  - Cả 2 elements đều có thể scroll → 2 scrollbars hiển thị
  - Container không được set `overflow: visible` rõ ràng → browser có thể tạo scrollbar cho nó
- **Cách xử lý**:
  - **HTML và Body height 100%**: Set `html { height: 100%; }` và `body { height: 100%; }` thay vì `min-height: 100vh` để tránh tạo scrollbar không cần thiết
  - **Container overflow visible**: Thêm class `.login-container` và `.register-container` với `overflow: visible` để container không tạo scrollbar
  - **Chỉ body scroll**: Browser tự tạo scrollbar từ body khi content vượt quá viewport, container chỉ là wrapper
  - **Test kỹ**: Luôn test với content dài (zoom out hoặc thêm nhiều content) để đảm bảo chỉ có 1 scrollbar
- **Bài học**: 
  - **Container không scroll**: Container div chỉ là wrapper, không được set `overflow-y-auto` hoặc để browser tự tạo scrollbar
  - **Body scroll tự nhiên**: Chỉ để body scroll tự nhiên, không force scrollbar trên container
  - **Height vs min-height**: Dùng `height: 100%` trên html/body thay vì `min-height: 100vh` để tránh scrollbar thừa
  - **Overflow visible cho container**: Luôn set `overflow: visible` cho container wrapper để đảm bảo không tạo scrollbar riêng
  - **Test với content dài**: Luôn test với content vượt quá viewport để verify chỉ có 1 scrollbar
  - **Debug scrollbar**: Dùng browser DevTools để kiểm tra element nào đang tạo scrollbar (check computed styles)

---

## 29) Fix 2 scrollbars - Nguyên nhân cốt lõi: 100vh + padding làm dư chiều cao

- **Issue**: Trang login và register vẫn có 2 thanh cuộn dù đã thử nhiều cách. Một từ body, một từ container.
- **Nguyên nhân cốt lõi**: 
  - **Body được phép scroll** (có `overflow-y: auto` hoặc mặc định)
  - **Container có `min-height: 100vh` + `py-6` (padding top + bottom)** → tổng chiều cao = 100vh + padding → vượt 100vh
  - Browser tạo scrollbar thứ 2 cho container vì chiều cao vượt viewport
  - Cả body và container đều có thể scroll → 2 scrollbars hiển thị
- **Cách xử lý đúng**:
  - **HTML overflow hidden**: Set `html { overflow: hidden; height: 100%; }` để html không scroll
  - **Body overflow-y auto**: Set `body { overflow-y: auto; overflow-x: hidden; height: 100%; }` để chỉ body scroll
  - **Container giữ nguyên**: Container có thể giữ `min-height: 100vh` và `py-6` vì html đã không scroll
  - **Kết quả**: Chỉ body scroll, html và container không scroll → chỉ có 1 scrollbar
- **Bài học**: 
  - **Nguyên nhân cốt lõi**: `100vh + padding` làm dư chiều cao → tạo scrollbar thứ 2
  - **Giải pháp đúng**: `html { overflow: hidden; }` + `body { overflow-y: auto; }` → chỉ body scroll
  - **Không cần xóa padding**: Có thể giữ `py-6` và `min-height: 100vh` trên container vì html đã không scroll
  - **Test kỹ**: Luôn test với content dài để verify chỉ có 1 scrollbar
  - **Debug scrollbar**: Dùng DevTools check computed styles của html, body, và container để tìm element nào đang tạo scrollbar
  - **Học từ user feedback**: User chỉ ra nguyên nhân chính xác (100vh + padding) → giải pháp đúng là set html overflow hidden

---

## 30) Function return signature phải khớp với cách gọi - Tuple unpacking

- **Issue**: Hàm `reset_password()` chỉ trả về 2 giá trị `(success, error_message)` nhưng route đang expect 3 giá trị `(success, error_msg, user_id)`. Khi unpacking sẽ gây lỗi `ValueError: not enough values to unpack (expected 3, got 2)`.
- **Nguyên nhân**: 
  - Function signature không khớp với cách sử dụng trong route
  - Route cần `user_id` để gọi `invalidate_user_sessions(user_id)` nhưng function không trả về
  - Thiếu `user_id` trong return statement
- **Cách xử lý**: 
  - Cập nhật function `reset_password()` để trả về 3 giá trị: `(success, error_message, user_id)`
  - Khi thành công: `return True, None, user_id`
  - Khi thất bại: `return False, error_message, None`
  - Đảm bảo `user_id` được lấy từ database query trước khi update password
- **Bài học**: 
  - **Function signature phải khớp**: Return values phải khớp với cách unpacking trong code gọi
  - **Verify tuple unpacking**: Luôn kiểm tra số lượng values trả về khớp với số lượng variables nhận
  - **Test function calls**: Test các function calls để đảm bảo không có lỗi unpacking
  - **Type hints**: Dùng type hints `Tuple[bool, Optional[str], Optional[int]]` để rõ ràng return type
  - **Code review**: Rà soát kỹ các function calls để phát hiện mismatch sớm

---

## 31) Custom 404 error page - Phân biệt API và Web requests

- **Issue**: Khi user truy cập endpoint không tồn tại, Flask trả về 404 mặc định (HTML hoặc JSON tùy request). Cần custom 404 page đẹp cho web requests và JSON response cho API requests.
- **Nguyên nhân**: 
  - Flask mặc định không có custom 404 handler
  - API requests (JSON) và Web requests (HTML) cần response format khác nhau
  - Cần phân biệt giữa API endpoints (`/v1/`, `/api/`) và web pages
- **Cách xử lý**: 
  - Thêm `@app.errorhandler(404)` trong `app/__init__.py`
  - Check nếu request là API request (path starts with `/v1/` hoặc `/api/`, hoặc `Accept: application/json`) → return JSON
  - Nếu là web request → render template `404.html` với dark theme
  - Template 404.html có navigation thông minh: redirect đến dashboard nếu logged in, login nếu not
- **Bài học**: 
  - **Error handlers**: Luôn có custom error handlers cho các HTTP status codes phổ biến (404, 500, 429)
  - **Phân biệt request type**: API requests cần JSON, web requests cần HTML
  - **User experience**: Custom 404 page đẹp giúp user không bị confused khi gặp lỗi
  - **Navigation logic**: 404 page nên có link quay lại trang chính (dashboard hoặc login)
  - **Consistent design**: 404 page nên dùng cùng design system (dark theme, glass-panel) với các trang khác


## 32, Chỉ test những test key được thêm; chứ ko nên test lại toàn hệ thống; tốn thời gian