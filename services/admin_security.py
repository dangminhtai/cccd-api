"""
Admin Security Service - Chống brute force attack
"""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

# In-memory storage cho failed attempts (trong production nên dùng Redis)
# Format: {ip_address: [(timestamp, endpoint), ...]}
_failed_attempts: Dict[str, list] = defaultdict(list)

# IP blocking: {ip_address: unblock_timestamp}
_blocked_ips: Dict[str, float] = {}

# Configuration
MAX_FAILED_ATTEMPTS = 5  # Số lần thử sai tối đa
BLOCK_DURATION_SECONDS = 300  # Block 5 phút sau khi vượt quá limit
WINDOW_SECONDS = 60  # Time window để đếm failed attempts (60 giây)
CLEANUP_INTERVAL = 3600  # Cleanup old records mỗi 1 giờ
_last_cleanup = time.time()


def record_failed_attempt(ip_address: str, endpoint: str) -> None:
    """
    Ghi lại failed attempt từ một IP
    
    Args:
        ip_address: IP address của request
        endpoint: Endpoint bị failed
    """
    global _last_cleanup
    
    current_time = time.time()
    
    # Cleanup old records định kỳ
    if current_time - _last_cleanup > CLEANUP_INTERVAL:
        _cleanup_old_records(current_time)
        _last_cleanup = current_time
    
    # Thêm failed attempt
    _failed_attempts[ip_address].append((current_time, endpoint))
    
    # Kiểm tra xem có vượt quá limit không
    recent_attempts = [
        ts for ts, ep in _failed_attempts[ip_address]
        if current_time - ts <= WINDOW_SECONDS
    ]
    
    if len(recent_attempts) >= MAX_FAILED_ATTEMPTS:
        # Block IP này
        _blocked_ips[ip_address] = current_time + BLOCK_DURATION_SECONDS


def is_ip_blocked(ip_address: str) -> Tuple[bool, float | None]:
    """
    Kiểm tra xem IP có bị block không
    
    Args:
        ip_address: IP address cần kiểm tra
        
    Returns:
        Tuple (is_blocked, unblock_timestamp)
    """
    if ip_address not in _blocked_ips:
        return False, None
    
    unblock_time = _blocked_ips[ip_address]
    current_time = time.time()
    
    if current_time >= unblock_time:
        # Hết thời gian block, xóa khỏi danh sách
        del _blocked_ips[ip_address]
        return False, None
    
    return True, unblock_time


def get_failed_attempts_count(ip_address: str, window_seconds: int = WINDOW_SECONDS) -> int:
    """
    Đếm số failed attempts trong time window
    
    Args:
        ip_address: IP address
        window_seconds: Time window (mặc định 60 giây)
        
    Returns:
        Số failed attempts trong window
    """
    if ip_address not in _failed_attempts:
        return 0
    
    current_time = time.time()
    recent_attempts = [
        ts for ts, ep in _failed_attempts[ip_address]
        if current_time - ts <= window_seconds
    ]
    
    return len(recent_attempts)


def _cleanup_old_records(current_time: float) -> None:
    """Xóa các records cũ hơn WINDOW_SECONDS"""
    global _failed_attempts, _blocked_ips
    
    # Cleanup failed attempts
    for ip in list(_failed_attempts.keys()):
        _failed_attempts[ip] = [
            (ts, ep) for ts, ep in _failed_attempts[ip]
            if current_time - ts <= WINDOW_SECONDS
        ]
        if not _failed_attempts[ip]:
            del _failed_attempts[ip]
    
    # Cleanup blocked IPs đã hết hạn
    for ip in list(_blocked_ips.keys()):
        if current_time >= _blocked_ips[ip]:
            del _blocked_ips[ip]


def get_security_stats() -> Dict:
    """
    Lấy thống kê security (cho admin monitoring)
    
    Returns:
        Dict với thông tin về blocked IPs và failed attempts
    """
    current_time = time.time()
    
    # Đếm số IP đang bị block
    active_blocks = sum(
        1 for unblock_time in _blocked_ips.values()
        if current_time < unblock_time
    )
    
    # Đếm tổng số failed attempts trong window
    total_failed = sum(
        len([ts for ts, ep in attempts if current_time - ts <= WINDOW_SECONDS])
        for attempts in _failed_attempts.values()
    )
    
    return {
        "blocked_ips_count": active_blocks,
        "total_failed_attempts": total_failed,
        "unique_ips_with_failures": len(_failed_attempts),
    }
