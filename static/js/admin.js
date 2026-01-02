// Real Estate Net Admin JavaScript
// Global variables
const ADMIN_CONFIG = {
    csrfToken: document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
    apiBaseUrl: '/admin/api/',
    theme: {
        primary: '#0033A0',
        secondary: '#DC143C',
        success: '#28a745',
        warning: '#ffc107',
        danger: '#dc3545'
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAdmin();
});

function initializeAdmin() {
    // Initialize DataTables
    initializeDataTables();

    // Initialize tooltips
    initializeTooltips();

    // Initialize form validations
    initializeFormValidations();

    // Initialize chart components
    initializeCharts();

    // Initialize real-time updates
    initializeRealTimeUpdates();

    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();

    console.log('Real Estate Net Admin initialized');
}

// DataTables Initialization
function initializeDataTables() {
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.data-table').each(function() {
            const table = $(this);
            const config = {
                responsive: true,
                pageLength: 25,
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                },
                initComplete: function() {
                    // Add custom styling
                    $(this).addClass('fade-in');
                }
            };

            // Check for server-side processing
            if (table.data('server-side')) {
                config.serverSide = true;
                config.ajax = {
                    url: table.data('ajax-url'),
                    type: 'POST',
                    headers: {
                        'X-CSRFToken': ADMIN_CONFIG.csrfToken
                    }
                };
            }

            table.DataTable(config);
        });
    }
}

// Tooltip Initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Form Validation
function initializeFormValidations() {
    const forms = document.querySelectorAll('.admin-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showToast('Please correct the errors in the form', 'error');
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    });

    return isValid;
}

// Chart Initialization
function initializeCharts() {
    if (typeof Chart !== 'undefined') {
        // Property views chart
        const propertyChartCanvas = document.getElementById('propertyViewsChart');
        if (propertyChartCanvas) {
            initializePropertyViewsChart(propertyChartCanvas);
        }

        // Revenue chart
        const revenueChartCanvas = document.getElementById('revenueChart');
        if (revenueChartCanvas) {
            initializeRevenueChart(revenueChartCanvas);
        }

        // User growth chart
        const userGrowthChartCanvas = document.getElementById('userGrowthChart');
        if (userGrowthChartCanvas) {
            initializeUserGrowthChart(userGrowthChartCanvas);
        }
    }
}

function initializePropertyViewsChart(canvas) {
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: window.chartData?.labels || [],
            datasets: [{
                label: 'Property Views',
                data: window.chartData?.values || [],
                borderColor: ADMIN_CONFIG.theme.primary,
                backgroundColor: 'rgba(0, 51, 160, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Property Views Over Time'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function initializeRevenueChart(canvas) {
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: window.revenueData?.labels || [],
            datasets: [{
                label: 'Revenue (NPR)',
                data: window.revenueData?.values || [],
                backgroundColor: ADMIN_CONFIG.theme.secondary,
                borderColor: ADMIN_CONFIG.theme.secondary,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'NPR ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function initializeUserGrowthChart(canvas) {
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Buyers', 'Brokers', 'Agents', 'Premium Users'],
            datasets: [{
                data: window.userData?.values || [0, 0, 0, 0],
                backgroundColor: [
                    ADMIN_CONFIG.theme.primary,
                    ADMIN_CONFIG.theme.secondary,
                    '#28a745',
                    '#ffc107'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: {
                    display: true,
                    text: 'User Distribution'
                }
            }
        }
    });
}

// Real-time Updates
function initializeRealTimeUpdates() {
    // Update stats every 5 minutes
    setInterval(updateDashboardStats, 300000);

    // WebSocket connection for real-time notifications (if implemented)
    initializeWebSocketConnection();
}

function updateDashboardStats() {
    fetch(ADMIN_CONFIG.apiBaseUrl + 'stats/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': ADMIN_CONFIG.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        updateStatsDisplay(data);
    })
    .catch(error => {
        console.error('Failed to update stats:', error);
    });
}

function updateStatsDisplay(data) {
    // Update stat cards with new data
    Object.keys(data).forEach(key => {
        const element = document.getElementById(`stat-${key}`);
        if (element) {
            element.textContent = data[key];
            element.classList.add('fade-in');
        }
    });
}

function initializeWebSocketConnection() {
    // Placeholder for WebSocket implementation
    // This would connect to a Django Channels WebSocket for real-time updates
    console.log('WebSocket connection placeholder');
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save forms
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('button[type="submit"], .btn-save');
            if (saveBtn) {
                saveBtn.click();
            }
        }

        // Ctrl/Cmd + F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.querySelector('.dataTables_filter input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

// AJAX Helper Functions
function ajaxPost(url, data, successCallback, errorCallback) {
    return $.ajax({
        url: url,
        method: 'POST',
        data: data,
        headers: {
            'X-CSRFToken': ADMIN_CONFIG.csrfToken
        },
        success: function(response) {
            if (response.success) {
                showToast(response.message || 'Operation successful', 'success');
                if (successCallback) successCallback(response);
            } else {
                showToast(response.message || 'Operation failed', 'error');
                if (errorCallback) errorCallback(response);
            }
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.message || 'An error occurred';
            showToast(errorMsg, 'error');
            if (errorCallback) errorCallback(xhr);
        }
    });
}

function ajaxGet(url, successCallback, errorCallback) {
    return $.ajax({
        url: url,
        method: 'GET',
        success: successCallback,
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.message || 'Failed to load data';
            showToast(errorMsg, 'error');
            if (errorCallback) errorCallback(xhr);
        }
    });
}

// Toast Notifications
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    document.getElementById('toast-container').appendChild(toastEl);

    const toast = new bootstrap.Toast(toastEl);
    toast.show();

    // Auto remove after duration
    setTimeout(() => {
        toastEl.remove();
    }, duration);
}

// Bulk Operations
function initializeBulkOperations() {
    // Select all checkbox
    document.addEventListener('change', function(e) {
        if (e.target.matches('.select-all-checkbox')) {
            const checkboxes = document.querySelectorAll('.row-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
            updateBulkActionsVisibility();
        }
    });

    // Individual checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.matches('.row-checkbox')) {
            updateBulkActionsVisibility();
        }
    });
}

