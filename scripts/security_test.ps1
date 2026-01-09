# Security Testing Script for CCCD API
# Chạy script này để test các lỗ hổng bảo mật

$base = "http://127.0.0.1:8000"
$testApiKey = "free_63e33bbea29eba186d44a9eceac326c5"  # Free tier API key
$results = @()
$findings = @()

function Test-Case {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$Expected,
        [string]$Category = "General"
    )
    Write-Host "`n[TEST] $Name" -ForegroundColor Cyan
    try {
        $result = & $Test
        $pass = ($result.Status -eq $Expected)
        $results += [PSCustomObject]@{
            Category = $Category
            Test = $Name
            Status = $result.Status
            Expected = $Expected
            Pass = $pass
            Details = $result.Details
            Severity = if ($result.Severity) { $result.Severity } else { "INFO" }
        }
        
        if ($pass) {
            Write-Host "  ✅ PASS: $($result.Details)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ FAIL: Expected $Expected, got $($result.Status). $($result.Details)" -ForegroundColor Red
            if ($result.Severity -eq "HIGH" -or $result.Severity -eq "CRITICAL") {
                $findings += [PSCustomObject]@{
                    Category = $Category
                    Test = $Name
                    Severity = $result.Severity
                    Issue = $result.Details
                    Recommendation = $result.Recommendation
                }
            }
        }
    } catch {
        Write-Host "  ❌ ERROR: $_" -ForegroundColor Red
        $results += [PSCustomObject]@{
            Category = $Category
            Test = $Name
            Status = "ERROR"
            Expected = $Expected
            Pass = $false
            Details = $_.Exception.Message
            Severity = "ERROR"
        }
    }
}

# Detect API key requirement
Write-Host "`n=== DETECTING API CONFIGURATION ===" -ForegroundColor Yellow
$apiKeyRequired = $false
try {
    $body = @{cccd = "079203012345"} | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
    $apiKeyRequired = $false
    Write-Host "  [INFO] API Key: NOT REQUIRED" -ForegroundColor Gray
} catch {
    $statusCode = $null
    if ($null -ne $_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
    }
    if ($statusCode -eq 401) {
        $apiKeyRequired = $true
        Write-Host "  [INFO] API Key: REQUIRED" -ForegroundColor Gray
    } else {
        Write-Host "  [WARN] Unexpected error: $statusCode" -ForegroundColor Yellow
    }
}

# ============================================
# 1. RECONNAISSANCE
# ============================================

Write-Host "`n=== 1. RECONNAISSANCE ===" -ForegroundColor Yellow

Test-Case "Health Check" {
    try {
        $r = Invoke-WebRequest -Uri "$base/health" -Method GET -ErrorAction Stop
        return @{Status = $r.StatusCode; Details = "Health endpoint accessible"}
    } catch {
        return @{Status = $_.Exception.Response.StatusCode.value__; Details = $_.Exception.Message}
    }
} "200" "Reconnaissance"

Test-Case "Root Endpoint" {
    try {
        $r = Invoke-WebRequest -Uri "$base/" -Method GET -ErrorAction Stop
        # Root endpoint returns 200 with info message - this is OK, not a vulnerability
        return @{Status = $r.StatusCode; Details = "Root endpoint returns info message (OK)"}
    } catch {
        return @{Status = $_.Exception.Response.StatusCode.value__; Details = "Not accessible"}
    }
} "200" "Reconnaissance"

Test-Case "Demo Page" {
    try {
        $r = Invoke-WebRequest -Uri "$base/demo" -Method GET -ErrorAction Stop
        return @{Status = $r.StatusCode; Details = "Demo page accessible"}
    } catch {
        return @{Status = $_.Exception.Response.StatusCode.value__; Details = $_.Exception.Message}
    }
} "200" "Reconnaissance"

# ============================================
# 2. AUTHENTICATION BYPASS
# ============================================

Write-Host "`n=== 2. AUTHENTICATION BYPASS ===" -ForegroundColor Yellow

if ($apiKeyRequired) {
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
    } "401" "Authentication"
    
    Test-Case "Empty API Key" {
        try {
            $body = @{cccd = "079203012345"} | ConvertTo-Json
            $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=""} -Body $body -ErrorAction Stop
            return @{
                Status = 200; 
                Details = "VULNERABLE! Empty key accepted";
                Severity = "HIGH";
                Recommendation = "Reject empty API keys explicitly"
            }
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            return @{Status = $status; Details = "Correctly rejected"}
        }
    } "401" "Authentication"
    
    Test-Case "SQL Injection in API Key" {
        try {
            $body = @{cccd = "079203012345"} | ConvertTo-Json
            $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="' OR '1'='1"} -Body $body -ErrorAction Stop
            return @{
                Status = 200; 
                Details = "VULNERABLE! SQL injection in API key";
                Severity = "CRITICAL";
                Recommendation = "Use parameterized queries or hash comparison for API keys"
            }
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            return @{Status = $status; Details = "Correctly rejected"}
        }
    } "401" "Authentication"
} else {
    Write-Host "  ⚠️  Skipping authentication tests - API key not required" -ForegroundColor Yellow
}

