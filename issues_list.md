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


