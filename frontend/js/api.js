const BASE_URL = "http://localhost:5000";

async function apiGet(endpoint) {
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error("API GET failed");
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

        if (!response.ok) {
            throw new Error("API POST failed");
        }

        return await response.json();
    } catch (error) {
        console.error("POST Error:", error);
        return null;
    }
}
