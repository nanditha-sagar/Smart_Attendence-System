// Authentication Handling

async function login() {
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const loginBtn = document.getElementById("loginBtn");

    const username = usernameInput ? usernameInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value.trim() : "";

    if (!username || !password) {
        showToast("Please enter both username and password.", "error");
        return;
    }

    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerText = "Authenticating...";
    }

    try {
        const response = await apiPost("/login", { username, password });

        if (response && response.success) {
            localStorage.setItem("user", JSON.stringify(response.user || { username }));
            showToast("Login successful! Redirecting...", "success");
            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 500);
        } else {
            showToast(response?.message || "Invalid credentials", "error");
            if (loginBtn) {
                loginBtn.disabled = false;
                loginBtn.innerText = "Login";
            }
        }
    } catch (err) {
        showToast("Server connection error", "error");
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerText = "Login";
        }
    }
}

function logout() {
    localStorage.removeItem("user");
    window.location.href = "index.html";
}

// Allow Enter key submit on password field
document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById("password");
    if (passwordInput) {
        passwordInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                login();
            }
        });
    }
});
