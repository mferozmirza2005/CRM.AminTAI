// ===============================
// Dashboard Data Loader
// ===============================

let charts = {};

async function loadDashboardData() {
    const token = localStorage.getItem("access");
    if (!token) {
        window.location.href = "/login/";
        return;
    }

    const res = await fetch("/api/dashboard/", {
        headers: { "Authorization": "Bearer " + token }
    });

    if (res.status === 401) {
        window.location.href = "/login/";
        return;
    }

    const data = await res.json();
    console.log("Dashboard data received:", data); // Debug log
    console.log("Deal stages:", data.deal_stages); // Debug log
    console.log("Lead statuses:", data.lead_statuses); // Debug log
    console.log("Trends:", data.trends); // Debug log
    const dashboard = document.getElementById("dashboardStats");

    // Header cards with modern design
    const icons = {
        Accounts: 'bi-building',
        Contacts: 'bi-person-lines-fill',
        Leads: 'bi-bullseye',
        Deals: 'bi-person-workspace',
        Campaigns: 'bi-megaphone',
        Tasks: 'bi-check2-square'
    };

    const cardsHTML = `
        <div class="row g-4 mb-4">
            ${Object.entries({
        Accounts: data.total_accounts,
        Contacts: data.total_contacts,
        Leads: data.total_leads,
        Deals: data.total_deals,
        Campaigns: data.total_campaigns,
        Tasks: data.total_tasks
    }).map(([key, val]) => `
                <div class="col-md-4 col-lg-2">
                    <div class="stat-card">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi ${icons[key]} text-primary fs-4 me-2"></i>
                        </div>
                        <div class="stat-value">${val || 0}</div>
                        <div class="stat-label">${key}</div>
                    </div>
                </div>
            `).join('')}
        </div>
        ${data.total_deal_value ? `
        <div class="row g-4 mb-4">
            <div class="col-12">
                <div class="card shadow-sm">
                    <div class="card-body">
                        <div class="d-flex align-items-center justify-content-between">
                            <div>
                                <h6 class="text-muted mb-1">Total Deal Value</h6>
                                <h3 class="mb-0 fw-bold text-primary">Rs. ${parseFloat(data.total_deal_value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h3>
                            </div>
                            <div class="text-end">
                                <div class="text-muted small">Last 7 Days</div>
                                <div class="h5 mb-0">
                                    <span class="badge bg-success">+${data.recent_deals_7d || 0}</span> deals
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
    `;

    let detailsHTML = "";

    if (data.role === "superuser") {
        detailsHTML += renderTableSection("Recent Campaigns", data.recent_campaigns, ["name", "budget", "created_at"]);
        detailsHTML += renderTableSection("Recent Leads", data.recent_leads, ["title", "status", "created_at"]);
        detailsHTML += renderTableSection("Recent Deals", data.recent_deals, ["title", "amount", "stage", "created_at"]);
    } else if (data.role === "admin") {
        detailsHTML += renderTableSection("Recent Accounts", data.recent_accounts, ["name", "region", "created_at"]);
        detailsHTML += renderTableSection("Recent Leads", data.recent_leads, ["title", "status", "created_at"]);
    } else if (data.role === "employee") {
        detailsHTML += renderTableSection("Assigned Leads", data.assigned_leads, ["title", "status", "created_at"]);
        detailsHTML += renderTableSection("Your Tasks", data.assigned_tasks, ["title", "due_date", "completed", "created_at"]);
    }

    dashboard.innerHTML = cardsHTML + detailsHTML;

    // Hook up dashboard table filter
    const filterInput = document.getElementById("dashboardFilter");
    const clearBtn = document.getElementById("clearDashboardFilter");
    if (filterInput) {
        const applyFilter = () => {
            const term = filterInput.value.trim().toLowerCase();
            document.querySelectorAll('#dashboardStats table tbody tr').forEach(tr => {
                const text = tr.textContent.toLowerCase();
                tr.style.display = term && !text.includes(term) ? 'none' : '';
            });
        };
        filterInput.addEventListener('input', () => {
            clearTimeout(window.__dashFilterTimer);
            window.__dashFilterTimer = setTimeout(applyFilter, 200);
        });
        clearBtn?.addEventListener('click', () => { filterInput.value = ''; applyFilter(); });
    }

    // Render analytics charts - always show charts section
    const chartsSection = document.getElementById("analyticsCharts");
    if (chartsSection) {
        chartsSection.style.display = "block";
        // Render charts after a short delay to ensure DOM is ready
        setTimeout(() => {
            if (typeof Chart !== 'undefined') {
                try {
                    renderAnalyticsCharts(data);
                } catch (error) {
                    console.error('Error rendering charts:', error);
                }
            } else {
                console.error('Chart.js library not loaded');
                chartsSection.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle me-2"></i>
                            Charts library failed to load. Please check your internet connection and refresh the page.
                        </div>
                    </div>
                `;
            }
        }, 200);
    }
}

