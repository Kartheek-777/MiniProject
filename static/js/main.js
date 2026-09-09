// Placement Copilot Core JavaScript & Real-Time Engine
document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss Django message alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // Initialize Real-Time Toast Notification Poller
    startRealTimePoller();
});

// Toast Notification Helper
function showPlacementToast(title, bodyText, iconClass = 'bi-stars text-primary', bgClass = 'bg-white') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 shadow-lg rounded-4 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body p-3">
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <i class="bi ${iconClass} fs-5"></i>
                        <strong class="me-auto text-dark small">${title}</strong>
                        <small class="text-muted" style="font-size: 0.7rem;">Just Now</small>
                    </div>
                    <p class="mb-0 text-secondary small" style="font-size: 0.8rem; line-height: 1.4;">${bodyText}</p>
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(toastId);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 6000 });
    bsToast.show();

    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

// Periodic Real-Time API Poller (polls every 20s)
let pollerInterval = null;
function startRealTimePoller() {
    // Run once after 5s
    setTimeout(fetchRealTimeActivity, 5000);
    // Poll every 25s
    pollerInterval = setInterval(fetchRealTimeActivity, 25000);
}

async function fetchRealTimeActivity() {
    try {
        const response = await fetch('/dashboard/api/activity/');
        if (!response.ok) return;
        const data = await response.json();

        if (data && data.live_tip) {
            // Show periodic placement tip
            showPlacementToast('AI Placement Insight', data.live_tip, 'bi-lightbulb-fill text-warning');
        }
    } catch (e) {
        // Silent catch for background poller
    }
}

