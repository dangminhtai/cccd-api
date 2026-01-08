from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, jsonify, render_template, request

from services.cccd_parser import parse_cccd
from services.province_mapping import ProvinceVersion, map_province_name

cccd_bp = Blueprint("cccd", __name__)

@cccd_bp.get("/demo")
def demo():
    return render_template("demo.html")


@cccd_bp.post("/v1/cccd/parse")
def cccd_parse():
    payload = request.get_json(silent=True) or {}
    cccd = payload.get("cccd")
    province_version = payload.get("province_version")

    # Basic validate (align with requirement.md)
    if cccd is None:
        return (
            jsonify(
                {
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": "Thiếu trường cccd.",
                }
            ),
            400,
        )

    if not isinstance(cccd, str):
        return (
            jsonify(
                {
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": "CCCD không hợp lệ (cần là chuỗi số, độ dài 12).",
                }
            ),
            400,
        )

    cccd = cccd.strip()
    if (not cccd.isdigit()) or (len(cccd) != 12):
        return (
            jsonify(
                {
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": "CCCD không hợp lệ (cần là chuỗi số, độ dài 12).",
                }
            ),
            400,
        )

    data = parse_cccd(cccd)

    warnings: list[str] = []
    is_plausible = True

    # Resolve province_version (canonical: legacy_63 / current_34)
    settings = current_app.config.get("SETTINGS")
    default_version = getattr(settings, "default_province_version", "current_34")
    version: ProvinceVersion
    if province_version is None or province_version == "":
        # Accept old config value "legacy_64" as alias
        if default_version in ("legacy_63", "legacy_64"):
            version = "legacy_63"
        elif default_version in ("current_34", "current_63"):
            version = "current_34"
        else:
            version = "current_34"
    elif province_version in ("legacy_63", "current_34"):
        version = province_version
    elif province_version == "legacy_64":
        # Backward-compatible alias
        version = "legacy_63"
        warnings.append("province_version_alias_legacy_64")
    elif province_version == "current_63":
        # Backward-compatible alias
        version = "current_34"
        warnings.append("province_version_alias_current_63")
    else:
        return (
            jsonify(
                {
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": "province_version không hợp lệ (chỉ nhận legacy_63 hoặc current_34).",
                }
            ),
            400,
        )

    # province mapping
    province_code = data.get("province_code")
    if isinstance(province_code, str):
        province_name = map_province_name(province_code, version)
        data["province_name"] = province_name
        if province_name is None:
            warnings.append("province_code_not_found")

    birth_year = data.get("birth_year")
    if isinstance(birth_year, int) and birth_year > date.today().year:
        warnings.append("birth_year_in_future")
        is_plausible = False

    return (
        jsonify(
            {
                "success": True,
                "data": data,
                "is_valid_format": True,
                "is_plausible": is_plausible,
                "province_version": version,
                "warnings": warnings,
            }
        ),
        200,
    )


