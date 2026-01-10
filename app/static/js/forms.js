// Form Validation & Feedback

(function() {
    'use strict';
    
    // Email validation
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    // Real-time validation
    function setupRealTimeValidation() {
        document.querySelectorAll('input[type="email"]').forEach(input => {
            input.addEventListener('blur', function() {
                const value = this.value.trim();
                if (value && !validateEmail(value)) {
                    this.classList.add('error');
                    showFieldError(this, 'Email không hợp lệ');
                } else {
                    this.classList.remove('error');
                    clearFieldError(this);
                }
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('error')) {
                    const value = this.value.trim();
                    if (validateEmail(value)) {
                        this.classList.remove('error');
                        clearFieldError(this);
                    }
                }
            });
        });
        
        // Password validation
        document.querySelectorAll('input[type="password"][minlength]').forEach(input => {
            input.addEventListener('blur', function() {
                const minLength = parseInt(this.getAttribute('minlength')) || 8;
                if (this.value.length > 0 && this.value.length < minLength) {
                    this.classList.add('error');
                    showFieldError(this, `Mật khẩu phải có ít nhất ${minLength} ký tự`);
                } else if (this.value.length >= minLength) {
                    this.classList.remove('error');
                    clearFieldError(this);
                }
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('error')) {
                    const minLength = parseInt(this.getAttribute('minlength')) || 8;
                    if (this.value.length >= minLength) {
                        this.classList.remove('error');
                        clearFieldError(this);
                    }
                }
            });
        });
        
        // Required fields
        document.querySelectorAll('input[required]').forEach(input => {
            input.addEventListener('blur', function() {
                if (!this.value.trim()) {
                    this.classList.add('error');
                    showFieldError(this, 'Trường này là bắt buộc');
                } else {
                    this.classList.remove('error');
                    clearFieldError(this);
                }
            });
        });
        
        // Label length validation (max 100 chars)
        document.querySelectorAll('.label-input').forEach(input => {
            input.addEventListener('input', function() {
                const value = this.value.trim();
                if (value.length > 100) {
                    this.classList.add('error');
                    showFieldError(this, 'Label không được quá 100 ký tự');
                } else {
                    this.classList.remove('error');
                    clearFieldError(this);
                }
            });
        });
    }
    
    // Show field error
    function showFieldError(input, message) {
        clearFieldError(input);
        const errorEl = document.createElement('div');
        errorEl.className = 'form-error';
        errorEl.textContent = message;
        input.parentElement.appendChild(errorEl);
    }
    
    // Clear field error
    function clearFieldError(input) {
        const errorEl = input.parentElement.querySelector('.form-error');
        if (errorEl) {
            errorEl.remove();
        }
    }
    
    // Form submit validation
    function setupFormValidation() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                let hasError = false;
                
                // Validate required fields
                form.querySelectorAll('input[required]').forEach(input => {
                    if (!input.value.trim()) {
                        input.classList.add('error');
                        showFieldError(input, 'Trường này là bắt buộc');
                        hasError = true;
                    }
                });
                
                // Validate email fields
                form.querySelectorAll('input[type="email"]').forEach(input => {
                    if (input.value.trim() && !validateEmail(input.value.trim())) {
                        input.classList.add('error');
                        showFieldError(input, 'Email không hợp lệ');
                        hasError = true;
                    }
                });
                
                // Validate password length
                form.querySelectorAll('input[type="password"][minlength]').forEach(input => {
                    const minLength = parseInt(input.getAttribute('minlength')) || 8;
                    if (input.value.length > 0 && input.value.length < minLength) {
                        input.classList.add('error');
                        showFieldError(input, `Mật khẩu phải có ít nhất ${minLength} ký tự`);
                        hasError = true;
                    }
                });
                
                if (hasError) {
                    e.preventDefault();
                    // Focus vào field đầu tiên có lỗi
                    const firstError = form.querySelector('.error');
                    if (firstError) {
                        firstError.focus();
                    }
                }
            });
        });
    }
    
    // Initialize when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setupRealTimeValidation();
            setupFormValidation();
        });
    } else {
        setupRealTimeValidation();
        setupFormValidation();
    }
})();
