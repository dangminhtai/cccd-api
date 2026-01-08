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