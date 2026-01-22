async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (username === "" || password === "") {
        alert("Please fill all fields");
        return;
    }

    const response = await apiPost("/login", { username, password });

    if (response && response.success) {
        window.location.href = "dashboard.html";
    } else {
        alert("Invalid credentials");
    }
}