function renderAnalyticsCharts(data) {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }

    console.log("Rendering charts with data:", {
        deal_stages: data.deal_stages,
        lead_statuses: data.lead_statuses,
        deal_value_by_stage: data.deal_value_by_stage,
        trends: data.trends
    }); // Debug log

    const chartColors = {
        primary: '#0d6efd',
        secondary: '#6c757d',
        success: '#198754',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#0dcaf0',
        purple: '#6f42c1',
        pink: '#d63384'
    };

    // Trends Chart (Line Chart) - show even if empty
    const trendsCtx = document.getElementById('trendsChart');
    if (trendsCtx) {
        if (!data.trends || !Array.isArray(data.trends) || data.trends.length === 0) {
            // Create default empty data
            data.trends = [
                { week: 'Week 1', accounts: 0, leads: 0, deals: 0 },
                { week: 'Week 2', accounts: 0, leads: 0, deals: 0 },
                { week: 'Week 3', accounts: 0, leads: 0, deals: 0 },
                { week: 'Week 4', accounts: 0, leads: 0, deals: 0 }
            ];
        }
        if (charts.trends) charts.trends.destroy();
        charts.trends = new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: data.trends.map(t => t.week),
                datasets: [
                    {
                        label: 'Accounts',
                        data: data.trends.map(t => t.accounts),
                        borderColor: chartColors.primary,
                        backgroundColor: chartColors.primary + '20',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Leads',
                        data: data.trends.map(t => t.leads),
                        borderColor: chartColors.success,
                        backgroundColor: chartColors.success + '20',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Deals',
                        data: data.trends.map(t => t.deals),
                        borderColor: chartColors.warning,
                        backgroundColor: chartColors.warning + '20',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    // Conversion Rate
    const conversionRateEl = document.getElementById('conversionRate');
    const conversionBarEl = document.getElementById('conversionBar');
    if (conversionRateEl) {
        const rate = data.conversion_rate !== undefined ? data.conversion_rate : 0;
        conversionRateEl.textContent = rate + '%';
        if (conversionBarEl) {
            conversionBarEl.style.width = rate + '%';
        }
    }

    // Deal Stages Chart (Bar Chart) - show even if empty
    const dealStagesCtx = document.getElementById('dealStagesChart');
    if (dealStagesCtx) {
        if (charts.dealStages) charts.dealStages.destroy();
        // Only use defaults if data.deal_stages is truly empty/undefined
        if (!data.deal_stages || (typeof data.deal_stages === 'object' && Object.keys(data.deal_stages).length === 0)) {
            // Check if we have any deals at all
            if (data.total_deals > 0) {
                // We have deals but no stage data - this shouldn't happen, but show empty chart
                data.deal_stages = {};
            } else {
                data.deal_stages = { 'PROSPECT': 0, 'QUALIFICATION': 0, 'PROPOSAL': 0, 'NEGOTIATION': 0, 'WON': 0, 'LOST': 0 };
            }
        }
        const stages = Object.keys(data.deal_stages);
        const counts = Object.values(data.deal_stages);
        charts.dealStages = new Chart(dealStagesCtx, {
            type: 'bar',
            data: {
                labels: stages,
                datasets: [{
                    label: 'Number of Deals',
                    data: counts,
                    backgroundColor: [
                        chartColors.primary,
                        chartColors.info,
                        chartColors.warning,
                        chartColors.success,
                        chartColors.danger,
                        chartColors.secondary
                    ],
                    borderColor: [
                        chartColors.primary,
                        chartColors.info,
                        chartColors.warning,
                        chartColors.success,
                        chartColors.danger,
                        chartColors.secondary
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    // Lead Status Chart (Doughnut Chart) - show even if empty
    const leadStatusCtx = document.getElementById('leadStatusChart');
    if (leadStatusCtx) {
        if (charts.leadStatus) charts.leadStatus.destroy();
        // Only use defaults if data.lead_statuses is truly empty/undefined
        if (!data.lead_statuses || (typeof data.lead_statuses === 'object' && Object.keys(data.lead_statuses).length === 0)) {
            // Check if we have any leads at all
            if (data.total_leads > 0) {
                // We have leads but no status data - this shouldn't happen, but show empty chart
                data.lead_statuses = {};
            } else {
                data.lead_statuses = { 'NEW': 0, 'CONTACTED': 0, 'QUALIFIED': 0, 'CONVERTED': 0, 'LOST': 0 };
            }
        }
        const statuses = Object.keys(data.lead_statuses);
        const statusCounts = Object.values(data.lead_statuses);
        charts.leadStatus = new Chart(leadStatusCtx, {
            type: 'doughnut',
            data: {
                labels: statuses,
                datasets: [{
                    data: statusCounts,
                    backgroundColor: [
                        chartColors.primary,
                        chartColors.info,
                        chartColors.warning,
                        chartColors.success,
                        chartColors.danger
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }

    // Deal Value by Stage Chart - show even if empty
    const dealValueCtx = document.getElementById('dealValueChart');
    if (dealValueCtx) {
        if (charts.dealValue) charts.dealValue.destroy();
        // Only use defaults if data.deal_value_by_stage is truly empty/undefined
        if (!data.deal_value_by_stage || (typeof data.deal_value_by_stage === 'object' && Object.keys(data.deal_value_by_stage).length === 0)) {
            // Check if we have any deals at all
            if (data.total_deals > 0) {
                // We have deals but no value data - this shouldn't happen, but show empty chart
                data.deal_value_by_stage = {};
            } else {
                data.deal_value_by_stage = { 'PROSPECT': 0, 'QUALIFICATION': 0, 'PROPOSAL': 0, 'NEGOTIATION': 0, 'WON': 0, 'LOST': 0 };
            }
        }
        const stages = Object.keys(data.deal_value_by_stage);
        const values = Object.values(data.deal_value_by_stage);
        charts.dealValue = new Chart(dealValueCtx, {
            type: 'bar',
            data: {
                labels: stages,
                datasets: [{
                    label: 'Total Value (Rs.)',
                    data: values,
                    backgroundColor: chartColors.success + '80',
                    borderColor: chartColors.success,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return 'Value: Rs.' + parseFloat(context.parsed.y).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return 'Rs.' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    // Campaign Performance Chart - show even if empty
    const campaignCtx = document.getElementById('campaignChart');
    if (campaignCtx) {
        if (!data.campaign_performance || data.campaign_performance.length === 0) {
            // Create empty placeholder
            data.campaign_performance = [{ id: 1, name: 'No campaigns', budget: 0, lead_count: 0 }];
        }
        if (charts.campaign) charts.campaign.destroy();
        const campaigns = data.campaign_performance.slice(0, 5); // Top 5
        charts.campaign = new Chart(campaignCtx, {
            type: 'bar',
            data: {
                labels: campaigns.map(c => c.name || 'Campaign ' + c.id),
                datasets: [
                    {
                        label: 'Leads Generated',
                        data: campaigns.map(c => c.lead_count || 0),
                        backgroundColor: chartColors.info,
                        borderColor: chartColors.info,
                        borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Budget (Rs.)',
                        data: campaigns.map(c => parseFloat(c.budget || 0)),
                        backgroundColor: chartColors.warning,
                        borderColor: chartColors.warning,
                        borderWidth: 2,
                        yAxisID: 'y1',
                        type: 'line'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            callback: function (value) {
                                return 'Rs.' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

function renderTableSection(title, items, cols) {
    if (!items?.length) return "";
    const headers = cols.map(c => {
        const label = c.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
        return `<th>${label}</th>`;
    }).join("");
    const rows = items.map(i => {
        return `<tr>${cols.map(c => {
            let value = i[c] ?? "-";
            if (c.includes('date') || c.includes('created_at') || c.includes('due_date')) {
                if (value !== "-" && value) {
                    value = new Date(value).toLocaleDateString();
                }
            } else if (c === 'amount' || c === 'budget') {
                if (value !== "-" && value !== null && value !== undefined) {
                    value = 'Rs.' + parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                }
            } else if (c === 'completed') {
                value = value ? '✅' : '❌';
            }
            return `<td>${value}</td>`;
        }).join("")}</tr>`;
    }).join("");
    return `
        <div class="card mt-4 shadow-sm">
            <div class="card-header">
                <i class="bi bi-list-ul me-2"></i>${title}
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead><tr>${headers}</tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

// ===============================
// Initialization
// ===============================
document.addEventListener("DOMContentLoaded", loadDashboardData);
