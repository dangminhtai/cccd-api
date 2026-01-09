# 📚 Documentation

Tài liệu dự án CCCD API được tổ chức theo cấu trúc sau:

## 📁 Cấu trúc thư mục

```
docs/
├── README.md                    # File này - tổng quan về docs
├── guides/                      # Hướng dẫn từng bước phát triển
│   ├── guide_step_00.md        # Bước 0: Setup ban đầu
│   ├── guide_step_01.md        # Bước 1: ...
│   └── ...
├── security/                    # Tài liệu và kết quả security testing
│   ├── security_testing_guide.md           # Hướng dẫn penetration testing
│   ├── security_testing_postman_guide.md   # Hướng dẫn test bằng Postman
│   ├── security_test_report.md             # Báo cáo tổng hợp
│   ├── security_test_tiers_report.md       # Báo cáo tier testing
│   ├── test_12_3_results.md                # Kết quả test error leakage
│   └── results/                            # Kết quả test (CSV)
│       ├── security_test_results.csv
│       ├── security_test_admin_results.csv
│       └── ...
└── project/                     # Tài liệu dự án
    ├── requirement.md           # Yêu cầu chi tiết, API contract
    ├── rules.md                 # Quy tắc phát triển
    ├── checklist.md             # Checklist các bước
    ├── issues_list.md           # Danh sách issues đã gặp
    ├── lession_learn.md         # Bài học rút ra
    ├── WHY_NEED_CCCD_API.md     # Lý do cần API này
    └── logging_strategy.md      # Chiến lược logging
```

---

## 🚀 Bắt đầu nhanh

### Cho Developer mới:
1. Đọc [`../README.md`](../README.md) - Quick start
2. Đọc [`project/requirement.md`](project/requirement.md) - Hiểu yêu cầu
3. Đọc [`guides/guide_step_00.md`](guides/guide_step_00.md) - Bắt đầu từ bước 0

### Cho Security Tester:
1. Đọc [`security/security_testing_guide.md`](security/security_testing_guide.md) - Hướng dẫn test
2. Xem [`security/security_test_report.md`](security/security_test_report.md) - Kết quả test

### Cho Project Manager:
1. Đọc [`project/requirement.md`](project/requirement.md) - Yêu cầu sản phẩm
2. Đọc [`project/checklist.md`](project/checklist.md) - Checklist hoàn thành

---

## 📖 Mô tả các file

### Guides (`guides/`)
Hướng dẫn từng bước phát triển dự án, từ setup ban đầu đến deploy:
- `guide_step_00.md` - Setup môi trường
- `guide_step_01.md` - Tạo Flask app
- `guide_step_02.md` - Design API
- ... (xem thêm trong thư mục)

### Security (`security/`)
Tài liệu và kết quả security testing:
- `security_testing_guide.md` - Hướng dẫn penetration testing đầy đủ
- `security_testing_postman_guide.md` - Hướng dẫn test bằng Postman
- `security_test_report.md` - Báo cáo tổng hợp các test cases
- `results/` - Kết quả test dạng CSV

### Project (`project/`)
Tài liệu quản lý dự án:
- `requirement.md` - Yêu cầu chi tiết, API contract
- `rules.md` - Quy tắc phát triển để tránh lỗi
- `checklist.md` - Checklist các bước cần làm
- `issues_list.md` - Danh sách issues đã gặp và cách fix
- `lession_learn.md` - Bài học rút ra trong quá trình phát triển
- `logging_strategy.md` - Chiến lược logging (Flask logger vs Database logs)

---

## 🔍 Tìm kiếm nhanh

| Muốn tìm | File |
|----------|------|
| Quick start | [`../README.md`](../README.md) |
| API contract | [`project/requirement.md`](project/requirement.md) |
| Hướng dẫn setup | [`guides/guide_step_00.md`](guides/guide_step_00.md) |
| Security testing | [`security/security_testing_guide.md`](security/security_testing_guide.md) |
| Quy tắc code | [`project/rules.md`](project/rules.md) |
| Issues đã fix | [`project/issues_list.md`](project/issues_list.md) |
| Bài học | [`project/lession_learn.md`](project/lession_learn.md) |

---

## 📝 Ghi chú

- Tất cả guides được đánh số theo thứ tự (`guide_step_00.md`, `guide_step_01.md`, ...)
- Security test results được lưu trong `security/results/` dạng CSV
- Project docs được tổ chức theo chủ đề trong `project/`
