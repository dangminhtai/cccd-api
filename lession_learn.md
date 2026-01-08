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
  - `git status` kiểm tra thay đổi
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


