from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, render_template, request

from services.cccd_parser import parse_cccd

cccd_bp = Blueprint("cccd", __name__)

@cccd_bp.get("/demo")
def demo():
    return render_template("demo.html")


@cccd_bp.post("/v1/cccd/parse")
def cccd_parse():
    payload = request.get_json(silent=True) or {}
    cccd = payload.get("cccd")

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
                "warnings": warnings,
            }
        ),
        200,
    )


