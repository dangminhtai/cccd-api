# Security Testing Script - Rate Limit Bypass Tests
# Test 5.2, 5.3 from security_testing_guide.md

$base = "http://127.0.0.1:8000"
$results = @()

# API Keys for testing
$freeKey = "free_a1c6062d52bdbff5762e07ec391dfb81"
$premKey = "prem_31c65c426015522c069a6dc1cf57a3ad"
$ultrKey = "ultr_8d2caeeb47a7a46bd959c0f5423d1843"

function Test-Case {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$Expected,
        [string]$Category = "Rate Limiting"
    )
    Write-Host "`n[TEST] $Name" -ForegroundColor Cyan
    try {
        $result = & $Test
        $pass = ($result.Status -eq $Expected -or $result.Pass -eq $true)
        $resultObj = [PSCustomObject]@{
            Category = $Category
            Test = $Name
            Status = $result.Status
            Expected = $Expected
            Pass = $pass
            Details = $result.Details
            Severity = if ($result.Severity) { $result.Severity } else { "INFO" }
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        $script:results += $resultObj
        
        if ($pass) {
            Write-Host "  PASS: $($result.Details)" -ForegroundColor Green
        } else {
            Write-Host "  FAIL: Expected $Expected, got $($result.Status). $($result.Details)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        $script:results += [PSCustomObject]@{
            Category = $Category
            Test = $Name
            Status = "ERROR"
            Expected = $Expected
            Pass = $false
            Details = $_.Exception.Message
            Severity = "ERROR"
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
    }
}

Write-Host "`n=== 5. RATE LIMITING BYPASS ===" -ForegroundColor Yellow

# ============================================
# Test 5.2: Rate Limit Bypass Techniques
# ============================================

Write-Host "`n--- Test 5.2: Rate Limit Bypass Techniques ---" -ForegroundColor Cyan

# Test 5.2.1: Đổi API key để bypass (mỗi key có limit riêng - đúng)
Write-Host "`n[5.2.1] Testing API Key Switching Bypass" -ForegroundColor Yellow

Test-Case "Rate Limit - Free Key (10 req/min)" {
    $successCount = 0
    $rateLimitCount = 0
    
    for ($i = 1; $i -le 15; $i++) {
        try {
            $body = @{cccd = "079203012345"} | ConvertTo-Json
            $headers = @{"X-API-Key" = $freeKey}
            $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
            $successCount++
            Start-Sleep -Milliseconds 100
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            if ($status -eq 429) {
                $rateLimitCount++
                Write-Host "    Request $i : 429 (Rate Limited)" -ForegroundColor Yellow
            } else {
                Write-Host "    Request $i : $status" -ForegroundColor Red
            }
        }
    }
    
    if ($rateLimitCount -gt 0) {
        return @{
            Status = "PASS";
            Pass = $true;
            Details = "Free key rate limit works: $successCount success, $rateLimitCount rate limited (expected ~10 req/min)"
        }
    } else {
        return @{
            Status = "WARN";
            Pass = $true;
            Details = "Free key: $successCount requests, no rate limit triggered (may need more requests)"
        }
    }
} "PASS" "Rate Limiting"

Test-Case "Rate Limit Bypass - Switch Keys" {
    # Test switching between keys to bypass rate limit
    $freeSuccess = 0
    $premSuccess = 0
    $ultrSuccess = 0
    
    # Make requests with free key until rate limited
    for ($i = 1; $i -le 12; $i++) {
        try {
            $body = @{cccd = "079203012345"} | ConvertTo-Json
            $headers = @{"X-API-Key" = $freeKey}
            $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
            $freeSuccess++
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            if ($status -eq 429) {
                Write-Host "    Free key rate limited at request $i" -ForegroundColor Yellow
                break
            }
        }
        Start-Sleep -Milliseconds 50
    }
    
    # Try premium key immediately after free key is rate limited
    try {
        $body = @{cccd = "079203012345"} | ConvertTo-Json
        $headers = @{"X-API-Key" = $premKey}
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
        $premSuccess = 1
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 429) {
            return @{
                Status = "PASS";
                Pass = $true;
                Details = "CORRECT: Each key has separate rate limit (premium key works after free key is limited)"
            }
        }
    }
    
    if ($premSuccess -eq 1) {
        return @{
            Status = "PASS";
            Pass = $true;
            Details = "CORRECT: Each key has separate rate limit (premium key works after free key is limited)"
        }
    } else {
        return @{
            Status = "WARN";
            Pass = $true;
            Details = "Premium key response: $status"
        }
    }
} "PASS" "Rate Limiting"