function updateBulkActionsVisibility() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    const bulkActions = document.querySelectorAll('.bulk-action');

    bulkActions.forEach(action => {
        action.style.display = checkedBoxes.length > 0 ? 'inline-block' : 'none';
    });
}

// Property Management Functions
function approveProperty(propertyId) {
    ajaxPost(`${ADMIN_CONFIG.apiBaseUrl}property/approve/`, { id: propertyId }, function() {
        location.reload();
    });
}

function rejectProperty(propertyId, reason) {
    const reasonText = reason || prompt('Rejection reason:');
    if (reasonText) {
        ajaxPost(`${ADMIN_CONFIG.apiBaseUrl}property/reject/`, {
            id: propertyId,
            reason: reasonText
        }, function() {
            location.reload();
        });
    }
}

function togglePremium(propertyId) {
    ajaxPost(`${ADMIN_CONFIG.apiBaseUrl}property/toggle-premium/`, { id: propertyId }, function(response) {
        const btn = document.querySelector(`[data-property-id="${propertyId}"] .premium-toggle`);
        if (btn) {
            btn.textContent = response.is_premium ? 'Remove Premium' : 'Make Premium';
            btn.className = response.is_premium ? 'btn btn-warning' : 'btn btn-success';
        }
        showToast('Premium status updated', 'success');
    });
}

// User Management Functions
function banUser(userId) {
    if (confirm('Are you sure you want to ban this user?')) {
        ajaxPost(`${ADMIN_CONFIG.apiBaseUrl}user/ban/`, { id: userId }, function() {
            location.reload();
        });
    }
}

function verifyUser(userId) {
    ajaxPost(`${ADMIN_CONFIG.apiBaseUrl}user/verify/`, { id: userId }, function() {
        location.reload();
    });
}

// Modal Management
function showModal(content, title = 'Details') {
    const modal = document.getElementById('admin-modal');
    if (modal) {
        modal.querySelector('.modal-title').textContent = title;
        modal.querySelector('.modal-body').innerHTML = content;
        new bootstrap.Modal(modal).show();
    }
}

// Export Functions
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const rowData = [];
        const cols = row.querySelectorAll('td, th');

        cols.forEach(col => {
            rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
        });

        csv.push(rowData.join(','));
    });

    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');

    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename || 'export.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Utility Functions
function formatCurrency(amount, currency = 'NPR') {
    return `${currency} ${parseFloat(amount).toLocaleString()}`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize bulk operations
initializeBulkOperations();

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Admin JavaScript error:', e.error);
    showToast('An error occurred. Please refresh the page.', 'error');
});

// Service worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/admin-sw.js')
        .then(registration => {
            console.log('Admin ServiceWorker registered');
        })
        .catch(error => {
            console.log('Admin ServiceWorker registration failed');
        });
}
