from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

ProvinceVersion = Literal["legacy_63", "current_34"]

_CACHE: dict[ProvinceVersion, dict[str, str]] = {}


def _data_path(version: ProvinceVersion) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    if version == "legacy_63":
        return repo_root / "data" / "provinces_legacy_63.json"
    return repo_root / "data" / "provinces_current_34.json"


def load_province_map(version: ProvinceVersion) -> dict[str, str]:
    if version in _CACHE:
        return _CACHE[version]

    path = _data_path(version)
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid province mapping JSON in {path}")

    # normalize keys to 3-digit strings
    mapping: dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        kk = k.strip()
        if len(kk) == 3 and kk.isdigit():
            mapping[kk] = v.strip()

    _CACHE[version] = mapping
    return mapping


def map_province_name(province_code: str | None, version: ProvinceVersion) -> str | None:
    if not province_code:
        return None
    mapping = load_province_map(version)
    return mapping.get(province_code)


