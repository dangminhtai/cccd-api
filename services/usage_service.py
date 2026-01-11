"""
Usage Service - Query usage statistics từ request_logs
"""
from __future__ import annotations

from datetime import datetime, timedelta
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


def get_user_usage_stats(user_id: int, days: int = 30) -> dict:
    """
    Lấy usage statistics của user từ request_logs
    
    Returns:
        {
            "total_requests": int,
            "success_requests": int,
            "error_requests": int,
            "avg_response_time_ms": float,
            "daily_stats": [
                {"date": "2024-01-01", "count": 100, "success": 95, "error": 5}
            ],
            "status_code_breakdown": {
                "200": 1000,
                "400": 50,
                "401": 10,
                "500": 5
            }
        }
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Get all API keys của user
                cursor.execute(
                    "SELECT id FROM api_keys WHERE user_id = %s",
                    (user_id,),
                )
                key_ids = [row["id"] for row in cursor.fetchall()]
                
                if not key_ids:
                    return {
                        "total_requests": 0,
                        "success_requests": 0,
                        "error_requests": 0,
                        "avg_response_time_ms": 0,
                        "daily_stats": [],
                        "status_code_breakdown": {},
                    }
                
                # Query request_logs cho các keys của user
                placeholders = ",".join(["%s"] * len(key_ids))
                
                # Daily stats
                cursor.execute(
                    f"""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as count,
                        SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as success,
                        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error
                    FROM request_logs
                    WHERE api_key_id IN ({placeholders})
                    AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    """,
                    key_ids + [days],
                )
                daily_rows = cursor.fetchall()
                
                # Total stats
                cursor.execute(
                    f"""
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as success_requests,
                        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_requests,
                        AVG(response_time_ms) as avg_response_time_ms
                    FROM request_logs
                    WHERE api_key_id IN ({placeholders})
                    AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    """,
                    key_ids + [days],
                )
                total_row = cursor.fetchone()
                
                # Status code breakdown
                cursor.execute(
                    f"""
                    SELECT 
                        status_code,
                        COUNT(*) as count
                    FROM request_logs
                    WHERE api_key_id IN ({placeholders})
                    AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    GROUP BY status_code
                    ORDER BY status_code
                    """,
                    key_ids + [days],
                )
                status_rows = cursor.fetchall()
                
        finally:
            conn.close()
        
        # Format results
        daily_stats = [
            {
                "date": str(row["date"]),
                "count": row["count"],
                "success": row["success"] or 0,
                "error": row["error"] or 0,
            }
            for row in daily_rows
        ]
        
        status_code_breakdown = {
            str(row["status_code"]): row["count"]
            for row in status_rows
        }
        
        return {
            "total_requests": total_row["total_requests"] or 0,
            "success_requests": total_row["success_requests"] or 0,
            "error_requests": total_row["error_requests"] or 0,
            "avg_response_time_ms": float(total_row["avg_response_time_ms"] or 0),
            "daily_stats": daily_stats,
            "status_code_breakdown": status_code_breakdown,
        }
    except Exception as e:
        # Return empty stats on error
        return {
            "total_requests": 0,
            "success_requests": 0,
            "error_requests": 0,
            "avg_response_time_ms": 0,
            "daily_stats": [],
            "status_code_breakdown": {},
            "error": str(e),
        }


def get_usage_stats_by_key(user_id: int, days: int = 30) -> list[dict]:
    """
    Lấy usage statistics theo từng API key của user
    
    Returns:
        [
            {
                "key_id": int,
                "key_prefix": str,
                "tier": str,
                "label": str | None,
                "total_requests": int,
                "success_requests": int,
                "error_requests": int,
                "avg_response_time_ms": float,
                "daily_stats": [
                    {"date": "2024-01-01", "count": 100, "success": 95, "error": 5}
                ]
            },
            ...
        ]
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Get all API keys của user với prefix và tier
                cursor.execute(
                    """
                    SELECT 
                        ak.id,
                        ak.key_prefix,
                        ak.tier,
                        ak.label
                    FROM api_keys ak
                    WHERE ak.user_id = %s AND ak.active = 1
                    ORDER BY ak.created_at DESC
                    """,
                    (user_id,),
                )
                keys = cursor.fetchall()
                
                if not keys:
                    return []
                
                result = []
                for key in keys:
                    key_id = key["id"]
                    
                    # Daily stats for this key
                    cursor.execute(
                        """
                        SELECT 
                            DATE(created_at) as date,
                            COUNT(*) as count,
                            SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as success,
                            SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error
                        FROM request_logs
                        WHERE api_key_id = %s
                        AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                        GROUP BY DATE(created_at)
                        ORDER BY date DESC
                        """,
                        (key_id, days),
                    )
                    daily_rows = cursor.fetchall()
                    
                    # Total stats for this key
                    cursor.execute(
                        """
                        SELECT 
                            COUNT(*) as total_requests,
                            SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as success_requests,
                            SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_requests,
                            AVG(response_time_ms) as avg_response_time_ms
                        FROM request_logs
                        WHERE api_key_id = %s
                        AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                        """,
                        (key_id, days),
                    )
                    total_row = cursor.fetchone()
                    
                    daily_stats = [
                        {
                            "date": str(row["date"]),
                            "count": row["count"],
                            "success": row["success"] or 0,
                            "error": row["error"] or 0,
                        }
                        for row in daily_rows
                    ]
                    
                    result.append({
                        "key_id": key_id,
                        "key_prefix": key["key_prefix"],
                        "tier": key["tier"],
                        "label": key["label"],
                        "total_requests": total_row["total_requests"] or 0,
                        "success_requests": total_row["success_requests"] or 0,
                        "error_requests": total_row["error_requests"] or 0,
                        "avg_response_time_ms": float(total_row["avg_response_time_ms"] or 0),
                        "daily_stats": daily_stats,
                    })
                
        finally:
            conn.close()
        
        return result
    except Exception as e:
        return []
