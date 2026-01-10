<?php
/**
 * CCCD API - PHP Example
 * ======================
 * Example code để gọi CCCD API sử dụng PHP cURL
 */

// Configuration
$API_BASE_URL = 'http://127.0.0.1:8000';
$API_KEY = 'your-api-key-here'; // Thay bằng API key của bạn

/**
 * Parse CCCD number
 * 
 * @param string $cccd Số CCCD 12 chữ số
 * @param string|null $provinceVersion Optional. "legacy_63" hoặc "current_34"
 * @return array Response từ API
 * @throws Exception Nếu có lỗi khi gọi API
 */
function parseCCCD($cccd, $provinceVersion = null) {
    global $API_BASE_URL, $API_KEY;
    
    $url = $API_BASE_URL . '/v1/cccd/parse';
    
    $payload = [
        'cccd' => $cccd
    ];
    
    if ($provinceVersion !== null) {
        $payload['province_version'] = $provinceVersion;
    }
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'X-API-Key: ' . $API_KEY,
        'Content-Type: application/json'
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        throw new Exception("cURL Error: " . $error);
    }
    
    if ($httpCode >= 400) {
        $errorData = json_decode($response, true);
        throw new Exception("HTTP {$httpCode}: " . ($errorData['message'] ?? 'Unknown error'));
    }
    
    return json_decode($response, true);
}

/**
 * Health check
 * 
 * @return array Health status
 */
function healthCheck() {
    global $API_BASE_URL;
    
    $url = $API_BASE_URL . '/health';
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json'
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode >= 400) {
        throw new Exception("HTTP {$httpCode}: Health check failed");
    }
    
    return json_decode($response, true);
}

// Example usage
try {
    // 1. Health check
    echo "=== Health Check ===\n";
    $health = healthCheck();
    echo "Status: " . $health['status'] . "\n";
    
    // 2. Parse CCCD - Basic
    echo "\n=== Parse CCCD - Basic ===\n";
    $result1 = parseCCCD('079203012345');
    echo json_encode($result1, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
    
    // 3. Parse CCCD - With province version
    echo "\n=== Parse CCCD - With province_version ===\n";
    $result2 = parseCCCD('079203012345', 'legacy_63');
    echo json_encode($result2, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
    
    // 4. Error handling
    echo "\n=== Error Handling ===\n";
    try {
        $result3 = parseCCCD('invalid');
        echo json_encode($result3, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
    }
    
} catch (Exception $e) {
    echo "Fatal Error: " . $e->getMessage() . "\n";
    exit(1);
}
?>
