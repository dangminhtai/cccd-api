# Security Testing Script - Reconnaissance Tests
# Test 2.1, 2.2, 2.3 from security_testing_guide.md

$base = "http://127.0.0.1:8000"
$results = @()

function Test-Case {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$Expected,
        [string]$Category = "Reconnaissance"
    )
    Write-Host "`n[TEST] $Name" -ForegroundColor Cyan
    try {
        $result = & $Test
        $pass = ($result.Status -eq $Expected)
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

Write-Host "`n=== 2. RECONNAISSANCE - THU THAP THONG TIN ===" -ForegroundColor Yellow

# Test 2.1: Kham Pha Endpoints
Write-Host "`n--- Test 2.1: Kham Pha Endpoints ---" -ForegroundColor Cyan

Test-Case "Health Check Endpoint" {
    try {
        $r = Invoke-WebRequest -Uri "$base/health" -Method GET -ErrorAction Stop
        return @{Status = $r.StatusCode; Details = "Health endpoint accessible"}
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        return @{Status = $status; Details = $_.Exception.Message}
    }
} "200" "Reconnaissance"

Test-Case "Root Endpoint" {
    try {
        $r = Invoke-WebRequest -Uri "$base/" -Method GET -ErrorAction Stop
        return @{Status = $r.StatusCode; Details = "Root endpoint accessible"}
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        return @{Status = $status; Details = "Not accessible"}
    }
} "200" "Reconnaissance"

Test-Case "Demo Page Endpoint" {
    try {
        $r = Invoke-WebRequest -Uri "$base/demo" -Method GET -ErrorAction Stop
        return @{Status = $r.StatusCode; Details = "Demo page accessible"}
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        return @{Status = $status; Details = $_.Exception.Message}
    }
} "200" "Reconnaissance"

Test-Case "API Endpoint Without Auth" {
    try {
        $body = @{cccd = "079203012345"} | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! API endpoint accessible without auth";
            Severity = "HIGH";
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 401) {
            return @{Status = $status; Details = "Correctly requires authentication"}
        } else {
            return @{Status = $status; Details = "Unexpected status"}
        }
    }
} "401" "Reconnaissance"

Test-Case "Admin Stats Endpoint Without Auth" {
    try {
        $r = Invoke-RestMethod -Uri "$base/admin/stats" -Method GET -ErrorAction Stop
        return @{
            Status = 200; 
            Details = "VULNERABLE! Admin endpoint accessible without auth";
            Severity = "CRITICAL";
        }
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 403 -or $status -eq 503) {
            return @{Status = $status; Details = "Correctly protected"}
        } else {
            return @{Status = $status; Details = "Unexpected status"}
        }
    }
} "403" "Reconnaissance"

Test-Case "Admin Dashboard Without Auth" {
    try {
        $r = Invoke-WebRequest -Uri "$base/admin/" -Method GET -ErrorAction Stop
        return @{Status = $r.StatusCode; Details = "Admin dashboard accessible (HTML page)"}
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        return @{Status = $status; Details = "Not accessible"}
    }
} "200" "Reconnaissance"

# Test potential endpoints
$potentialEndpoints = @("/debug", "/admin/debug", "/test", "/api", "/v1", "/.env", "/config", "/logs")

Write-Host "`n--- Testing Potential Endpoints ---" -ForegroundColor Cyan
foreach ($endpoint in $potentialEndpoints) {
    Test-Case "Potential Endpoint: $endpoint" {
        try {
            $r = Invoke-WebRequest -Uri "$base$endpoint" -Method GET -ErrorAction Stop
            $content = $r.Content
            $vulnerable = $false
            $vulnInfo = ""
            
            if ($content -match "stacktrace|traceback|File.*\.py|pymysql|MySQL|database|password|secret") {
                $vulnerable = $true
                $vulnInfo = "VULNERABLE! Contains sensitive information"
            }
            
            if ($vulnerable) {
                return @{
                    Status = $r.StatusCode; 
                    Details = $vulnInfo;
                    Severity = "HIGH";
                }
            } else {
                return @{Status = $r.StatusCode; Details = "Endpoint exists but safe"}
            }
        } catch {
            $status = $_.Exception.Response.StatusCode.value__
            if ($status -eq 404) {
                return @{Status = $status; Details = "Not found (OK)"}
            } else {
                return @{Status = $status; Details = "Unexpected status"}
            }
        }
    } "404" "Reconnaissance"
}

