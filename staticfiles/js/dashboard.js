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

    // Header cards
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
                    <div class="card shadow-sm border-0">
                        <div class="card-body text-center">
                            <h4 class="fw-bold text-primary">${val}</h4>
                            <p class="text-muted mb-0">${key}</p>
                        </div>
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
    const headers = cols.map(c => `<th>${c.replace("_", " ").toUpperCase()}</th>`).join("");
    const rows = items.map(i =>
        `<tr>${cols.map(c => `<td>${i[c] ?? "-"}</td>`).join("")}</tr>`
    ).join("");
    return `
        <div class="card mt-4 shadow-sm border-0">
            <div class="card-header bg-light fw-semibold">${title}</div>
            <div class="card-body p-0">
                <table class="table table-hover mb-0">
                    <thead class="table-light"><tr>${headers}</tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </div>
    `;
}

// ===============================
// Initialization
// ===============================
document.addEventListener("DOMContentLoaded", loadDashboardData);
