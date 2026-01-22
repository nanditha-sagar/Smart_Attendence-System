async function generateReport() {
    const month = document.getElementById("month").value;
    const result = await apiGet(`/attendance/report/${month}`);

    if (!result) return;

    const table = document.getElementById("reportTable");
    table.innerHTML = `
        <tr>
            <th>Name</th>
            <th>Attendance %</th>
        </tr>
    `;

    result.report.forEach(r => {
        table.innerHTML += `
            <tr>
                <td>${r.name}</td>
                <td>${r.percentage}</td>
            </tr>
        `;
    });
}
