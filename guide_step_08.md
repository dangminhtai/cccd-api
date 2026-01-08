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

- [x] Chạy test pass hết (18 tests)
- [x] Khi đổi mapping/tên tỉnh, test giúp phát hiện sai lệch ngay

## Tự test (Self-check)

### Chạy tất cả tests

```bash
python -m pytest tests/ -v
```

Kỳ vọng: **18 passed**

### Danh sách test hiện có

| File | Test cases |
|------|------------|
| `test_validation.py` | missing_cccd, cccd_not_string, cccd_with_letters, wrong_length_short, wrong_length_long, cccd_extremely_long, cccd_valid, invalid_province_version (8) |
| `test_api_key.py` | missing_api_key_401, wrong_api_key_401, correct_api_key_200, no_api_key_allows_access (4) |
| `test_cccd_parser.py` | parse_gender_century, parse_cccd_basic (2) |
| `test_province_mapping.py` | province_name_resolved, province_code_not_found_warning, backward_compat_legacy_64_maps_to_legacy_63 (3) |
| `test_plausibility.py` | birth_year_in_future_flagged (1) |

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
| Validation tests (8 cases) | ✅ |
| API Key tests (4 cases) | ✅ |
| Parser tests (2 cases) | ✅ |
| Mapping tests (3 cases) | ✅ |
| Plausibility tests (1 case) | ✅ |
| Tổng: **18 tests pass** | ✅ |