# Test 2.2: HTTP Methods Enumeration
Write-Host "`n--- Test 2.2: HTTP Methods Enumeration ---" -ForegroundColor Cyan

$methods = @("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD")
$apiEndpoint = "$base/v1/cccd/parse"

foreach ($method in $methods) {
    Test-Case "HTTP Method: $method on /v1/cccd/parse" {
        try {
            if ($method -eq "POST") {
                $body = @{cccd = "079203012345"} | ConvertTo-Json
                $r = Invoke-WebRequest -Uri $apiEndpoint -Method $method -ContentType "application/json" -Body $body -ErrorAction Stop
            } else {
                $r = Invoke-WebRequest -Uri $apiEndpoint -Method $method -ErrorAction Stop
            }
            
            if ($method -eq "POST") {
                return @{Status = $r.StatusCode; Details = "POST method allowed (correct)"}
            } else {
                return @{
                    Status = $r.StatusCode; 
                    Details = "VULNERABLE! $method method accepted (should be rejected)";
                    Severity = "MEDIUM";
                }
            }
        } catch {
            $status = $_.Exception.Response.StatusCode.value__
            if ($method -eq "POST") {
                if ($status -eq 401) {
                    return @{Status = $status; Details = "POST requires auth (correct)"}
                } else {
                    return @{Status = $status; Details = "Unexpected status for POST"}
                }
            } else {
                if ($status -eq 405) {
                    return @{Status = $status; Details = "Correctly rejected - 405"}
                } else {
                    return @{Status = $status; Details = "Rejected with status $status"}
                }
            }
        }
    } $(if ($method -eq "POST") { "200" } else { "405" }) "Reconnaissance"
}

# Test 2.3: Error Messages Analysis
Write-Host "`n--- Test 2.3: Error Messages Analysis ---" -ForegroundColor Cyan

Test-Case "Error Message - Missing CCCD" {
    try {
        $body = @{} | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        return @{Status = 200; Details = "Unexpected success"}
    } catch {
        $errorResponse = $_.Exception.Response
        $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        
        $leaked = $false
        $leakInfo = ""
        if ($responseBody -match "stacktrace|traceback|File.*\.py|pymysql|MySQL|database|password|secret|__init__|routes/|app/") {
            $leaked = $true
            $leakInfo = "VULNERABLE! Information leaked: $($matches[0])"
        }
        
        $status = [int]$_.Exception.Response.StatusCode
        if ($leaked) {
            return @{
                Status = $status; 
                Details = $leakInfo;
                Severity = "HIGH";
            }
        } else {
            return @{Status = $status; Details = "Error message is safe (generic)"}
        }
    }
} "400" "Reconnaissance"

Test-Case "Error Message - Null CCCD" {
    try {
        $body = '{"cccd": null}' | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        return @{Status = 200; Details = "Unexpected success"}
    } catch {
        $errorResponse = $_.Exception.Response
        $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        
        $leaked = $false
        if ($responseBody -match "stacktrace|traceback|File.*\.py|pymysql|MySQL|database|password|secret") {
            $leaked = $true
        }
        
        $status = [int]$_.Exception.Response.StatusCode
        if ($leaked) {
            return @{
                Status = $status; 
                Details = "VULNERABLE! Information leaked in error";
                Severity = "HIGH";
            }
        } else {
            return @{Status = $status; Details = "Error message is safe"}
        }
    }
} "400" "Reconnaissance"

Test-Case "Error Message - Invalid Format" {
    try {
        $body = @{cccd = "abc123"} | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        return @{Status = 200; Details = "Unexpected success"}
    } catch {
        $errorResponse = $_.Exception.Response
        $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        
        $leaked = $false
        if ($responseBody -match "stacktrace|traceback|File.*\.py|pymysql|MySQL|database|password|secret") {
            $leaked = $true
        }
        
        $status = [int]$_.Exception.Response.StatusCode
        if ($leaked) {
            return @{
                Status = $status; 
                Details = "VULNERABLE! Information leaked in error";
                Severity = "HIGH";
            }
        } else {
            return @{Status = $status; Details = "Error message is safe"}
        }
    }
} "400" "Reconnaissance"

# SUMMARY
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
$csvPath = "security_test_reconnaissance_results.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "`nResults saved to: $csvPath" -ForegroundColor Green
