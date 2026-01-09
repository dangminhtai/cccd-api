# Test 12.3: Error Logs Leakage
# Kiểm tra xem error response có leak thông tin không

$baseUrl = "http://127.0.0.1:8000"
$apiKey = "free_49cc865e34f850d6d398d744b3ce2993"

Write-Host "=== Test 12.3: Error Logs Leakage ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Invalid CCCD format
Write-Host "Test 1: Invalid CCCD format ('invalid')" -ForegroundColor Yellow
$body1 = @{cccd = "invalid"} | ConvertTo-Json
try {
    $response1 = Invoke-WebRequest -Uri "$baseUrl/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=$apiKey} -Body ([System.Text.Encoding]::UTF8.GetBytes($body1)) -ErrorAction Stop
    Write-Host "Status Code: $($response1.StatusCode)" -ForegroundColor Green
    Write-Host "Response Body:" -ForegroundColor Green
    $response1.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
    $responseBody1 = $response1.Content
} catch {
    $statusCode1 = [int]$_.Exception.Response.StatusCode.value__
    $responseBody1 = $_.Exception.Response | ConvertTo-Json -Depth 10
    
    # Try to get response body
    try {
        $stream1 = $_.Exception.Response.GetResponseStream()
        $reader1 = New-Object System.IO.StreamReader($stream1, [System.Text.Encoding]::UTF8)
        $responseBody1 = $reader1.ReadToEnd()
        $reader1.Close()
        $stream1.Close()
    } catch {
        $responseBody1 = "Could not read response body"
    }
    
    Write-Host "Status Code: $statusCode1" -ForegroundColor $(if ($statusCode1 -eq 400) { "Green" } else { "Red" })
    Write-Host "Response Body:" -ForegroundColor Green
    try {
        $json1 = $responseBody1 | ConvertFrom-Json
        $json1 | ConvertTo-Json -Depth 5
    } catch {
        Write-Host $responseBody1
    }
    
    # Kiểm tra leak
    $leaks = @()
    if ($responseBody1 -match "stacktrace|traceback|Traceback") { $leaks += "Stacktrace" }
    if ($responseBody1 -match "File.*\.py|at.*line \d+") { $leaks += "File paths" }
    if ($responseBody1 -match "pymysql|MySQL|database|connection") { $leaks += "Database info" }
    if ($responseBody1 -match "password|credential|secret") { $leaks += "Credentials" }
    if ($responseBody1 -match "127\.0\.0\.1|localhost|internal") { $leaks += "Internal IPs" }
    
    if ($leaks.Count -gt 0) {
        Write-Host "`n❌ LEAK DETECTED: $($leaks -join ', ')" -ForegroundColor Red
    } else {
        Write-Host "`n✅ No leaks detected" -ForegroundColor Green
    }
}

Write-Host "`n" + ("="*60) + "`n"

# Test 2: Missing CCCD
Write-Host "Test 2: Missing CCCD (empty body)" -ForegroundColor Yellow
$body2 = '{}'
try {
    $response2 = Invoke-RestMethod -Uri "$baseUrl/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=$apiKey} -Body $body2 -ErrorAction Stop
    Write-Host "Response:" -ForegroundColor Green
    $response2 | ConvertTo-Json -Depth 5
} catch {
    $statusCode2 = [int]$_.Exception.Response.StatusCode.value__
    $stream2 = $_.Exception.Response.GetResponseStream()
    $reader2 = New-Object System.IO.StreamReader($stream2, [System.Text.Encoding]::UTF8)
    $responseBody2 = $reader2.ReadToEnd()
    $reader2.Close()
    $stream2.Close()
    
    Write-Host "Status Code: $statusCode2" -ForegroundColor $(if ($statusCode2 -eq 400) { "Green" } else { "Red" })
    Write-Host "Response Body:" -ForegroundColor Green
    try {
        $json2 = $responseBody2 | ConvertFrom-Json
        $json2 | ConvertTo-Json -Depth 5
    } catch {
        Write-Host $responseBody2
    }
    
    # Kiểm tra leak
    $leaks2 = @()
    if ($responseBody2 -match "stacktrace|traceback|Traceback") { $leaks2 += "Stacktrace" }
    if ($responseBody2 -match "File.*\.py|at.*line \d+") { $leaks2 += "File paths" }
    if ($responseBody2 -match "pymysql|MySQL|database|connection") { $leaks2 += "Database info" }
    if ($responseBody2 -match "password|credential|secret") { $leaks2 += "Credentials" }
    if ($responseBody2 -match "127\.0\.0\.1|localhost|internal") { $leaks2 += "Internal IPs" }
    
    if ($leaks2.Count -gt 0) {
        Write-Host "`n❌ LEAK DETECTED: $($leaks2 -join ', ')" -ForegroundColor Red
    } else {
        Write-Host "`n✅ No leaks detected" -ForegroundColor Green
    }
}

Write-Host "`n" + ("="*60) + "`n"

# Test 3: Wrong API Key
Write-Host "Test 3: Wrong API Key" -ForegroundColor Yellow
$body3 = @{cccd = "079203012345"} | ConvertTo-Json
try {
    $response3 = Invoke-RestMethod -Uri "$baseUrl/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="wrong_key_12345"} -Body $body3 -ErrorAction Stop
    Write-Host "Response:" -ForegroundColor Green
    $response3 | ConvertTo-Json -Depth 5
} catch {
    $statusCode3 = [int]$_.Exception.Response.StatusCode.value__
    $stream3 = $_.Exception.Response.GetResponseStream()
    $reader3 = New-Object System.IO.StreamReader($stream3, [System.Text.Encoding]::UTF8)
    $responseBody3 = $reader3.ReadToEnd()
    $reader3.Close()
    $stream3.Close()
    
    Write-Host "Status Code: $statusCode3" -ForegroundColor $(if ($statusCode3 -eq 401) { "Green" } else { "Red" })
    Write-Host "Response Body:" -ForegroundColor Green
    try {
        $json3 = $responseBody3 | ConvertFrom-Json
        $json3 | ConvertTo-Json -Depth 5
    } catch {
        Write-Host $responseBody3
    }
    
    # Kiểm tra leak
    $leaks3 = @()
    if ($responseBody3 -match "stacktrace|traceback|Traceback") { $leaks3 += "Stacktrace" }
    if ($responseBody3 -match "File.*\.py|at.*line \d+") { $leaks3 += "File paths" }
    if ($responseBody3 -match "pymysql|MySQL|database|connection") { $leaks3 += "Database info" }
    if ($responseBody3 -match "password|credential|secret") { $leaks3 += "Credentials" }
    if ($responseBody3 -match "127\.0\.0\.1|localhost|internal") { $leaks3 += "Internal IPs" }
    
    if ($leaks3.Count -gt 0) {
        Write-Host "`n❌ LEAK DETECTED: $($leaks3 -join ', ')" -ForegroundColor Red
    } else {
        Write-Host "`n✅ No leaks detected" -ForegroundColor Green
    }
}

Write-Host "`n" + ("="*60) + "`n"
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
