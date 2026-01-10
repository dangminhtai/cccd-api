// AJAX Helpers - Loading states, error handling, toast notifications

(function() {
    'use strict';
    
    // Toast notification system
    function showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: var(--spacing-4) var(--spacing-5);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: var(--z-tooltip);
            animation: slideIn 0.3s ease;
            max-width: 400px;
            word-wrap: break-word;
        `;
        
        if (type === 'success') {
            toast.style.backgroundColor = 'var(--color-success-bg)';
            toast.style.color = 'var(--color-success-text)';
            toast.style.border = '1px solid var(--color-success-border)';
        } else if (type === 'error') {
            toast.style.backgroundColor = 'var(--color-error-bg)';
            toast.style.color = 'var(--color-error-text)';
            toast.style.border = '1px solid var(--color-error-border)';
        } else if (type === 'warning') {
            toast.style.backgroundColor = 'var(--color-warning-bg)';
            toast.style.color = 'var(--color-warning-text)';
            toast.style.border = '1px solid var(--color-warning-border)';
        } else {
            toast.style.backgroundColor = 'var(--color-info-bg)';
            toast.style.color = 'var(--color-info-text)';
            toast.style.border = '1px solid var(--color-info-border)';
        }
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    // Loading spinner HTML
    function getSpinnerHTML() {
        return '<span class="spinner"></span> ';
    }
    
    // Set button loading state
    function setButtonLoading(button, loading = true) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = getSpinnerHTML() + button.dataset.originalText;
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || button.textContent;
        }
    }
    
    // Enhanced fetch with loading states and error handling
    window.ajaxFetch = function(url, options = {}) {
        const {
            button = null,
            showLoading = true,
            showToast = true,
            successMessage = null,
            errorMessage = 'Đã xảy ra lỗi. Vui lòng thử lại.',
            parseJSON = true,
            ...fetchOptions
        } = options;
        
        // Set loading state
        if (button && showLoading) {
            setButtonLoading(button, true);
        }
        
        // Default headers
        const headers = {
            'X-Requested-With': 'XMLHttpRequest',
            ...fetchOptions.headers
        };
        
        return fetch(url, {
            ...fetchOptions,
            headers
        })
        .then(async response => {
            // Check content type
            const contentType = response.headers.get('content-type') || '';
            
            if (!contentType.includes('application/json')) {
                if (response.redirected || response.status === 302 || response.status === 401) {
                    throw new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
                }
                const text = await response.text();
                throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 100)}`);
            }
            
            if (!response.ok && response.status !== 200) {
                const data = await response.json();
                const errorMsg = data.message || data.error || errorMessage;
                throw new Error(errorMsg);
            }
            
            return parseJSON ? response.json() : response;
        })
        .then(data => {
            // Handle wrapped response
            if (data && typeof data === 'object') {
                if (data.success === false) {
                    throw new Error(data.message || data.error || errorMessage);
                }
            }
            
            // Show success toast
            if (successMessage && showToast) {
                window.showToast(successMessage, 'success');
            }
            
            return data;
        })
        .catch(error => {
            // Show error toast
            if (showToast) {
                window.showToast(error.message || errorMessage, 'error');
            }
            throw error;
        })
        .finally(() => {
            // Remove loading state
            if (button && showLoading) {
                setButtonLoading(button, false);
            }
        });
    };
    
    // Expose showToast globally
    window.showToast = showToast;
    
    // Add CSS animations for toast
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
})();
