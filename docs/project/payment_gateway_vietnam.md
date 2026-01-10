# Payment Gateway Integration - Thị trường Việt Nam

Tài liệu này mô tả các payment gateway phù hợp với thị trường Việt Nam và cách tích hợp vào hệ thống CCCD API.

---

## 🏆 Khuyến nghị: VNPay

**VNPay** là lựa chọn tốt nhất cho thị trường Việt Nam vì:
- ✅ Hỗ trợ đa dạng phương thức thanh toán (thẻ ATM, thẻ tín dụng, ví điện tử)
- ✅ Tích hợp với hầu hết các ngân hàng lớn ở Việt Nam
- ✅ Có sandbox environment để test
- ✅ Tài liệu API đầy đủ (tiếng Việt)
- ✅ Phí hợp lý (~2-3% mỗi giao dịch)
- ✅ Hỗ trợ webhook/IPN để xác nhận thanh toán tự động

### Tài liệu VNPay:
- **Sandbox**: https://sandbox.vnpayment.vn/apis/
- **Production**: https://www.vnpayment.vn/
- **API Docs**: https://sandbox.vnpayment.vn/apis/docs/checkout/

### Cách tích hợp VNPay:

1. **Đăng ký tài khoản VNPay**
   - Đăng ký tại: https://www.vnpayment.vn/
   - Lấy `TmnCode` và `SecretKey`

2. **Cài đặt thư viện Python:**
   ```bash
   pip install vnpay-python
   ```
   Hoặc tự implement theo API docs của VNPay.

3. **Tạo payment URL:**
   ```python
   from vnpay import VNPay
   
   vnpay = VNPay(
       tmn_code='YOUR_TMN_CODE',
       secret_key='YOUR_SECRET_KEY',
       sandbox=True  # False cho production
   )
   
   payment_url = vnpay.create_payment_url({
       'amount': 100000,  # VND
       'order_id': 'ORDER_123',
       'order_desc': 'Thanh toán gói Premium',
       'return_url': 'https://yourdomain.com/portal/payment/callback',
       'ipaddr': request.remote_addr,
   })
   ```

4. **Xử lý callback:**
   ```python
   @portal_bp.route('/payment/callback')
   def payment_callback():
       # Verify payment từ VNPay
       result = vnpay.verify_payment(request.args)
       
       if result['status'] == 'success':
           # Update payment status trong database
           # Activate subscription
           # Send confirmation email
       else:
           # Handle failed payment
   ```

---

## 💰 Momo

**Momo** là ví điện tử phổ biến ở Việt Nam:
- ✅ Dễ sử dụng, nhiều người dùng
- ✅ Tích hợp nhanh
- ✅ Phí thấp (~1-2%)
- ❌ Chỉ hỗ trợ ví Momo (không có thẻ ngân hàng)

### Tài liệu Momo:
- **Developer Portal**: https://developers.momo.vn/
- **API Docs**: https://developers.momo.vn/docs/

### Cách tích hợp Momo:

1. **Đăng ký tài khoản Merchant**
   - Đăng ký tại: https://developers.momo.vn/
   - Lấy `PartnerCode`, `AccessKey`, `SecretKey`

2. **Tạo payment request:**
   ```python
   import requests
   import hashlib
   import json
   
   def create_momo_payment(amount, order_id, return_url):
       endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
       
       data = {
           "partnerCode": "YOUR_PARTNER_CODE",
           "partnerName": "CCCD API",
           "storeId": "YOUR_STORE_ID",
           "requestId": order_id,
           "amount": amount,
           "orderId": order_id,
           "orderInfo": "Thanh toán gói Premium",
           "redirectUrl": return_url,
           "ipnUrl": "https://yourdomain.com/portal/payment/momo/callback",
           "lang": "vi",
           "extraData": ""
       }
       
       # Tạo signature
       raw_signature = f"accessKey={access_key}&amount={amount}&extraData={extra_data}&ipnUrl={ipn_url}&orderId={order_id}&orderInfo={order_info}&partnerCode={partner_code}&redirectUrl={redirect_url}&requestId={request_id}&requestType={request_type}"
       signature = hmac.new(secret_key.encode(), raw_signature.encode(), hashlib.sha256).hexdigest()
       data["signature"] = signature
       
       response = requests.post(endpoint, json=data)
       return response.json()["payUrl"]
   ```

---

## 💳 ZaloPay

**ZaloPay** tích hợp với Zalo ecosystem:
- ✅ Nhiều người dùng Zalo
- ✅ Dễ tích hợp
- ✅ Phí thấp (~1-2%)
- ❌ Chủ yếu cho người dùng Zalo

### Tài liệu ZaloPay:
- **Developer Portal**: https://developers.zalopay.vn/
- **API Docs**: https://developers.zalopay.vn/docs/

