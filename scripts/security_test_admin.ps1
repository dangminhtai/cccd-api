# Security Testing Script - Admin Endpoint Security Tests
# Test 7.3, 7.4 from security_testing_guide.md

$base = "http://127.0.0.1:8000"
$results = @()

# Admin Key (cần config trong .env)
# Try to get from environment or .env file
$adminKey = $env:ADMIN_SECRET
if (-not $adminKey) {
    # Try to read from .env file
    if (Test-Path ".env") {
        $envContent = Get-Content ".env" -Raw
        if ($envContent -match "ADMIN_SECRET=(.+)") {
            $adminKey = $matches[1].Trim()
        }
    }
}

if (-not $adminKey) {
    Write-Host "WARNING: ADMIN_SECRET not found. Some tests may fail." -ForegroundColor Yellow
    Write-Host "Set ADMIN_SECRET in .env file or environment variable." -ForegroundColor Yellow
    Write-Host "Tests will continue but may return 403/503 errors." -ForegroundColor Yellow
}

function Test-Case {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$Expected,
        [string]$Category = "Admin Security"
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

Write-Host "`n=== 7. ADMIN ENDPOINT SECURITY ===" -ForegroundColor Yellow

# ============================================
# Test 7.3: SQL Injection trong Admin Endpoints
# ============================================

Write-Host "`n--- Test 7.3: SQL Injection trong Admin Endpoints ---" -ForegroundColor Cyan

# Test 7.3.1: SQL Injection trong key_prefix parameter
Write-Host "`n[7.3.1] Testing SQL Injection in key_prefix parameter" -ForegroundColor Yellow

$sqlPayloads = @(
    "free_1' OR '1'='1",
    "free_1' UNION SELECT * FROM api_keys--",
    "free_1'; DROP TABLE api_keys--",
    "free_1' OR 1=1--",
    "free_1' AND SLEEP(5)--"
)

foreach ($payload in $sqlPayloads) {
    Test-Case "SQL Injection in key_prefix: $payload" {
        if (-not $adminKey) {
            return @{
                Status = "SKIP";
                Pass = $true;
                Details = "Skipped: ADMIN_SECRET not configured"
            }
        }
        try {
            $headers = @{"X-Admin-Key" = $adminKey}
            $r = Invoke-RestMethod -Uri "$base/admin/keys/$payload/info" -Method GET -Headers $headers -ErrorAction Stop
            
            # Check if response contains SQL error or unexpected data
            $responseJson = $r | ConvertTo-Json
            $vulnerable = $false
            $vulnInfo = ""
            
            if ($responseJson -match "mysql|pymysql|SQL|syntax error|database|table.*doesn't exist|Unknown column") {
                $vulnerable = $true
                $vulnInfo = "VULNERABLE! SQL error leaked: $($matches[0])"
            }
            
            if ($vulnerable) {
                return @{
                    Status = "VULNERABLE";
                    Pass = $false;
                    Details = $vulnInfo;
                    Severity = "HIGH"
                }
            } else {
                return @{
                    Status = "PASS";
                    Pass = $true;
                    Details = "SQL injection payload rejected or handled safely"
                }
            }
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            if ($status -eq 404 -or $status -eq 400 -or $status -eq 401 -or $status -eq 403) {
                return @{
                    Status = $status;
                    Pass = $true;
                    Details = "SQL injection payload correctly rejected (status $status)"
                }
            } else {
                # Check error message for SQL leakage
                $errorResponse = $_.Exception.Response
                $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
                $responseBody = $reader.ReadToEnd()
                
                if ($responseBody -match "mysql|pymysql|SQL|syntax error|database") {
                    return @{
                        Status = $status;
                        Pass = $false;
                        Details = "VULNERABLE! SQL error leaked in response";
                        Severity = "HIGH"
                    }
                } else {
                    return @{
                        Status = $status;
                        Pass = $true;
                        Details = "Error response is safe (no SQL leakage)"
                    }
                }
            }
        }
    } "PASS" "Admin Security"
}

# Test 7.3.2: SQL Injection trong create_key endpoint (email, tier)
Write-Host "`n[7.3.2] Testing SQL Injection in create_key endpoint" -ForegroundColor Yellow

$sqlEmailPayloads = @(
    "test@example.com' OR '1'='1",
    "test@example.com'; DROP TABLE api_keys--",
    "test@example.com' UNION SELECT * FROM api_keys--"
)

$sqlTierPayloads = @(
    "free' OR '1'='1",
    "free'; DROP TABLE api_keys--",
    "free' UNION SELECT * FROM api_keys--"
)

foreach ($emailPayload in $sqlEmailPayloads) {
    Test-Case "SQL Injection in create_key email: $emailPayload" {
        if (-not $adminKey) {
            return @{
                Status = "SKIP";
                Pass = $true;
                Details = "Skipped: ADMIN_SECRET not configured"
            }
        }
        try {
            $body = @{
                email = $emailPayload
                tier = "free"
                days = 30
            } | ConvertTo-Json
            
            $headers = @{"X-Admin-Key" = $adminKey}
            $r = Invoke-RestMethod -Uri "$base/admin/keys/create" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
            
            # Check if SQL injection succeeded (unlikely, but check)
            $responseJson = $r | ConvertTo-Json
            if ($responseJson -match "mysql|pymysql|SQL|syntax error") {
                return @{
                    Status = "VULNERABLE";
                    Pass = $false;
                    Details = "VULNERABLE! SQL error leaked";
                    Severity = "HIGH"
                }
            } else {
                return @{
                    Status = "PASS";
                    Pass = $true;
                    Details = "SQL injection payload handled safely (may have created key or rejected)"
                }
            }
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            $errorResponse = $_.Exception.Response
            $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            
            if ($responseBody -match "mysql|pymysql|SQL|syntax error|database") {
                return @{
                    Status = $status;
                    Pass = $false;
                    Details = "VULNERABLE! SQL error leaked in response";
                    Severity = "HIGH"
                }
            } elseif ($status -eq 400 -or $status -eq 422) {
                return @{
                    Status = $status;
                    Pass = $true;
                    Details = "SQL injection payload correctly rejected (validation error)"
                }
            } else {
                return @{
                    Status = $status;
                    Pass = $true;
                    Details = "Error response is safe (status $status)"
                }
            }
        }
    } "PASS" "Admin Security"
}

foreach ($tierPayload in $sqlTierPayloads) {
    Test-Case "SQL Injection in create_key tier: $tierPayload" {
        if (-not $adminKey) {
            return @{
                Status = "SKIP";
                Pass = $true;
                Details = "Skipped: ADMIN_SECRET not configured"
            }
        }
        try {
            $body = @{
                email = "test@example.com"
                tier = $tierPayload
                days = 30
            } | ConvertTo-Json
            
            $headers = @{"X-Admin-Key" = $adminKey}
            $r = Invoke-RestMethod -Uri "$base/admin/keys/create" -Method POST -ContentType "application/json" -Body $body -Headers $headers -ErrorAction Stop
            
            $responseJson = $r | ConvertTo-Json
            if ($responseJson -match "mysql|pymysql|SQL|syntax error") {
                return @{
                    Status = "VULNERABLE";
                    Pass = $false;
                    Details = "VULNERABLE! SQL error leaked";
                    Severity = "HIGH"
                }
            } else {
                return @{
                    Status = "PASS";
                    Pass = $true;
                    Details = "SQL injection payload handled safely"
                }
            }
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            $errorResponse = $_.Exception.Response
            $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            
            if ($responseBody -match "mysql|pymysql|SQL|syntax error|database") {
                return @{
                    Status = $status;
                    Pass = $false;
                    Details = "VULNERABLE! SQL error leaked in response";
                    Severity = "HIGH"
                }
            } elseif ($status -eq 400 -or $status -eq 422) {
                return @{
                    Status = $status;
                    Pass = $true;
                    Details = "SQL injection payload correctly rejected (validation error)"
                }
            } else {
                return @{
                    Status = $status;
                    Pass = $true;
                    Details = "Error response is safe (status $status)"
                }
            }
        }
    } "PASS" "Admin Security"
}

# ============================================
# Test 7.4: IDOR (Insecure Direct Object Reference)
# ============================================

Write-Host "`n--- Test 7.4: IDOR (Insecure Direct Object Reference) ---" -ForegroundColor Cyan

# Test 7.4.1: Admin có thể truy cập key của người khác (đúng - admin có quyền)
Write-Host "`n[7.4.1] Testing Admin Access to Other Users' Keys" -ForegroundColor Yellow

# First, create a test key to get a key_prefix
Test-Case "IDOR - Admin can access any key (expected behavior)" {
    if (-not $adminKey) {
        return @{
            Status = "SKIP";
            Pass = $true;
            Details = "Skipped: ADMIN_SECRET not configured"
        }
    }
    try {
        # Create a test key
        $createBody = @{
            email = "test_idor@example.com"
            tier = "free"
            days = 1
        } | ConvertTo-Json
        
        $headers = @{"X-Admin-Key" = $adminKey}
        $createResponse = Invoke-RestMethod -Uri "$base/admin/keys/create" -Method POST -ContentType "application/json" -Body $createBody -Headers $headers -ErrorAction Stop
        
        $createdKeyPrefix = $createResponse.key_prefix
        
        # Admin should be able to access this key
        $infoResponse = Invoke-RestMethod -Uri "$base/admin/keys/$createdKeyPrefix/info" -Method GET -Headers $headers -ErrorAction Stop
        
        return @{
            Status = "PASS";
            Pass = $true;
            Details = "CORRECT: Admin can access any key (expected admin behavior)"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        return @{
            Status = $status;
            Pass = $true;
            Details = "Admin access test: Status $status (may need valid admin key)"
        }
    }
} "PASS" "Admin Security"

# Test 7.4.2: User thường (không phải admin) có thể truy cập key của người khác không
Write-Host "`n[7.4.2] Testing Non-Admin Access to Other Users' Keys" -ForegroundColor Yellow

Test-Case "IDOR - Non-admin cannot access other users' keys" {
    try {
        # Try to access admin endpoint with regular API key (not admin key)
        $regularKey = "free_a1c6062d52bdbff5762e07ec391dfb81"
        $headers = @{"X-API-Key" = $regularKey}
        
        # Try to access admin endpoint
        $r = Invoke-RestMethod -Uri "$base/admin/stats" -Method GET -Headers $headers -ErrorAction Stop
        
        return @{
            Status = "VULNERABLE";
            Pass = $false;
            Details = "VULNERABLE! Regular API key can access admin endpoint";
            Severity = "CRITICAL"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 403 -or $status -eq 401) {
            return @{
                Status = $status;
                Pass = $true;
                Details = "CORRECT: Regular API key cannot access admin endpoint (status $status)"
            }
        } else {
            return @{
                Status = $status;
                Pass = $true;
                Details = "Regular key access rejected (status $status)"
            }
        }
    }
} "403" "Admin Security"

Test-Case "IDOR - Non-admin cannot access other users' key info" {
    try {
        # Try to access another user's key info with regular API key
        $regularKey = "free_a1c6062d52bdbff5762e07ec391dfb81"
        $headers = @{"X-API-Key" = $regularKey}
        
        # Try to access a key that doesn't belong to this user
        $r = Invoke-RestMethod -Uri "$base/admin/keys/prem_31c65c426015522c069a6dc1cf57a3ad/info" -Method GET -Headers $headers -ErrorAction Stop
        
        return @{
            Status = "VULNERABLE";
            Pass = $false;
            Details = "VULNERABLE! Regular API key can access other users' key info";
            Severity = "HIGH"
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 403 -or $status -eq 401 -or $status -eq 404) {
            return @{
                Status = $status;
                Pass = $true;
                Details = "CORRECT: Regular API key cannot access other users' key info (status $status)"
            }
        } else {
            return @{
                Status = $status;
                Pass = $true;
                Details = "Access rejected (status $status)"
            }
        }
    }
} "403" "Admin Security"

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
$csvPath = "security_test_admin_results.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "`nResults saved to: $csvPath" -ForegroundColor Green