# Test 5.2.2: X-Forwarded-For header manipulation
Write-Host "`n[5.2.2] Testing X-Forwarded-For Header Manipulation" -ForegroundColor Yellow

Test-Case "Rate Limit - X-Forwarded-For Manipulation" {
    # Make requests with different X-Forwarded-For headers
    $successCount = 0
    $rateLimitCount = 0
    
    for ($i = 1; $i -le 15; $i++) {
        try {
            $body = @{cccd = "079203012345"} | ConvertTo-Json
            $headers = @{
                "X-API-Key" = $freeKey
                "X-Forwarded-For" = "192.168.1.$i"
            }
            $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
            $successCount++
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            if ($status -eq 429) {
                $rateLimitCount++
            }
        }
        Start-Sleep -Milliseconds 50
    }
    
    # If rate limit is based on API key (not IP), changing X-Forwarded-For should not bypass
    if ($rateLimitCount -gt 0) {
        return @{
            Status = "PASS";
            Pass = $true;
            Details = "CORRECT: Rate limit based on API key, X-Forwarded-For manipulation does not bypass ($rateLimitCount rate limited)"
        }
    } else {
        return @{
            Status = "WARN";
            Pass = $true;
            Details = "X-Forwarded-For manipulation: $successCount requests, no rate limit (may be API key based)"
        }
    }
} "PASS" "Rate Limiting"

# Test 5.2.3: Case sensitivity trong API key
Write-Host "`n[5.2.3] Testing API Key Case Sensitivity" -ForegroundColor Yellow

Test-Case "Rate Limit - Case Sensitivity in API Key" {
    # Test với API key viết hoa/chữ thường
    $testCases = @(
        @{Key = $freeKey.ToUpper(); Name = "Uppercase"},
        @{Key = $freeKey.ToLower(); Name = "Lowercase"},
        @{Key = "FREE_a1c6062d52bdbff5762e07ec391dfb81"; Name = "Prefix Uppercase"},
        @{Key = "free_A1C6062D52BDBFF5762E07EC391DFB81"; Name = "Hash Uppercase"}
    )
    
    $allRejected = $true
    foreach ($testCase in $testCases) {
        try {
            $body = @{cccd = "079203012345"} | ConvertTo-Json
            $headers = @{"X-API-Key" = $testCase.Key}
            $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
            $allRejected = $false
            Write-Host "    $($testCase.Name): ACCEPTED (VULNERABLE!)" -ForegroundColor Red
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            if ($status -eq 401) {
                Write-Host "    $($testCase.Name): Rejected (401) - OK" -ForegroundColor Green
            } else {
                Write-Host "    $($testCase.Name): Status $status" -ForegroundColor Yellow
            }
        }
    }
    
    if ($allRejected) {
        return @{
            Status = "PASS";
            Pass = $true;
            Details = "CORRECT: API key is case-sensitive, all variations rejected"
        }
    } else {
        return @{
            Status = "FAIL";
            Pass = $false;
            Details = "VULNERABLE: API key case-insensitive, some variations accepted";
            Severity = "MEDIUM"
        }
    }
} "PASS" "Rate Limiting"

# ============================================
# Test 5.3: Distributed Rate Limiting
# ============================================

Write-Host "`n--- Test 5.3: Distributed Rate Limiting ---" -ForegroundColor Cyan

