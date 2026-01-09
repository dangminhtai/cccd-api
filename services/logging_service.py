"""
Logging Service - Ghi log requests vào database
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pymysql


def _get_db_connection():
    """Tạo connection MySQL từ environment variables"""
    import os
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cccd_api"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def log_request_to_database(
    request_id: str,
    api_key_id: Optional[int] = None,
    api_key_prefix: Optional[str] = None,
    ip_address: Optional[str] = None,
    method: str = "POST",
    endpoint: str = "/v1/cccd/parse",
    status_code: int = 200,
    response_time_ms: Optional[int] = None,
    cccd_masked: Optional[str] = None,
    province_code: Optional[str] = None,
    province_version: Optional[str] = None,
    is_valid_format: Optional[bool] = None,
    is_plausible: Optional[bool] = None,
    error_message: Optional[str] = None,
) -> bool:
    """
    Ghi log request vào database
    
    Returns:
        True nếu thành công, False nếu có lỗi (không throw exception để không làm gián đoạn request)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO request_logs (
                        request_id, api_key_id, api_key_prefix, ip_address,
                        method, endpoint, status_code, response_time_ms,
                        cccd_masked, province_code, province_version,
                        is_valid_format, is_plausible, error_message,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    )
                    """,
                    (
                        request_id,
                        api_key_id,
                        api_key_prefix,
                        ip_address,
                        method,
                        endpoint,
                        status_code,
                        response_time_ms,
                        cccd_masked,
                        province_code,
                        province_version,
                        is_valid_format,
                        is_plausible,
                        error_message,
                    ),
                )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        # Log lỗi nhưng không throw để không làm gián đoạn request
        # Có thể log vào file hoặc print (không dùng Flask logger vì có thể gây circular import)
        print(f"Warning: Failed to log to database: {e}")
        return False