---

## 🏦 OnePay

**OnePay** là payment gateway chuyên nghiệp:
- ✅ Hỗ trợ nhiều ngân hàng
- ✅ Tích hợp quốc tế (Visa, Mastercard)
- ✅ Phí: ~2-3%
- ❌ Tài liệu ít hơn VNPay

### Tài liệu OnePay:
- **Website**: https://onepay.vn/
- **API Docs**: Liên hệ OnePay để lấy tài liệu

---

## 📊 So sánh Payment Gateways

| Gateway | Phí | Phương thức | Độ phổ biến | Dễ tích hợp | Khuyến nghị |
|---------|-----|-------------|-------------|-------------|-------------|
| **VNPay** | 2-3% | ATM, Credit, Ví | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ **Tốt nhất** |
| **Momo** | 1-2% | Ví Momo | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Tốt cho ví điện tử |
| **ZaloPay** | 1-2% | Ví ZaloPay | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Tốt nếu target Zalo users |
| **OnePay** | 2-3% | ATM, Credit, Quốc tế | ⭐⭐⭐ | ⭐⭐⭐ | ⚠️ Tùy chọn |
| **Payoo** | 2-3% | ATM, Credit | ⭐⭐ | ⭐⭐⭐ | ⚠️ Ít phổ biến |

---

## 🎯 Khuyến nghị Implementation

### Option 1: Chỉ VNPay (Đơn giản nhất)
- Tích hợp VNPay trước
- Hỗ trợ đủ các phương thức thanh toán
- Dễ maintain

### Option 2: VNPay + Momo (Cân bằng)
- VNPay cho thẻ ngân hàng
- Momo cho ví điện tử
- Cover được đa số người dùng

### Option 3: Multi-gateway (Linh hoạt nhất)
- Hỗ trợ nhiều gateway
- User chọn gateway khi thanh toán
- Phức tạp hơn nhưng linh hoạt

---

## 📝 Implementation Checklist

### Phase 1: VNPay Integration
- [ ] Đăng ký tài khoản VNPay (sandbox)
- [ ] Tạo `services/payment_gateway.py` service
- [ ] Implement `create_payment_url()` function
- [ ] Implement `verify_payment()` function
- [ ] Tạo route `/portal/payment/vnpay/callback`
- [ ] Update `billing_service.py` để auto-activate subscription
- [ ] Test với sandbox environment
- [ ] Deploy production và test với số tiền nhỏ

### Phase 2: Momo Integration (Optional)
- [ ] Đăng ký tài khoản Momo Merchant
- [ ] Extend `payment_gateway.py` để support Momo
- [ ] Tạo route `/portal/payment/momo/callback`
- [ ] Update UI để user chọn payment method
- [ ] Test integration

### Phase 3: Multi-gateway Support
- [ ] Refactor code để support multiple gateways
- [ ] Create payment gateway abstraction layer
- [ ] Add payment method selection UI
- [ ] Add payment gateway status monitoring

---

## 🔒 Security Best Practices

1. **Never store payment credentials in code**
   - Store `SecretKey`, `AccessKey` trong `.env` file
   - Use environment variables

2. **Always verify payment signatures**
   - VNPay, Momo, ZaloPay đều có signature verification
   - Never trust payment data without verification

3. **Use HTTPS**
   - All payment callbacks must use HTTPS
   - Never send payment data over HTTP

4. **Validate payment amounts**
   - Always verify payment amount matches order amount
   - Prevent amount tampering

5. **Handle timeouts**
   - Payment callbacks có thể bị delay
   - Implement retry logic
   - Use webhook polling nếu cần

6. **Log everything**
   - Log all payment attempts
   - Log successful/failed payments
   - Log callback IPs để detect fraud

---

## 💡 Tips

1. **Start with Sandbox**
   - Test kỹ với sandbox trước khi deploy production
   - VNPay sandbox: https://sandbox.vnpayment.vn/

2. **Test với số tiền nhỏ**
   - Khi deploy production, test với số tiền nhỏ trước
   - Verify toàn bộ flow trước khi accept real payments

3. **Monitor payment success rate**
   - Track tỷ lệ thành công/thất bại
   - Identify issues early

4. **Customer support**
   - Có process để handle payment issues
   - User có thể contact support nếu payment failed

5. **Refund process**
   - Có process để refund nếu cần
   - Document refund policy

---

## 📚 Resources

- **VNPay API Docs**: https://sandbox.vnpayment.vn/apis/docs/checkout/
- **Momo Developer Portal**: https://developers.momo.vn/
- **ZaloPay Developer Portal**: https://developers.zalopay.vn/
- **OnePay**: https://onepay.vn/

---

*Last updated: 2026-01-10*
