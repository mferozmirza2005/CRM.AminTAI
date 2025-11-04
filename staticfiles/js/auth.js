// ===============================
// Authentication Utility Functions
// ===============================

function authHeaders() {
    const token = localStorage.getItem("access");
    return token ? { "Authorization": "Bearer " + token } : {};
}

// Save JWT tokens in localStorage
function saveTokens(access, refresh) {
    localStorage.setItem("access", access);
    localStorage.setItem("refresh", refresh);
}

// Get stored access token
function getAccessToken() {
    return localStorage.getItem("access");
}

// Get stored refresh token
function getRefreshToken() {
    return localStorage.getItem("refresh");
}

// Remove tokens (logout)
function clearTokens() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
}

// Check login status
function isAuthenticated() {
    return !!getAccessToken();
}

// Redirect helper
function redirectTo(url) {
    window.location.href = url;
}

// ===============================
// Token Refresh Handling
// ===============================

async function refreshAccessToken() {
    const refresh = getRefreshToken();
    if (!refresh) {
        clearTokens();
        redirectTo("/login/");
        return;
    }

    try {
        const response = await fetch("/api/auth/login/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh }),
        });
        if (response.ok) {
            const data = await response.json();
            saveTokens(data.access, refresh);
        } else {
            clearTokens();
            redirectTo("/login/");
        }
    } catch (err) {
        console.error("Error refreshing token:", err);
        clearTokens();
        redirectTo("/login/");
    }
}

// ===============================
// Logout Functionality
// ===============================

async function logoutUser() {
    const refresh = getRefreshToken();
    if (!refresh) {
        clearTokens();
        redirectTo("/login/");
        return;
    }

    try {
        await fetch("/api/auth/logout/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh }),
        });
    } catch (err) {
        console.warn("Logout error:", err);
    } finally {
        clearTokens();
        redirectTo("/login/");
    }
}

// Attach logout handler to button
document.addEventListener("DOMContentLoaded", () => {
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logoutUser();
        });
    }
});
