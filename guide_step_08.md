# guide_step_08.md — Bước 8: Test

## Mục tiêu

Đảm bảo API chạy ổn định và không bị "mỗi nơi một kiểu" khi đổi người làm/đổi phiên bản.

## Việc cần làm

- Unit test validate:
  - thiếu `cccd`
  - `cccd` có chữ
  - sai độ dài
- Unit test parse:
  - vài CCCD giả lập để ra đúng `birth_year`, `gender`, `province_code`
- Unit test mapping:
  - cùng `province_code` nhưng `legacy_63` vs `current_34`
- API test:
  - gọi `POST /v1/cccd/parse` và kiểm tra response có đủ field

## Hoàn thành khi

- [x] Chạy test pass hết (13 tests)
- [x] Khi đổi mapping/tên tỉnh, test giúp phát hiện sai lệch ngay

## Tự test (Self-check)

### Chạy tất cả tests

```bash
python -m pytest tests/ -v
```

Kỳ vọng: **13 passed**

### Danh sách test hiện có

| File | Test cases |
|------|------------|
| `test_validation.py` | missing_cccd, cccd_not_string, cccd_with_letters, wrong_length_short, wrong_length_long, cccd_valid, invalid_province_version |
| `test_cccd_parser.py` | parse_gender_century, parse_cccd_basic |
| `test_province_mapping.py` | province_name_resolved, province_code_not_found_warning, legacy_64_alias_accepted |
| `test_plausibility.py` | birth_year_in_future_flagged |

### Test phát hiện sai lệch

1. Mở `data/provinces_legacy_63.json`
2. Đổi `"079": "Hồ Chí Minh"` thành `"079": "Test City"`
3. Chạy `python -m pytest tests/test_province_mapping.py -v`
4. Sẽ thấy test **FAIL** vì province_name không còn khớp
5. Đổi lại `"079": "Hồ Chí Minh"` → test pass

---

## ✅ DoD (Definition of Done) - Bước 8

| Tiêu chí | Kết quả |
|----------|---------|
| Validation tests (7 cases) | ✅ |
| Parser tests (2 cases) | ✅ |
| Mapping tests (3 cases) | ✅ |
| Plausibility tests (1 case) | ✅ |
| Tổng: 13 tests pass | ✅ |