# ============================================
# 3. INPUT VALIDATION & INJECTION
# ============================================

Write-Host "`n=== 3. INPUT VALIDATION & INJECTION ===" -ForegroundColor Yellow

# Test with valid request (may need API key)
$testHeaders = @{}
if ($apiKeyRequired) {
    $testHeaders["X-API-Key"] = $testApiKey
    Write-Host "  [INFO] Using API key: $($testApiKey.Substring(0, 20))..." -ForegroundColor Gray
    Write-Host "  [INFO] Waiting 5 seconds to reset rate limit..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
} else {
    Write-Host "  ⚠️  Note: Some tests may fail with 401 if API key is required" -ForegroundColor Yellow
}

Test-Case "SQL Injection in CCCD" {
    try {
        $body = @{cccd = "' OR '1'='1"} | ConvertTo-Json
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
        } elseif ($status -eq 401) {
            return @{Status = $status; Details = "Rejected due to auth (test inconclusive)"}
        } else {
            return @{Status = $status; Details = "Unexpected status"}
        }
    }
} "400" "Input Validation"

Test-Case "XSS in CCCD" {
    try {
        $body = @{cccd = "<script>alert('XSS')</script>"} | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $testHeaders -Body $body -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! XSS payload accepted";
            Severity = "HIGH";
            Recommendation = "Validate input format strictly"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 400) {
            return @{Status = $status; Details = "Correctly rejected"}
        } elseif ($status -eq 401) {
            return @{Status = $status; Details = "Rejected due to auth (test inconclusive)"}
        } else {
            return @{Status = $status; Details = "Unexpected status"}
        }
    }
} "400" "Input Validation"

Test-Case "DoS - Very Long CCCD (10000 chars)" {
    try {
        $longCccd = "0" * 10000
        $body = @{cccd = $longCccd} | ConvertTo-Json
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
        } elseif ($status -eq 401) {
            return @{Status = $status; Details = "Rejected due to auth (test inconclusive)"}
        } else {
            return @{Status = $status; Details = "Timeout or error (may be DoS vulnerable)"}
        }
    }
} "400" "DoS Protection"

Test-Case "Type Confusion - Number instead of String" {
    try {
        $body = '{"cccd": 79203012345}'  # Number, not string
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $testHeaders -Body $body -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! Number type accepted";
            Severity = "MEDIUM";
            Recommendation = "Validate input type strictly (must be string)"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 400) {
            return @{Status = $status; Details = "Correctly rejected"}
        } elseif ($status -eq 401) {
            return @{Status = $status; Details = "Rejected due to auth (test inconclusive)"}
        } else {
            return @{Status = $status; Details = "Unexpected status"}
        }
    }
} "400" "Input Validation"

Test-Case "Path Traversal in Province Version" {
    try {
        $body = @{
            cccd = "079203012345"
            province_version = "../../../etc/passwd"
        } | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $testHeaders -Body $body -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! Path traversal worked";
            Severity = "CRITICAL";
            Recommendation = "Whitelist allowed province_version values"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 400) {
            return @{Status = $status; Details = "Correctly rejected"}
        } elseif ($status -eq 401) {
            return @{Status = $status; Details = "Rejected due to auth (test inconclusive)"}
        } else {
            return @{Status = $status; Details = "Unexpected status"}
        }
    }
} "400" "Input Validation"

# ============================================
# 4. RATE LIMITING
# ============================================

Write-Host "`n=== 4. RATE LIMITING ===" -ForegroundColor Yellow

Test-Case "Rate Limit Test (35 requests)" {
    $body = @{cccd = "079203012345"} | ConvertTo-Json
    $headers = @{}
    if ($apiKeyRequired) {
        $headers["X-API-Key"] = $testApiKey
    }
    $rateLimited = $false
    $lastStatus = 200
    
    for ($i = 1; $i -le 35; $i++) {
        try {
            $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $headers -Body $body -ErrorAction Stop
            $lastStatus = 200
            if ($i % 10 -eq 0) {
                Write-Host "  Request $i : 200 OK" -ForegroundColor Gray
            }
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            $lastStatus = $status
            if ($status -eq 429) {
                $rateLimited = $true
                Write-Host "  Request $i : 429 Rate Limited" -ForegroundColor Yellow
                break
            } elseif ($status -eq 401) {
                Write-Host "  Request $i : 401 (auth required, skipping rate limit test)" -ForegroundColor Yellow
                return @{Status = 401; Details = "Cannot test - API key required"}
            }
        }
        Start-Sleep -Milliseconds 50
    }
    
    if ($rateLimited) {
        return @{Status = 429; Details = "Rate limit working correctly"}
    } else {
        return @{
            Status = 200; 
            Details = "VULNERABLE! No rate limit detected after 35 requests";
            Severity = "MEDIUM";
            Recommendation = "Ensure rate limiting is properly configured"
        }
    }
} "429" "Rate Limiting"

