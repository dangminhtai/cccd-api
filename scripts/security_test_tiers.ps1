# Security Testing Script for CCCD API - Tier-based Rate Limiting
# Test với các API keys khác nhau theo tier config

$base = "http://127.0.0.1:8000"

# API Keys theo tier
$apiKeys = @{
    "free" = "free_63e33bbea29eba186d44a9eceac326c5"
    "premium" = "prem_76c84e97be127a255eeb9104d835a6e3"
    "ultra" = "ultr_d747a2117778a744cad6483773732316"
}

# Tier config từ database
$tierConfig = @{
    "free" = @{ per_minute = 10; per_day = 1000 }
    "premium" = @{ per_minute = 100; per_day = $null }  # unlimited
    "ultra" = @{ per_minute = 1000; per_day = $null }    # unlimited
}

$results = @()
$findings = @()

function Test-Case {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$Expected,
        [string]$Category = "General",
        [string]$Tier = ""
    )
    Write-Host "`n[TEST] $Name" -ForegroundColor Cyan
    if ($Tier) {
        Write-Host "  Tier: $Tier" -ForegroundColor Gray
    }
    try {
        $result = & $Test
        $pass = ($result.Status -eq $Expected)
        $resultObj = [PSCustomObject]@{
            Category = $Category
            Tier = $Tier
            Test = $Name
            Status = $result.Status
            Expected = $Expected
            Pass = $pass
            Details = $result.Details
            Severity = if ($result.Severity) { $result.Severity } else { "INFO" }
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        $global:results += $resultObj
        
        if ($pass) {
            Write-Host "  ✅ PASS: $($result.Details)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ FAIL: Expected $Expected, got $($result.Status). $($result.Details)" -ForegroundColor Red
            if ($result.Severity -eq "HIGH" -or $result.Severity -eq "CRITICAL") {
                $global:findings += [PSCustomObject]@{
                    Category = $Category
                    Tier = $Tier
                    Test = $Name
                    Severity = $result.Severity
                    Issue = $result.Details
                    Recommendation = $result.Recommendation
                }
            }
        }
    } catch {
        Write-Host "  ❌ ERROR: $_" -ForegroundColor Red
        $global:results += [PSCustomObject]@{
            Category = $Category
            Tier = $Tier
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

# ============================================
# RATE LIMITING TESTS BY TIER
# ============================================

Write-Host "`n=== RATE LIMITING TESTS BY TIER ===" -ForegroundColor Yellow

foreach ($tier in $apiKeys.Keys) {
    $apiKey = $apiKeys[$tier]
    $config = $tierConfig[$tier]
    $limitPerMin = $config.per_minute
    $limitPerDay = $config.per_day
    
    Write-Host "`n--- Testing $tier tier (Limit: $limitPerMin req/min" -ForegroundColor Cyan
    if ($limitPerDay) {
        Write-Host "  Daily limit: $limitPerDay req/day)" -ForegroundColor Gray
    } else {
        Write-Host "  Daily limit: unlimited)" -ForegroundColor Gray
    }
    
    # Test rate limit per minute
    $testName = "Rate Limit Test - $tier tier ($limitPerMin req/min)"
    Test-Case $testName {
        $body = @{cccd = "079203012345"} | ConvertTo-Json
        $headers = @{"X-API-Key" = $apiKey}
        $rateLimited = $false
        $first429At = $null
        
        # Gửi requests vượt limit (limit + 5)
        $testLimit = $limitPerMin + 5
        Write-Host "  Sending $testLimit requests..." -ForegroundColor Gray
        
        for ($i = 1; $i -le $testLimit; $i++) {
            try {
                $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $headers -Body $body -ErrorAction Stop
                # Chỉ log mỗi 50 requests cho ultra tier (1000 req/min)
                if ($tier -eq "ultra") {
                    if ($i % 50 -eq 0) {
                        Write-Host "    Request $i : 200 OK" -ForegroundColor Gray
                    }
                } elseif ($i % 10 -eq 0 -and $i -le $limitPerMin) {
                    Write-Host "    Request $i : 200 OK" -ForegroundColor Gray
                }
            } catch {
                $status = [int]$_.Exception.Response.StatusCode
                if ($status -eq 429) {
                    $rateLimited = $true
                    if ($null -eq $first429At) {
                        $first429At = $i
                    }
                    Write-Host "    Request $i : 429 Rate Limited" -ForegroundColor Yellow
                    # Break sau khi thấy 429 để không tốn quota
                    if ($i -gt $limitPerMin) {
                        break
                    }
                } elseif ($status -eq 401) {
                    return @{Status = 401; Details = "API key invalid"}
                }
            }
            # Delay nhỏ giữa các requests (ultra tier cần delay ngắn hơn)
            if ($tier -eq "ultra") {
                Start-Sleep -Milliseconds 10
            } else {
                Start-Sleep -Milliseconds 50
            }
        }
        
        if ($rateLimited) {
            if ($first429At -le ($limitPerMin + 2)) {
                return @{Status = 429; Details = "Rate limit working correctly (429 at request $first429At)"}
            } else {
                return @{
                    Status = 429; 
                    Details = "Rate limit triggered but late (429 at request $first429At, expected <= $($limitPerMin + 2))";
                    Severity = "MEDIUM";
                    Recommendation = "Check rate limiting configuration"
                }
            }
        } else {
            # Với ultra tier, có thể không trigger nếu test quá nhanh
            if ($tier -eq "ultra") {
                return @{
                    Status = 200; 
                    Details = "No rate limit detected (may be too fast - 1000 req/min is very high)";
                    Severity = "INFO";
                    Recommendation = "Test with longer time window or more requests"
                }
            } else {
                return @{
                    Status = 200; 
                    Details = "VULNERABLE! No rate limit detected after $testLimit requests";
                    Severity = "HIGH";
                    Recommendation = "Fix rate limiting for $tier tier"
                }
            }
        }
    } "429" "Rate Limiting" $tier
    
    # Đợi reset rate limit trước khi test tier tiếp theo
    Write-Host "  Waiting 5 seconds before next tier test..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}

# ============================================
# INPUT VALIDATION TESTS (với mỗi tier)
# ============================================

Write-Host "`n=== INPUT VALIDATION TESTS ===" -ForegroundColor Yellow

# Test với free tier (đủ cho validation tests)
$testKey = $apiKeys["free"]
$testHeaders = @{"X-API-Key" = $testKey}

Write-Host "  Using free tier key for validation tests..." -ForegroundColor Gray
Start-Sleep -Seconds 5  # Reset rate limit

Test-Case "SQL Injection in CCCD" {
    $body = @{cccd = "' OR '1'='1"} | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $testHeaders -Body $body -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! SQL injection accepted";
            Severity = "CRITICAL";
            Recommendation = "Validate input format strictly (digits only)"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 400) {
            return @{Status = $status; Details = "Correctly rejected (not digits)"}
        } else {
            return @{Status = $status; Details = "Unexpected status"}
        }
    }
} "400" "Input Validation" "free"

Test-Case "DoS - Very Long CCCD (10000 chars)" {
    $longCccd = "0" * 10000
    $body = @{cccd = $longCccd} | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $testHeaders -Body $body -TimeoutSec 5 -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! Very long input accepted (DoS risk)";
            Severity = "HIGH";
            Recommendation = "Add early length check (reject if > 20 chars)"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 400) {
            return @{Status = $status; Details = "Correctly rejected early"}
        } else {
            return @{Status = $status; Details = "Timeout or error"}
        }
    }
} "400" "DoS Protection" "free"

