from __future__ import annotations

import time
from datetime import date

from flask import Blueprint, current_app, g, jsonify, render_template, request

from services.cccd_parser import parse_cccd
from services.province_mapping import ProvinceVersion, map_province_name
from app import limiter

cccd_bp = Blueprint("cccd", __name__)


def _get_request_id() -> str:
    return g.get("request_id", "-")


def _mask_cccd(cccd: str) -> str:
    if len(cccd) <= 4:
        return "*" * len(cccd)
    return f"{cccd[:3]}******{cccd[-3:]}"


def _log_to_database_if_enabled(
    request_id: str,
    api_key_id: int | None = None,
    api_key_prefix: str | None = None,
    ip_address: str | None = None,
    method: str = "POST",
    endpoint: str = "/v1/cccd/parse",
    status_code: int = 200,
    response_time_ms: int | None = None,
    cccd_masked: str | None = None,
    province_code: str | None = None,
    province_version: str | None = None,
    is_valid_format: bool | None = None,
    is_plausible: bool | None = None,
    error_message: str | None = None,
) -> None:
    """
    Log request vào database nếu API_KEY_MODE=tiered
    Chỉ log khi tiered mode (có MySQL connection)
    """
    try:
        settings = current_app.config.get("SETTINGS")
        api_key_mode = getattr(settings, "api_key_mode", "simple")
        
        # Chỉ log khi tiered mode (có MySQL)
        if api_key_mode == "tiered":
            from services.logging_service import log_request_to_database
            
            log_request_to_database(
                request_id=request_id,
                api_key_id=api_key_id,
                api_key_prefix=api_key_prefix,
                ip_address=ip_address,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                response_time_ms=response_time_ms,
                cccd_masked=cccd_masked,
                province_code=province_code,
                province_version=province_version,
                is_valid_format=is_valid_format,
                is_plausible=is_plausible,
                error_message=error_message,
            )
    except Exception as e:
        # Không throw exception để không làm gián đoạn request
        # Chỉ log warning vào Flask logger
        current_app.logger.warning(f"Failed to log to database: {e}")


@cccd_bp.route("/v1/cccd/parse", methods=["OPTIONS"])
@limiter.exempt  # Exempt OPTIONS from rate limiting
def cccd_parse_options():
    """Reject OPTIONS method - only POST is allowed"""
    return jsonify({"error": "Method not allowed"}), 405




def _check_api_key():
    """
    Kiểm tra API key theo mode (simple hoặc tiered)
    Returns: (is_valid, error_response, key_info)
    """
    settings = current_app.config.get("SETTINGS")
    api_key_mode = getattr(settings, "api_key_mode", "simple")
    provided_api_key = request.headers.get("X-API-Key")
    
    # Debug log
    current_app.logger.debug(
        f"api_key_check | mode={api_key_mode} | "
        f"provided_key_length={len(provided_api_key) if provided_api_key else 0}"
    )
    
    if api_key_mode == "tiered":
        # Tiered mode: validate với MySQL
        from services.api_key_service import validate_api_key, log_request
        is_valid, error_msg, key_info = validate_api_key(provided_api_key)
        if not is_valid:
            current_app.logger.warning(
                f"api_key_check_failed | mode=tiered | reason={error_msg}"
            )
            return False, (
                jsonify({
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": error_msg,
                }),
                401,
            ), None
        # Log usage
        log_request(provided_api_key)
        return True, None, key_info
    else:
        # Simple mode: so sánh với API_KEY trong .env
        required_api_key = getattr(settings, "api_key", None)
        if required_api_key:
            if not provided_api_key:
                current_app.logger.warning(
                    f"api_key_check_failed | mode=simple | reason=missing_key"
                )
                return False, (
                    jsonify({
                        "success": False,
                        "is_valid_format": False,
                        "data": None,
                        "message": "API key không hợp lệ hoặc thiếu.",
                    }),
                    401,
                ), None
            if provided_api_key != required_api_key:
                current_app.logger.warning(
                    f"api_key_check_failed | mode=simple | "
                    f"provided_length={len(provided_api_key)} | "
                    f"required_length={len(required_api_key)}"
                )
                return False, (
                    jsonify({
                        "success": False,
                        "is_valid_format": False,
                        "data": None,
                        "message": "API key không hợp lệ hoặc thiếu.",
                    }),
                    401,
                ), None
        return True, None, None


def _get_rate_limit():
    """Lấy rate limit động theo tier của API key"""
    settings = current_app.config.get("SETTINGS")
    api_key_mode = getattr(settings, "api_key_mode", "simple")
    
    if api_key_mode == "tiered":
        provided_api_key = request.headers.get("X-API-Key")
        if provided_api_key:
            from services.api_key_service import get_rate_limit_for_key
            return get_rate_limit_for_key(provided_api_key)
    
    # Default cho simple mode hoặc không có key
    return "30 per minute"


