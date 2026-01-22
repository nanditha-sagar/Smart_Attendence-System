document.addEventListener("DOMContentLoaded", loadDashboard);

async function loadDashboard() {
    const data = await apiGet("/attendance/today");

    if (!data) return;

    document.getElementById("total").innerText = data.length;
    document.getElementById("present").innerText =
        data.filter(d => d.status === "Present").length;
    document.getElementById("absent").innerText =
        data.filter(d => d.status === "Absent").length;

    const table = document.getElementById("attendanceTable");
    table.innerHTML = "";

    data.forEach(d => {
        table.innerHTML += `
            <tr>
                <td>${d.name}</td>
                <td>${d.status}</td>
                <td>${d.time}</td>
            </tr>
        `;
    });
}