# ============================================
# AUTHENTICATION TESTS
# ============================================

Write-Host "`n=== AUTHENTICATION TESTS ===" -ForegroundColor Yellow

Test-Case "No API Key" {
    try {
        $body = @{cccd = "079203012345"} | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! No key required when it should be";
            Severity = "CRITICAL";
            Recommendation = "Ensure API key is checked before processing requests"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        return @{Status = $status; Details = "Correctly rejected"}
    }
} "401" "Authentication" ""

Test-Case "Wrong API Key" {
    try {
        $body = @{cccd = "079203012345"} | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="wrong_key_12345"} -Body $body -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! Wrong key accepted";
            Severity = "CRITICAL";
            Recommendation = "Fix API key validation"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        return @{Status = $status; Details = "Correctly rejected"}
    }
} "401" "Authentication" ""

# ============================================
# SUMMARY
# ============================================

Write-Host "`n`n=== TEST SUMMARY ===" -ForegroundColor Yellow
Write-Host "Total tests: $($results.Count)" -ForegroundColor Cyan
$passed = ($results | Where-Object { $_.Pass }).Count
$failed = ($results | Where-Object { -not $_.Pass }).Count

Write-Host "✅ Passed: $passed" -ForegroundColor Green
Write-Host "❌ Failed: $failed" -ForegroundColor Red

# Summary by tier
Write-Host "`nResults by Tier:" -ForegroundColor Cyan
$results | Where-Object { $_.Tier -ne "" } | Group-Object Tier | ForEach-Object {
    $tier = $_.Name
    $tierResults = $_.Group
    $tierPassed = ($tierResults | Where-Object { $_.Pass }).Count
    $tierTotal = $tierResults.Count
    Write-Host "  $tier : $tierPassed/$tierTotal passed" -ForegroundColor $(if ($tierPassed -eq $tierTotal) { "Green" } else { "Yellow" })
}

if ($findings.Count -gt 0) {
    Write-Host "`n=== SECURITY FINDINGS ===" -ForegroundColor Red
    $findings | Format-Table -AutoSize
}

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
$results | Format-Table -AutoSize

# Save to CSV
$csvPath = "security_test_results.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "`n✅ Results saved to: $csvPath" -ForegroundColor Green
Write-Host "   Total rows: $($results.Count)" -ForegroundColor Gray

if ($findings.Count -gt 0) {
    $findings | Export-Csv -Path "security_findings.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Security findings saved to: security_findings.csv" -ForegroundColor Yellow
}
