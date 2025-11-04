// ===============================
// Dashboard Data Loader
// ===============================

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
    `;

    let detailsHTML = "";

    if (data.role === "superuser") {
        detailsHTML += renderTableSection("Recent Campaigns", data.recent_campaigns, ["name", "region", "created_at"]);
        detailsHTML += renderTableSection("Recent Leads", data.recent_leads, ["name", "status", "created_at"]);
        detailsHTML += renderTableSection("Recent Deals", data.recent_deals, ["title", "value", "stage", "created_at"]);
    } else if (data.role === "admin") {
        detailsHTML += renderTableSection("Recent Accounts", data.recent_accounts, ["name", "region", "created_at"]);
        detailsHTML += renderTableSection("Recent Leads", data.recent_leads, ["name", "status", "created_at"]);
    } else if (data.role === "employee") {
        detailsHTML += renderTableSection("Assigned Leads", data.assigned_leads, ["name", "status", "created_at"]);
        detailsHTML += renderTableSection("Your Tasks", data.assigned_tasks, ["title", "due_date", "status"]);
    }

    dashboard.innerHTML = cardsHTML + detailsHTML;
}

function renderTableSection(title, items, cols) {
    if (!items?.length) return "";
    const headers = cols.map(c => {
        const label = c.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
        return `<th>${label}</th>`;
    }).join("");
    const rows = items.map(i =>
        `<tr>${cols.map(c => {
            let value = i[c] ?? "-";
            if (c.includes('date') || c.includes('created_at') || c.includes('due_date')) {
                if (value !== "-" && value) {
                    value = new Date(value).toLocaleDateString();
                }
            }
            return `<td>${value}</td>`;
        }).join("")}</tr>`
    ).join("");
    return `
        <div class="card mt-4">
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