# ============================================
# 5. INFORMATION DISCLOSURE
# ============================================

Write-Host "`n=== 5. INFORMATION DISCLOSURE ===" -ForegroundColor Yellow

Test-Case "Error Message Analysis" {
    # Wait longer to avoid rate limit from previous test
    Start-Sleep -Seconds 10
    try {
        $body = @{} | ConvertTo-Json  # Missing cccd
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $testHeaders -Body $body -ErrorAction Stop
        return @{Status = 200; Details = "Unexpected success"}
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        # If rate limited, skip this test
        if ($status -eq 429) {
            return @{Status = $status; Details = "Rate limited (test skipped)"}
        }
        
        $errorResponse = $_.Exception.Response
        $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        
        # Check for information leakage
        $leaked = $false
        $leakInfo = ""
        if ($responseBody -match "stacktrace|traceback|File.*\.py|pymysql|MySQL|database|password|secret|__init__|routes/") {
            $leaked = $true
            $leakInfo = "VULNERABLE! Information leaked: $($matches[0])"
        }
        
        if ($leaked) {
            return @{
                Status = $status; 
                Details = $leakInfo;
                Severity = "HIGH";
                Recommendation = "Ensure error messages are generic and don't expose internal details"
            }
        } else {
            return @{Status = $status; Details = "Error message is safe"}
        }
    }
} "400" "Information Disclosure"

Test-Case "Response Headers Check" {
    try {
        $r = Invoke-WebRequest -Uri "$base/health" -Method GET -ErrorAction Stop
        
        $leaked = $false
        $leakInfo = ""
        if ($r.Headers["Server"] -and $r.Headers["Server"] -match "Werkzeug|Flask") {
            $leaked = $true
            $leakInfo = "Server header leaks framework: $($r.Headers['Server'])"
        }
        if ($r.Headers["X-Powered-By"]) {
            $leaked = $true
            $leakInfo += " | X-Powered-By: $($r.Headers['X-Powered-By'])"
        }
        
        if ($leaked) {
            return @{
                Status = $r.StatusCode; 
                Details = $leakInfo;
                Severity = "LOW";
                Recommendation = "Remove or modify Server/X-Powered-By headers"
            }
        } else {
            return @{Status = $r.StatusCode; Details = "Headers are safe"}
        }
    } catch {
        return @{Status = 500; Details = $_.Exception.Message}
    }
} "200" "Information Disclosure"

Test-Case "Directory Traversal - .env" {
    try {
        $r = Invoke-WebRequest -Uri "$base/.env" -Method GET -ErrorAction Stop
        return @{
            Status = $r.StatusCode; 
            Details = "VULNERABLE! .env file accessible";
            Severity = "CRITICAL";
            Recommendation = "Ensure .env and sensitive files are not accessible via web server"
        }
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        return @{Status = $status; Details = "Correctly blocked"}
    }
} "404" "Information Disclosure"

# ============================================
# 6. ADMIN ENDPOINT SECURITY
# ============================================

Write-Host "`n=== 6. ADMIN ENDPOINT SECURITY ===" -ForegroundColor Yellow

Test-Case "Admin Stats Without Key" {
    try {
        $r = Invoke-RestMethod -Uri "$base/admin/stats" -Method GET -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! Admin endpoint accessible without key";
            Severity = "CRITICAL";
            Recommendation = "Ensure admin endpoints require authentication"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        return @{Status = $status; Details = "Correctly protected"}
    }
} "403" "Admin Security"

Test-Case "Admin Stats With Wrong Key" {
    try {
        $r = Invoke-RestMethod -Uri "$base/admin/stats" -Method GET -Headers @{"X-Admin-Key"="wrongkey"} -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! Wrong admin key accepted";
            Severity = "CRITICAL";
            Recommendation = "Fix admin key validation"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        return @{Status = $status; Details = "Correctly rejected"}
    }
} "403" "Admin Security"

# ============================================
# SUMMARY
# ============================================

Write-Host "`n`n=== TEST SUMMARY ===" -ForegroundColor Yellow
Write-Host "Total tests: $($results.Count)" -ForegroundColor Cyan
$passed = ($results | Where-Object { $_.Pass }).Count
$failed = ($results | Where-Object { -not $_.Pass }).Count

Write-Host "✅ Passed: $passed" -ForegroundColor Green
Write-Host "❌ Failed: $failed" -ForegroundColor Red

if ($findings.Count -gt 0) {
    Write-Host "`n=== SECURITY FINDINGS ===" -ForegroundColor Red
    $findings | Format-Table -AutoSize
}

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
$results | Format-Table -AutoSize

# Save to file
$results | Export-Csv -Path "security_test_results.csv" -NoTypeInformation -Encoding UTF8
Write-Host "`nResults saved to: security_test_results.csv" -ForegroundColor Green

if ($findings.Count -gt 0) {
    $findings | Export-Csv -Path "security_findings.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Security findings saved to: security_findings.csv" -ForegroundColor Yellow
}
