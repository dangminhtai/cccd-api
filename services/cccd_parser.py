from __future__ import annotations

from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class GenderCentury:
    gender: str  # "Nam" | "Nữ"
    century: str  # "18" | "19" | "20" | "21" | "22"


_GENDER_CENTURY_MAP: dict[int, GenderCentury] = {
    0: GenderCentury(gender="Nam", century="19"),
    1: GenderCentury(gender="Nữ", century="19"),
    2: GenderCentury(gender="Nam", century="20"),
    3: GenderCentury(gender="Nữ", century="20"),
    4: GenderCentury(gender="Nam", century="21"),
    5: GenderCentury(gender="Nữ", century="21"),
    6: GenderCentury(gender="Nam", century="22"),
    7: GenderCentury(gender="Nữ", century="22"),
    8: GenderCentury(gender="Nam", century="18"),
    9: GenderCentury(gender="Nữ", century="18"),
}


def parse_province_code(cccd: str) -> str | None:
    # CCCD 12 digits: province code is first 3 digits
    if len(cccd) < 3:
        return None
    return cccd[:3]


def parse_gender_century(cccd: str) -> GenderCentury | None:
    # 4th digit indicates gender + century
    if len(cccd) < 4:
        return None
    try:
        code = int(cccd[3])
    except ValueError:
        return None
    return _GENDER_CENTURY_MAP.get(code)


def parse_birth_year(cccd: str) -> int | None:
    # birth year: century digit (pos 4) + 2 digits (pos 5-6)
    gc = parse_gender_century(cccd)
    if gc is None or len(cccd) < 6:
        return None
    yy = cccd[4:6]
    if not yy.isdigit():
        return None
    return int(gc.century) * 100 + int(yy)


def parse_age(birth_year: int | None, as_of_year: int | None = None) -> int | None:
    if birth_year is None:
        return None
    year_now = as_of_year if as_of_year is not None else date.today().year
    age = year_now - birth_year
    if age < 0 or age > 150:
        return None
    return age


def parse_cccd(cccd: str) -> dict:
    """
    Parse CCCD (12 digits) to minimal, stable fields for downstream systems.

    Note: `province_name` is intentionally left as None for Step 5 (mapping).
    """
    province_code = parse_province_code(cccd)
    gc = parse_gender_century(cccd)
    birth_year = parse_birth_year(cccd)

    return {
        "province_code": province_code,
        "province_name": None,
        "gender": gc.gender if gc else None,
        "birth_year": birth_year,
        "century": gc.century if gc else None,
        "age": parse_age(birth_year),
    }


