/**
 * CCCD API - JavaScript Example
 * ==============================
 * Example code để gọi CCCD API sử dụng JavaScript fetch API
 */

// Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';
const API_KEY = 'your-api-key-here'; // Thay bằng API key của bạn

/**
 * Parse CCCD number
 * @param {string} cccd - Số CCCD 12 chữ số
 * @param {string|null} provinceVersion - Optional. "legacy_63" hoặc "current_34"
 * @returns {Promise<Object>} Response từ API
 * @throws {Error} Nếu có lỗi khi gọi API
 */
async function parseCCCD(cccd, provinceVersion = null) {
  const url = `${API_BASE_URL}/v1/cccd/parse`;
  
  const payload = {
    cccd: cccd
  };
  
  if (provinceVersion) {
    payload.province_version = provinceVersion;
  }
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`HTTP ${response.status}: ${errorData.message || response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request Error:', error);
    throw error;
  }
}

/**
 * Health check
 * @returns {Promise<Object>} Health status
 */
async function healthCheck() {
  const url = `${API_BASE_URL}/health`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return await response.json();
}

// Example usage
(async function main() {
  try {
    // 1. Health check
    console.log('=== Health Check ===');
    const health = await healthCheck();
    console.log(`Status: ${health.status}`);
    
    // 2. Parse CCCD - Basic
    console.log('\n=== Parse CCCD - Basic ===');
    const result1 = await parseCCCD('079203012345');
    console.log(JSON.stringify(result1, null, 2));
    
    // 3. Parse CCCD - With province version
    console.log('\n=== Parse CCCD - With province_version ===');
    const result2 = await parseCCCD('079203012345', 'legacy_63');
    console.log(JSON.stringify(result2, null, 2));
    
    // 4. Error handling
    console.log('\n=== Error Handling ===');
    try {
      const result3 = await parseCCCD('invalid');
      console.log(JSON.stringify(result3, null, 2));
    } catch (error) {
      console.error('Error:', error.message);
    }
    
  } catch (error) {
    console.error('Fatal Error:', error);
    process.exit(1);
  }
})();

// Node.js: npm install node-fetch (nếu dùng Node.js < 18)
// Browser: fetch is available natively
