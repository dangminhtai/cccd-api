# guide_step_00.md — Git/GitHub: lưu trạng thái và đẩy lên repo

## Mục tiêu

Đảm bảo mọi thay đổi tài liệu/source code đều được **commit rõ ràng** và **push lên GitHub** để dễ review và rollback.

## Việc cần làm

- Kiểm tra thay đổi hiện có.
- Add đúng file cần commit.
- Commit với message ngắn gọn, mô tả đúng nội dung.
- Push lên nhánh đang làm việc.

## Lệnh gợi ý

```bash
git status
git add .
git commit -m "docs: add CCCD API requirements/checklist"
git push
```

> Lưu ý: Nếu repo dùng nhánh khác (vd: `main`/`master`/`dev`), hãy đảm bảo bạn đang ở đúng nhánh trước khi push.

## Hoàn thành khi

- [ ] `git status` sạch (working tree clean) sau khi push
- [ ] Nhìn thấy commit mới trên GitHub

## Tự test (Self-check)

- [ ] Chạy `git status` và thấy: `working tree clean`
- [ ] Chạy `git log -1 --oneline` và thấy commit mới nhất đúng nội dung step vừa làm
- [ ] Chạy `git push` và không báo lỗi (hoặc vào GitHub thấy commit đã lên)



