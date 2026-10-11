// Smart Attendance - API Client Utility

const BASE_URL = (window.location.protocol.startsWith("http")) 
    ? window.location.origin 
    : "http://localhost:5000";

async function apiGet(endpoint) {
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`);
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.message || `API GET failed: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("GET Error:", error);
        return null;
    }
}

async function apiPost(endpoint, data) {
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const resData = await response.json().catch(() => null);
        if (!response.ok) {
            return resData || { success: false, message: `Request failed (${response.status})` };
        }
        return resData;
    } catch (error) {
        console.error("POST Error:", error);
        return { success: false, message: error.message || "Network error" };
    }
}

async function apiDelete(endpoint) {
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: "DELETE"
        });
        const resData = await response.json().catch(() => null);
        if (!response.ok) {
            return resData || { success: false, message: `Delete failed (${response.status})` };
        }
        return resData;
    } catch (error) {
        console.error("DELETE Error:", error);
        return { success: false, message: error.message || "Network error" };
    }
}

// Global Toast Notification Helper
function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("show");
    }, 10);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