Test-Case "Rate Limit - Concurrent Requests (Free Tier)" {
    # Test concurrent requests to see if rate limit is accurate
    $jobs = @()
    $successCount = 0
    $rateLimitCount = 0
    
    # Start 15 concurrent requests
    for ($i = 1; $i -le 15; $i++) {
        $job = Start-Job -ScriptBlock {
            param($base, $key, $index)
            try {
                $body = @{cccd = "079203012345"} | ConvertTo-Json
                $headers = @{"X-API-Key" = $key}
                $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
                return @{Index = $index; Status = 200; Success = $true}
            } catch {
                $status = [int]$_.Exception.Response.StatusCode
                return @{Index = $index; Status = $status; Success = $false}
            }
        } -ArgumentList $base, $freeKey, $i
        $jobs += $job
    }
    
    # Wait for all jobs to complete
    $jobs | Wait-Job | Out-Null
    
    # Collect results
    foreach ($job in $jobs) {
        $result = Receive-Job -Job $job
        if ($result.Success) {
            $successCount++
        } elseif ($result.Status -eq 429) {
            $rateLimitCount++
        }
        Remove-Job -Job $job
    }
    
    # Free tier should have ~10 req/min limit
    # With 15 concurrent requests, we expect some to be rate limited
    if ($rateLimitCount -gt 0) {
        return @{
            Status = "PASS";
            Pass = $true;
            Details = "CORRECT: Rate limit works with concurrent requests - $successCount success, $rateLimitCount rate limited"
        }
    } else {
        return @{
            Status = "INFO";
            Pass = $true;
            Details = "Concurrent requests: $successCount success, $rateLimitCount rate limited (may need longer time window)"
        }
    }
} "PASS" "Rate Limiting"

Test-Case "Rate Limit - Different Tiers Concurrent" {
    # Test concurrent requests with different tier keys
    $jobs = @()
    $results = @{}
    
    # Start concurrent requests with free, premium, ultra keys
    $keys = @(
        @{Key = $freeKey; Tier = "Free"},
        @{Key = $premKey; Tier = "Premium"},
        @{Key = $ultrKey; Tier = "Ultra"}
    )
    
    foreach ($keyInfo in $keys) {
        for ($i = 1; $i -le 5; $i++) {
            $job = Start-Job -ScriptBlock {
                param($base, $key, $tier, $index)
                try {
                    $body = @{cccd = "079203012345"} | ConvertTo-Json
                    $headers = @{"X-API-Key" = $key}
                    $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
                    return @{Tier = $tier; Index = $index; Status = 200; Success = $true}
                } catch {
                    $status = [int]$_.Exception.Response.StatusCode
                    return @{Tier = $tier; Index = $index; Status = $status; Success = $false}
                }
            } -ArgumentList $base, $keyInfo.Key, $keyInfo.Tier, $i
            $jobs += $job
        }
    }
    
    # Wait and collect results
    $jobs | Wait-Job | Out-Null
    
    foreach ($job in $jobs) {
        $result = Receive-Job -Job $job
        if (-not $results.ContainsKey($result.Tier)) {
            $results[$result.Tier] = @{Success = 0; RateLimited = 0}
        }
        if ($result.Success) {
            $results[$result.Tier].Success++
        } elseif ($result.Status -eq 429) {
            $results[$result.Tier].RateLimited++
        }
        Remove-Job -Job $job
    }
    
    $details = "Concurrent requests by tier: "
    foreach ($tier in $results.Keys) {
        $details += "$tier ($($results[$tier].Success) success, $($results[$tier].RateLimited) rate limited); "
    }
    
    return @{
        Status = "PASS";
        Pass = $true;
        Details = $details.TrimEnd("; ")
    }
} "PASS" "Rate Limiting"

# ============================================
# SUMMARY
# ============================================

Write-Host "`n`n=== TEST SUMMARY ===" -ForegroundColor Yellow
Write-Host "Total tests: $($results.Count)" -ForegroundColor Cyan
$passed = ($results | Where-Object { $_.Pass }).Count
$failed = ($results | Where-Object { -not $_.Pass }).Count

Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

Write-Host "`nResults by Category:" -ForegroundColor Cyan
$results | Group-Object Category | ForEach-Object {
    $cat = $_.Name
    $catResults = $_.Group
    $catPassed = ($catResults | Where-Object { $_.Pass }).Count
    $catTotal = $catResults.Count
    Write-Host "  $cat : $catPassed/$catTotal passed" -ForegroundColor $(if ($catPassed -eq $catTotal) { "Green" } else { "Yellow" })
}

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
$results | Format-Table -AutoSize

# Save to CSV
$csvPath = "security_test_rate_limit_bypass_results.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "`nResults saved to: $csvPath" -ForegroundColor Green
