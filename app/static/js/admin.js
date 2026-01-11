// Admin Dashboard JavaScript Functions
// All functions are preserved from the original admin.html

function showError(msg) {
  const errorEl = document.getElementById("error");
  if (errorEl) {
    errorEl.textContent = msg;
    errorEl.style.display = "block";
    const statsEl = document.getElementById("stats");
    if (statsEl) statsEl.style.display = "none";
  }
}

function hideError() {
  const errorEl = document.getElementById("error");
  if (errorEl) errorEl.style.display = "none";
}

async function loadStats() {
  const adminKey = document.getElementById("adminKey").value.trim();
  if (!adminKey) {
    showError("Vui lòng nhập Admin Secret Key");
    return;
  }

  const loadingEl = document.getElementById("loading");
  const statsEl = document.getElementById("stats");
  if (loadingEl) loadingEl.style.display = "block";
  if (statsEl) statsEl.style.display = "none";
  hideError();

  try {
    const resp = await fetch("/admin/stats", {
      headers: { "X-Admin-Key": adminKey }
    });

    if (!resp.ok) {
      const data = await resp.json();
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    const data = await resp.json();

    // Update requests today
    const requestsTodayEl = document.getElementById("requestsToday");
    if (requestsTodayEl) requestsTodayEl.textContent = data.requests_today || 0;

    // Update tier stats
    const tbody = document.getElementById("tierTableBody");
    if (tbody) {
      tbody.innerHTML = "";

      const tiers = data.tiers || {};
      const tierOrder = ["free", "premium", "ultra"];
      const tierLabels = { free: "Free", premium: "Premium", ultra: "Ultra" };

      tierOrder.forEach(tier => {
        if (tiers[tier]) {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td class="px-6 py-4 font-medium text-white flex items-center gap-2">
              <div class="w-2 h-2 rounded-full ${tier === 'free' ? 'bg-slate-500' : tier === 'premium' ? 'bg-amber-500' : 'bg-purple-500'}"></div>
              ${tierLabels[tier]}
            </td>
            <td class="px-6 py-4 text-slate-300">${tiers[tier].total || 0}</td>
            <td class="px-6 py-4 text-slate-300">${tiers[tier].active || 0}</td>
          `;
          tbody.appendChild(row);
        }
      });
    }

    if (loadingEl) loadingEl.style.display = "none";
    if (statsEl) statsEl.style.display = "block";
    
    // Load pending payments sau khi load stats thành công
    loadPendingPayments(adminKey);
  } catch (e) {
    if (loadingEl) loadingEl.style.display = "none";
    showError("Lỗi: " + e.message);
  }
}

async function loadPendingPayments(adminKey) {
  if (!adminKey) return;
  
  const paymentsContainer = document.getElementById("paymentsContainer");
  if (!paymentsContainer) return;
  
  try {
    const resp = await fetch("/admin/payments", {
      headers: { "X-Admin-Key": adminKey }
    });
    
    if (!resp.ok) {
      if (resp.status === 403) {
        paymentsContainer.innerHTML = 
          '<p class="text-center text-red-400 py-10">❌ Admin key không hợp lệ. Vui lòng kiểm tra lại.</p>';
      } else {
        throw new Error(`HTTP ${resp.status}`);
      }
      return;
    }
    
    const data = await resp.json();
    const payments = data.payments || [];
    
    if (payments.length === 0) {
      paymentsContainer.innerHTML = 
        '<p class="text-center text-slate-400 py-10">Không có payment nào đang chờ xử lý</p>';
      return;
    }
    
    // Render payments table
    let html = '<div class="overflow-x-auto"><table class="w-full text-left border-collapse"><thead class="bg-surface-dark/50 text-slate-400 text-xs uppercase font-medium"><tr><th class="p-4 w-[60px] text-center">#</th><th class="p-4">User Email</th><th class="p-4">Amount</th><th class="p-4">Date</th><th class="p-4">Tier Request</th><th class="p-4">Ghi chú</th><th class="p-4 text-right">Actions</th></tr></thead><tbody class="text-sm divide-y divide-glass-border">';
    
    payments.forEach(payment => {
      const dateStr = payment.created_at ? new Date(payment.created_at).toLocaleString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }) : 'N/A';
      
      const amountStr = payment.currency === 'VND' 
        ? new Intl.NumberFormat('vi-VN').format(payment.amount) + ' ' + payment.currency
        : '$' + payment.amount.toFixed(2) + ' ' + payment.currency;
      
      const tierBadge = payment.tier === 'premium' 
        ? '<span class="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded text-xs font-bold uppercase">Premium</span>'
        : payment.tier === 'ultra'
        ? '<span class="bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded text-xs font-bold uppercase">Ultra</span>'
        : '<span class="bg-slate-500/10 text-slate-400 border border-slate-500/20 px-2 py-0.5 rounded text-xs font-bold uppercase">Free</span>';
      
      html += `
        <tr class="hover:bg-white/5 transition-colors group" id="payment-row-${payment.id}">
          <td class="p-4 text-center text-slate-500">${payment.id}</td>
          <td class="p-4 font-medium text-white">
            <div>${payment.user_email || 'N/A'}</div>
            <div class="text-xs text-slate-400">${payment.user_name || 'N/A'}</div>
          </td>
          <td class="p-4 text-emerald-400 font-bold">${amountStr}</td>
          <td class="p-4 text-slate-300">${dateStr}</td>
          <td class="p-4">${tierBadge}</td>
          <td class="p-4 text-slate-400">${payment.notes || '-'}</td>
          <td class="p-4 text-right">
            <div class="flex items-center justify-end gap-2 opacity-80 group-hover:opacity-100">
              <button class="h-8 w-8 rounded flex items-center justify-center bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500 hover:text-white transition-all border border-emerald-500/30" onclick="approvePayment(${payment.id})" title="Approve">
                <span class="material-symbols-outlined text-[18px]">check</span>
              </button>
              <button class="h-8 w-8 rounded flex items-center justify-center bg-rose-500/20 text-rose-500 hover:bg-rose-500 hover:text-white transition-all border border-rose-500/30" onclick="rejectPayment(${payment.id})" title="Reject">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
          </td>
        </tr>
      `;
    });
    
    html += '</tbody></table></div>';
    paymentsContainer.innerHTML = html;
  } catch (e) {
    paymentsContainer.innerHTML = 
      '<p class="text-center text-red-400 py-10">❌ Lỗi khi tải pending payments: ' + e.message + '</p>';
  }
}

// Enter key to load
document.addEventListener('DOMContentLoaded', function() {
  const adminKeyInput = document.getElementById("adminKey");
  const adminKeyStatus = document.getElementById("adminKeyStatus");
  
  if (adminKeyInput) {
    // Update status icon based on input value
    adminKeyInput.addEventListener("input", function() {
      if (adminKeyStatus) {
        if (this.value.trim().length > 0) {
          adminKeyStatus.classList.remove("hidden");
          adminKeyStatus.classList.add("text-emerald-500");
        } else {
          adminKeyStatus.classList.add("hidden");
        }
      }
    });
    
    adminKeyInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") loadStats();
    });
  }
  
  // Chỉ cho phép nhập số 0-9 vào ô "Số ngày"
  const createDaysInput = document.getElementById("createDays");
  if (createDaysInput) {
    createDaysInput.addEventListener("keypress", (e) => {
      const allowed = /[0-9]|Backspace|Delete|ArrowLeft|ArrowRight|Tab/;
      if (!allowed.test(e.key)) {
        e.preventDefault();
      }
    });

    // Ngăn paste text không phải số
    createDaysInput.addEventListener("paste", (e) => {
      e.preventDefault();
      const paste = (e.clipboardData || window.clipboardData).getData("text");
      const numbersOnly = paste.replace(/[^0-9]/g, "");
      if (numbersOnly) {
        e.target.value = numbersOnly;
      }
    });
  }
});

// Test API function
async function testApi() {
  const cccd = document.getElementById("demoCccd")?.value.trim() || '';
  const provinceVersion = document.getElementById("demoProvinceVersion")?.value || '';
  const apiKey = document.getElementById("demoApiKey")?.value.trim() || '';
  
  const demoError = document.getElementById("demoError");
  const demoResult = document.getElementById("demoResult");
  if (demoError) demoError.style.display = "none";
  if (demoResult) demoResult.style.display = "none";
  
  const payload = {};
  if (cccd) payload.cccd = cccd;
  if (provinceVersion) payload.province_version = provinceVersion;
  
  try {
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;
    
    const resp = await fetch("/v1/cccd/parse", {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    
    const statusEl = document.getElementById("demoStatus");
    const outputEl = document.getElementById("demoOutput");
    
    if (statusEl) statusEl.textContent = resp.status;
    
    const text = await resp.text();
    try {
      const json = JSON.parse(text);
      if (outputEl) outputEl.textContent = JSON.stringify(json, null, 2);
      
      if (statusEl) {
        if (resp.status === 200) {
          statusEl.className = "text-emerald-400";
        } else if (resp.status === 401 || resp.status === 400) {
          statusEl.className = "text-red-400";
        } else {
          statusEl.className = "text-slate-400";
        }
      }
    } catch {
      if (outputEl) outputEl.textContent = text;
      if (statusEl) statusEl.className = "text-red-400";
    }
    
    if (demoResult) demoResult.style.display = "block";
  } catch (e) {
    if (demoError) {
      demoError.textContent = "Lỗi: " + e.message;
      demoError.style.display = "block";
    }
  }
}

async function createKey() {
  const adminKey = document.getElementById("adminKey")?.value.trim() || '';
  const tier = document.getElementById("createTier")?.value || 'ultra';
  const days = document.getElementById("createDays")?.value.trim() || '';

  if (!adminKey) {
    showError("Vui lòng nhập Admin Secret Key trước");
    return;
  }

  const createError = document.getElementById("createError");
  const createSuccess = document.getElementById("createSuccess");
  if (createError) createError.style.display = "none";
  if (createSuccess) createSuccess.style.display = "none";

  try {
    const body = { tier };
    if (days) {
      const daysNum = parseInt(days);
      if (isNaN(daysNum) || daysNum < 1) {
        if (createError) {
          createError.textContent = "Số ngày phải là số nguyên >= 1";
          createError.style.display = "block";
        }
        return;
      }
      body.days = daysNum;
    }

    const resp = await fetch("/admin/keys/create", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Key": adminKey
      },
      body: JSON.stringify(body)
    });

    if (!resp.ok) {
      const data = await resp.json();
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    
    // Hiển thị key
    const createdKeyEl = document.getElementById("createdKey");
    if (createdKeyEl) createdKeyEl.textContent = data.api_key;
    if (createSuccess) createSuccess.style.display = "block";
    
    // Reset form
    const createDaysInput = document.getElementById("createDays");
    if (createDaysInput) createDaysInput.value = "";
    
    // Reload stats để cập nhật số lượng keys
    loadStats();
  } catch (e) {
    if (createError) {
      createError.textContent = "Lỗi: " + e.message;
      createError.style.display = "block";
    }
  }
}

async function approvePayment(paymentId) {
  if (!confirm('Xác nhận approve payment này? API keys của user sẽ được extend 30 ngày.')) {
    return;
  }
  
  const adminKey = document.getElementById('adminKey')?.value.trim() || '';
  if (!adminKey) {
    alert('Vui lòng nhập Admin Secret Key ở trên');
    return;
  }
  
  const row = document.getElementById('payment-row-' + paymentId);
  if (!row) return;
  
  const btn = row.querySelector('button[onclick*="approvePayment"]');
  const rejectBtn = row.querySelector('button[onclick*="rejectPayment"]');
  if (!btn) return;
  
  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  if (rejectBtn) rejectBtn.disabled = true;
  btn.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin">hourglass_empty</span>';
  
  try {
    const resp = await fetch(`/admin/payments/${paymentId}/approve`, {
      method: 'POST',
      headers: { 'X-Admin-Key': adminKey }
    });
    
    if (resp.ok || resp.redirected) {
      row.remove();
      showMessage('✅ Đã approve payment thành công!', 'success');
      const tbody = row.closest('tbody');
      if (tbody && tbody.children.length === 0) {
        loadPendingPayments(adminKey);
      }
    } else {
      const data = await resp.json();
      throw new Error(data.error || 'Lỗi khi approve payment');
    }
  } catch (error) {
    alert('Lỗi: ' + error.message);
    btn.disabled = false;
    if (rejectBtn) rejectBtn.disabled = false;
    btn.innerHTML = originalHTML;
  }
}

async function rejectPayment(paymentId) {
  if (!confirm('Xác nhận reject payment này? Payment sẽ bị hủy và không được xử lý.')) {
    return;
  }
  
  const adminKey = document.getElementById('adminKey')?.value.trim() || '';
  if (!adminKey) {
    alert('Vui lòng nhập Admin Secret Key ở trên');
    return;
  }
  
  const row = document.getElementById('payment-row-' + paymentId);
  if (!row) return;
  
  const btn = row.querySelector('button[onclick*="rejectPayment"]');
  const approveBtn = row.querySelector('button[onclick*="approvePayment"]');
  if (!btn) return;
  
  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  if (approveBtn) approveBtn.disabled = true;
  btn.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin">hourglass_empty</span>';
  
  try {
    const resp = await fetch(`/admin/payments/${paymentId}/reject`, {
      method: 'POST',
      headers: { 'X-Admin-Key': adminKey }
    });
    
    if (resp.ok || resp.redirected) {
      row.remove();
      showMessage('✅ Đã reject payment thành công!', 'success');
      const tbody = row.closest('tbody');
      if (tbody && tbody.children.length === 0) {
        loadPendingPayments(adminKey);
      }
    } else {
      const data = await resp.json();
      throw new Error(data.error || 'Lỗi khi reject payment');
    }
  } catch (error) {
    alert('Lỗi: ' + error.message);
    btn.disabled = false;
    if (approveBtn) approveBtn.disabled = false;
    btn.innerHTML = originalHTML;
  }
}

function showMessage(message, type) {
  const div = document.createElement('div');
  div.className = type === 'success' 
    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-4 py-3 rounded-lg mb-4'
    : 'bg-red-500/20 text-red-400 border border-red-500/30 px-4 py-3 rounded-lg mb-4';
  div.textContent = message;
  const paymentsSection = document.querySelector('[id*="payment"], [id*="user"]').closest('section') || document.body;
  paymentsSection.insertBefore(div, paymentsSection.firstChild);
  setTimeout(() => div.remove(), 5000);
}

let currentUsersPage = 1;
let currentUserSearch = '';

async function loadUsersList(page = 1) {
  const adminKey = document.getElementById('adminKey')?.value.trim() || '';
  if (!adminKey) {
    const usersContainer = document.getElementById('usersContainer');
    if (usersContainer) {
      usersContainer.innerHTML = 
        '<p class="text-center text-red-400 py-10">Vui lòng nhập Admin Secret Key ở trên</p>';
    }
    return;
  }
  
  const search = document.getElementById('userSearchInput')?.value.trim() || '';
  currentUsersPage = page;
  currentUserSearch = search;
  
  try {
    let url = `/admin/users?page=${page}&per_page=20`;
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }
    
    const resp = await fetch(url, {
      headers: { 'X-Admin-Key': adminKey }
    });
    
    const usersContainer = document.getElementById('usersContainer');
    if (!usersContainer) return;
    
    if (!resp.ok) {
      if (resp.status === 403) {
        usersContainer.innerHTML = 
          '<p class="text-center text-red-400 py-10">❌ Admin key không hợp lệ. Vui lòng kiểm tra lại.</p>';
      } else {
        const data = await resp.json();
        throw new Error(data.error || 'Lỗi khi tải danh sách users');
      }
      return;
    }
    
    const data = await resp.json();
    const users = data.users || [];
    const pagination = data.pagination || {};
    
    if (users.length === 0) {
      usersContainer.innerHTML = 
        '<p class="text-center text-slate-400 py-10">Không tìm thấy user nào</p>';
      return;
    }
    
    // Render users table
    const tierLabels = { free: 'Free', premium: 'Premium', ultra: 'Ultra' };
    let html = '<div class="overflow-x-auto"><table class="w-full text-left border-collapse"><thead class="bg-surface-dark/50 text-slate-400 text-xs uppercase font-medium"><tr><th class="p-4">ID</th><th class="p-4">Email</th><th class="p-4">Tên</th><th class="p-4">Tier hiện tại</th><th class="p-4">Status</th><th class="p-4">Ngày tạo</th><th class="p-4 text-right">Thao tác</th></tr></thead><tbody class="text-sm divide-y divide-glass-border">';
    
    users.forEach(user => {
      const currentTier = user.current_tier ? tierLabels[user.current_tier] || user.current_tier : 'Chưa có';
      const dateStr = user.created_at ? new Date(user.created_at).toLocaleDateString('vi-VN') : 'N/A';
      
      const userEmailEscaped = (user.email || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const userTierEscaped = (user.current_tier || 'free').replace(/'/g, "\\'").replace(/"/g, '&quot;');
      
      const tierBadge = user.current_tier === 'premium'
        ? '<span class="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded text-xs font-bold uppercase">Premium</span>'
        : user.current_tier === 'ultra'
        ? '<span class="bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded text-xs font-bold uppercase">Ultra</span>'
        : '<span class="bg-slate-500/10 text-slate-400 border border-slate-500/20 px-2 py-0.5 rounded text-xs font-bold uppercase">Free</span>';
      
      html += `
        <tr class="hover:bg-white/5 transition-colors group" id="user-row-${user.id}">
          <td class="p-4 text-slate-300">${user.id}</td>
          <td class="p-4 font-medium text-white">${user.email}</td>
          <td class="p-4 text-slate-300">${user.full_name || 'N/A'}</td>
          <td class="p-4">${tierBadge}</td>
          <td class="p-4 text-slate-300">${user.status}</td>
          <td class="p-4 text-slate-300">${dateStr}</td>
          <td class="p-4 text-right">
            <div class="flex items-center justify-end gap-2 opacity-80 group-hover:opacity-100">
              <button class="h-8 w-8 rounded flex items-center justify-center bg-primary/20 text-primary hover:bg-primary hover:text-white transition-all border border-primary/30" onclick="showChangeTierModal(${user.id}, '${userEmailEscaped}', '${userTierEscaped}')" title="Đổi Tier">
                <span class="material-symbols-outlined text-[18px]">swap_horiz</span>
              </button>
              <button class="h-8 w-8 rounded flex items-center justify-center bg-rose-500/20 text-rose-500 hover:bg-rose-500 hover:text-white transition-all border border-rose-500/30" onclick="deleteUser(${user.id}, '${userEmailEscaped}')" title="Xóa">
                <span class="material-symbols-outlined text-[18px]">delete</span>
              </button>
            </div>
          </td>
        </tr>
      `;
    });
    
    html += '</tbody></table></div>';
    
    // Add pagination
    if (pagination.total_pages > 1) {
      html += '<div class="px-6 py-4 border-t border-glass-border flex justify-between items-center bg-surface-dark/30"><span class="text-xs text-slate-400">Trang ' + pagination.page + '/' + pagination.total_pages + ' - Tổng: ' + pagination.total + ' users</span><div class="flex gap-1">';
      
      if (pagination.page > 1) {
        html += `<button class="px-2 py-1 rounded border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500" onclick="loadUsersList(${pagination.page - 1})"><span class="material-symbols-outlined text-sm">chevron_left</span></button>`;
      }
      
      const startPage = Math.max(1, pagination.page - 2);
      const endPage = Math.min(pagination.total_pages, pagination.page + 2);
      
      if (startPage > 1) {
        html += `<button class="px-3 py-1 rounded border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 text-xs" onclick="loadUsersList(1)">1</button>`;
        if (startPage > 2) html += '<span class="px-2 text-slate-500">...</span>';
      }
      
      for (let i = startPage; i <= endPage; i++) {
        if (i === pagination.page) {
          html += `<button class="px-3 py-1 rounded bg-primary text-white text-xs font-bold">${i}</button>`;
        } else {
          html += `<button class="px-3 py-1 rounded border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 text-xs" onclick="loadUsersList(${i})">${i}</button>`;
        }
      }
      
      if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) html += '<span class="px-2 text-slate-500">...</span>';
        html += `<button class="px-3 py-1 rounded border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 text-xs" onclick="loadUsersList(${pagination.total_pages})">${pagination.total_pages}</button>`;
      }
      
      if (pagination.page < pagination.total_pages) {
        html += `<button class="px-2 py-1 rounded border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500" onclick="loadUsersList(${pagination.page + 1})"><span class="material-symbols-outlined text-sm">chevron_right</span></button>`;
      }
      
      html += '</div></div>';
    }
    
    usersContainer.innerHTML = html;
  } catch (error) {
    const usersContainer = document.getElementById('usersContainer');
    if (usersContainer) {
      usersContainer.innerHTML = 
        '<p class="text-center text-red-400 py-10">❌ Lỗi: ' + error.message + '</p>';
    }
  }
}

async function deleteUser(userId, userEmail) {
  const displayEmail = userEmail.replace(/'/g, "\\'");
  
  if (!confirm(`Bạn có chắc chắn muốn xóa user này?\n\nEmail: ${displayEmail}\nID: ${userId}\n\n⚠️ Hành động này không thể hoàn tác!`)) {
    return;
  }
  
  const adminKey = document.getElementById('adminKey')?.value.trim() || '';
  if (!adminKey) {
    alert('Vui lòng nhập Admin Secret Key ở trên');
    return;
  }
  
  try {
    const resp = await fetch(`/admin/users/${userId}/delete`, {
      method: 'POST',
      headers: { 
        'X-Admin-Key': adminKey,
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    const data = await resp.json();
    
    if (resp.ok && data.success) {
      alert('✅ ' + (data.message || 'Đã xóa user thành công!'));
      loadUsersList(currentUsersPage);
    } else {
      throw new Error(data.error || data.message || 'Lỗi khi xóa user');
    }
  } catch (error) {
    console.error('Error deleting user:', error);
    alert('Lỗi: ' + error.message);
  }
}

function showChangeTierModal(userId, userEmail, currentTier) {
  userEmail = userEmail.replace(/'/g, "\\'");
  
  const tierInput = prompt(`Đổi tier cho user:\n${userEmail}\n\nTier hiện tại: ${currentTier || 'Chưa có'}\n\nNhập tier mới (free/premium/ultra):`, currentTier || 'free');
  if (tierInput === null) return;
  
  const tier = tierInput.trim().toLowerCase();
  if (!tier) {
    alert('Tier không được để trống!');
    return;
  }
  
  if (!['free', 'premium', 'ultra'].includes(tier)) {
    alert('Tier không hợp lệ! Phải là: free, premium, hoặc ultra');
    return;
  }
  
  const notesInput = prompt('Ghi chú (tùy chọn, để trống nếu không có):', '');
  const notes = notesInput ? notesInput.trim() : '';
  
  changeUserTierDirectly(userId, tier, notes);
}

async function changeUserTierDirectly(userId, targetTier, notes) {
  const adminKey = document.getElementById('adminKey')?.value.trim() || '';
  if (!adminKey) {
    alert('Vui lòng nhập Admin Secret Key ở trên');
    return;
  }
  
  if (!confirm(`Xác nhận đổi tier user ID ${userId} sang ${targetTier.toUpperCase()}?`)) {
    return;
  }
  
  try {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('tier', targetTier);
    if (notes) formData.append('notes', notes);
    
    const resp = await fetch('/admin/users/change-tier', {
      method: 'POST',
      headers: { 
        'X-Admin-Key': adminKey,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    });
    
    const data = await resp.json();
    
    if (resp.ok && data.success) {
      alert('✅ ' + (data.message || 'Đã đổi tier thành công!'));
      loadUsersList(currentUsersPage);
    } else {
      throw new Error(data.error || data.message || 'Lỗi khi đổi tier');
    }
  } catch (error) {
    alert('Lỗi: ' + error.message);
  }
}

// Load users list when stats are loaded
const originalLoadStats = loadStats;
loadStats = function() {
  originalLoadStats();
  const adminKey = document.getElementById('adminKey')?.value.trim() || '';
  if (adminKey) {
    setTimeout(() => loadUsersList(1), 500);
  }
};

// Tab switching for Payments/Users
function switchTab(tabName) {
  const paymentsTab = document.getElementById('paymentsTab');
  const usersTab = document.getElementById('usersTab');
  const paymentsContent = document.getElementById('paymentsContent');
  const usersContent = document.getElementById('usersContent');
  
  if (tabName === 'payments') {
    if (paymentsTab) {
      paymentsTab.classList.add('border-primary', 'bg-primary/5', 'text-white');
      paymentsTab.classList.remove('border-transparent', 'text-slate-400');
    }
    if (usersTab) {
      usersTab.classList.remove('border-primary', 'bg-primary/5', 'text-white');
      usersTab.classList.add('border-transparent', 'text-slate-400');
    }
    if (paymentsContent) paymentsContent.style.display = 'block';
    if (usersContent) usersContent.style.display = 'none';
  } else {
    if (usersTab) {
      usersTab.classList.add('border-primary', 'bg-primary/5', 'text-white');
      usersTab.classList.remove('border-transparent', 'text-slate-400');
    }
    if (paymentsTab) {
      paymentsTab.classList.remove('border-primary', 'bg-primary/5', 'text-white');
      paymentsTab.classList.add('border-transparent', 'text-slate-400');
    }
    if (usersContent) usersContent.style.display = 'block';
    if (paymentsContent) paymentsContent.style.display = 'none';
  }
}