@cccd_bp.route("/v1/cccd/parse", methods=["POST"])
@limiter.limit(_get_rate_limit)
def cccd_parse():
    # Start timing for response time measurement
    start_time = time.time()
    
    payload = request.get_json(silent=True) or {}
    cccd = payload.get("cccd")
    province_version = payload.get("province_version")
    
    # Get request info for logging
    req_id = _get_request_id()
    ip_address = request.remote_addr
    api_key_header = request.headers.get("X-API-Key")
    api_key_id = None
    api_key_prefix = None
    status_code = 200
    error_msg = None
    cccd_masked = None
    province_code = None
    province_version_used = None
    is_valid_format = None
    is_plausible = None

    # API Key check
    is_valid, error_response, key_info = _check_api_key()
    if not is_valid:
        current_app.logger.warning(
            f"auth_failed | request_id={req_id} | reason=invalid_or_missing_api_key"
        )
        # Extract status code from error response
        if error_response and isinstance(error_response, tuple):
            status_code = error_response[1] if len(error_response) > 1 else 401
            if isinstance(error_response[0], dict) and "message" in error_response[0]:
                error_msg = error_response[0]["message"]
        else:
            status_code = 401
            error_msg = "API key không hợp lệ hoặc thiếu."
        
        # Log to database if tiered mode
        _log_to_database_if_enabled(
            request_id=req_id,
            api_key_id=None,
            api_key_prefix=api_key_header[:8] if api_key_header else None,
            ip_address=ip_address,
            method="POST",
            endpoint="/v1/cccd/parse",
            status_code=status_code,
            response_time_ms=int((time.time() - start_time) * 1000),
            error_message=error_msg,
        )
        
        return error_response
    
    # Get API key info for logging
    if key_info:
        api_key_id = key_info.id
        api_key_prefix = key_info.key_prefix

    # Basic validate (align with requirement.md)
    if cccd is None:
        current_app.logger.warning(f"validation_failed | request_id={req_id} | reason=missing_cccd")
        status_code = 400
        error_msg = "Thiếu trường cccd."
        is_valid_format = False
        
        # Log to database
        _log_to_database_if_enabled(
            request_id=req_id,
            api_key_id=api_key_id,
            api_key_prefix=api_key_prefix,
            ip_address=ip_address,
            method="POST",
            endpoint="/v1/cccd/parse",
            status_code=status_code,
            response_time_ms=int((time.time() - start_time) * 1000),
            is_valid_format=is_valid_format,
            error_message=error_msg,
        )
        
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
        current_app.logger.warning(f"validation_failed | request_id={req_id} | reason=cccd_not_string")
        status_code = 400
        error_msg = "CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."
        is_valid_format = False
        
        _log_to_database_if_enabled(
            request_id=req_id,
            api_key_id=api_key_id,
            api_key_prefix=api_key_prefix,
            ip_address=ip_address,
            method="POST",
            endpoint="/v1/cccd/parse",
            status_code=status_code,
            response_time_ms=int((time.time() - start_time) * 1000),
            is_valid_format=is_valid_format,
            error_message=error_msg,
        )
        
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

    # Early length check to prevent DoS (reject before processing long strings)
    if len(cccd) > 20:  # 12 digits + buffer for whitespace
        current_app.logger.warning(
            f"validation_failed | request_id={req_id} | reason=cccd_too_long | length={len(cccd)}"
        )
        status_code = 400
        error_msg = "CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."
        is_valid_format = False
        
        _log_to_database_if_enabled(
            request_id=req_id,
            api_key_id=api_key_id,
            api_key_prefix=api_key_prefix,
            ip_address=ip_address,
            method="POST",
            endpoint="/v1/cccd/parse",
            status_code=status_code,
            response_time_ms=int((time.time() - start_time) * 1000),
            is_valid_format=is_valid_format,
            error_message=error_msg,
        )
        
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
        current_app.logger.warning(
            f"validation_failed | request_id={req_id} | reason=invalid_cccd_format | length={len(cccd)}"
        )
        status_code = 400
        error_msg = "CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."
        is_valid_format = False
        
        _log_to_database_if_enabled(
            request_id=req_id,
            api_key_id=api_key_id,
            api_key_prefix=api_key_prefix,
            ip_address=ip_address,
            method="POST",
            endpoint="/v1/cccd/parse",
            status_code=status_code,
            response_time_ms=int((time.time() - start_time) * 1000),
            cccd_masked=_mask_cccd(cccd) if cccd else None,
            is_valid_format=is_valid_format,
            error_message=error_msg,
        )
        
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
    masked = _mask_cccd(cccd)

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
        current_app.logger.warning(
            f"validation_failed | request_id={req_id} | reason=invalid_province_version | value={province_version}"
        )
        status_code = 400
        error_msg = "province_version không hợp lệ (chỉ nhận legacy_63 hoặc current_34)."
        is_valid_format = False
        
        _log_to_database_if_enabled(
            request_id=req_id,
            api_key_id=api_key_id,
            api_key_prefix=api_key_prefix,
            ip_address=ip_address,
            method="POST",
            endpoint="/v1/cccd/parse",
            status_code=status_code,
            response_time_ms=int((time.time() - start_time) * 1000),
            cccd_masked=_mask_cccd(cccd) if cccd else None,
            is_valid_format=is_valid_format,
            error_message=error_msg,
        )
        
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

    current_app.logger.info(
        f"cccd_parsed | request_id={req_id} | cccd_masked={masked} | province_version={version} | warnings={warnings}"
    )
    
    # Prepare response data
    response_data = {
        "success": True,
        "data": data,
        "is_valid_format": True,
        "is_plausible": is_plausible,
        "province_version": version,
        "warnings": warnings if warnings else None,
    }
    
    # Log to database (success case)
    response_time_ms = int((time.time() - start_time) * 1000)
    _log_to_database_if_enabled(
        request_id=req_id,
        api_key_id=api_key_id,
        api_key_prefix=api_key_prefix,
        ip_address=ip_address,
        method="POST",
        endpoint="/v1/cccd/parse",
        status_code=200,
        response_time_ms=response_time_ms,
        cccd_masked=masked,
        province_code=data.get("province_code"),
        province_version=version,
        is_valid_format=True,
        is_plausible=is_plausible,
    )

    return (
        jsonify(response_data),
        200,
    )


