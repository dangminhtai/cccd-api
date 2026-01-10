# Rate Limits Documentation

Tài liệu chi tiết về rate limits và cách xử lý.

## Overview

API sử dụng rate limiting để đảm bảo chất lượng dịch vụ và bảo vệ server khỏi abuse. Rate limits được áp dụng theo tier của API key.

## Rate Limits by Tier

| Tier | Requests per Minute | Requests per Day | Description |
|------|---------------------|------------------|-------------|
| **Free** | 10 | 1,000 | Free tier, phù hợp cho testing và development |
| **Premium** | 100 | Unlimited | Premium tier, phù hợp cho production applications |
| **Ultra** | 1,000 | Unlimited | Ultra tier, phù hợp cho high-volume applications |

## Rate Limit Headers

Khi gọi API, response sẽ chứa các headers sau:

### `X-RateLimit-Remaining`
Số requests còn lại trong window hiện tại.

**Example:**
```
X-RateLimit-Remaining: 7
```

### `X-RateLimit-Reset`
Unix timestamp khi rate limit window reset.

**Example:**
```
X-RateLimit-Reset: 1704931200
```

### `Retry-After` (khi 429)
Số giây cần chờ trước khi retry.

**Example:**
```
Retry-After: 45
```

## Rate Limit Window

Rate limits được tính theo **sliding window** với độ dài **1 minute**.

Ví dụ:
- 10:00:00 - Request 1 (remaining: 9)
- 10:00:30 - Request 2 (remaining: 8)
- 10:01:00 - Request 3 (remaining: 7, window reset at 10:02:00)
- 10:01:30 - Request 4 (remaining: 6)
- ...
- 10:02:00 - Window reset, remaining: 10

## Handling Rate Limits

### Check Headers

Luôn kiểm tra `X-RateLimit-Remaining` để biết còn bao nhiêu requests:

```python
import requests

response = requests.post(url, json=data, headers=headers)
remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

if remaining < 5:
    print(f"Warning: Only {remaining} requests remaining")
    print(f"Window resets at: {reset_time}")
```

### Handle 429 Errors

Khi nhận 429 error, đợi theo `Retry-After` header:

```python
from cccd_api import CCCDRateLimitError
import time

try:
    result = api.parse("079203012345")
except CCCDRateLimitError as e:
    # Get Retry-After from response headers
    retry_after = int(response.headers.get('Retry-After', 60))
    print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
    time.sleep(retry_after)
    result = api.parse("079203012345")
```

### Exponential Backoff

Implement exponential backoff cho retry:

```python
import time
import random

def parse_with_backoff(api, cccd, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api.parse(cccd)
        except CCCDRateLimitError:
            if attempt < max_retries - 1:
                # Exponential backoff: 2^attempt seconds + jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                raise
```

## Best Practices

### 1. Monitor Rate Limit Headers

Luôn check `X-RateLimit-Remaining` để tránh hit limit:

```python
def safe_parse(api, cccd):
    # Check remaining before request
    response = api._session.post(...)  # Internal method
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    
    if remaining == 0:
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        wait_time = reset_time - int(time.time())
        if wait_time > 0:
            print(f"Rate limit reached. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    return api.parse(cccd)
```

### 2. Batch Requests

Nếu cần parse nhiều CCCD, batch requests để tránh rate limit:

```python
def parse_batch(api, cccd_list, delay=0.1):
    results = []
    for cccd in cccd_list:
        try:
            result = api.parse(cccd)
            results.append(result)
            # Small delay between requests
            time.sleep(delay)
        except CCCDRateLimitError:
            # Wait for rate limit window
            time.sleep(60)
            result = api.parse(cccd)
            results.append(result)
    return results
```

### 3. Queue System

Sử dụng queue system để quản lý requests:

```python
import queue
import threading

class CCCDQueue:
    def __init__(self, api, max_requests_per_minute=10):
        self.api = api
        self.queue = queue.Queue()
        self.max_requests = max_requests_per_minute
        self.request_times = []
    
    def add_request(self, cccd):
        self.queue.put(cccd)
    
    def process_queue(self):
        while True:
            cccd = self.queue.get()
            # Check rate limit
            now = time.time()
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            if len(self.request_times) >= self.max_requests:
                # Wait until oldest request is 60 seconds old
                wait_time = 60 - (now - self.request_times[0])
                if wait_time > 0:
                    time.sleep(wait_time)
            
            # Make request
            result = self.api.parse(cccd)
            self.request_times.append(time.time())
            self.queue.task_done()
```

### 4. Upgrade Tier

Nếu thường xuyên hit rate limit, cân nhắc upgrade tier:

- **Free → Premium**: 10x increase (10 → 100 requests/min)
- **Premium → Ultra**: 10x increase (100 → 1,000 requests/min)

## Testing Rate Limits

Test rate limits với script sau:

```python
import time
from cccd_api import CCCDRateLimitError

api = CCCDAPI(api_key="your-api-key")

# Test rate limit
start_time = time.time()
requests_made = 0

for i in range(20):  # Try to make 20 requests
    try:
        result = api.parse("079203012345")
        requests_made += 1
        print(f"Request {i+1}: Success")
    except CCCDRateLimitError as e:
        print(f"Request {i+1}: Rate limited - {e}")
        break
    except Exception as e:
        print(f"Request {i+1}: Error - {e}")
        break
    time.sleep(0.1)  # Small delay

elapsed = time.time() - start_time
print(f"\nMade {requests_made} requests in {elapsed:.2f} seconds")
print(f"Rate: {requests_made / elapsed * 60:.2f} requests/minute")
```

## FAQ

### Q: Rate limit được tính như thế nào?
A: Rate limit được tính theo sliding window 1 phút. Ví dụ: nếu limit là 10/min, bạn có thể gửi 10 requests bất kỳ trong 60 giây bất kỳ.

### Q: Làm sao biết còn bao nhiêu requests?
A: Check header `X-RateLimit-Remaining` trong response.

### Q: Khi nào rate limit window reset?
A: Window reset liên tục theo sliding window. Check header `X-RateLimit-Reset` để biết timestamp reset.

### Q: Có thể request reset rate limit không?
A: Không. Rate limit được tự động reset theo sliding window.

### Q: Rate limit có áp dụng cho health check không?
A: Không. Endpoint `/health` không bị rate limit.

## Support

Nếu cần hỗ trợ về rate limits, vui lòng liên hệ support@cccd-api.com.
