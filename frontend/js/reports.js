// Attendance Reports Logic

document.addEventListener("DOMContentLoaded", () => {
    // Configure export button link
    const exportBtn = document.getElementById("exportCsvBtn");
    if (exportBtn) {
        exportBtn.href = `${BASE_URL}/attendance/export`;
    }

    generateReport();
});

async function generateReport() {
    const monthSelect = document.getElementById("month");
    const month = monthSelect ? monthSelect.value : "October";

    const reportTitle = document.getElementById("reportTitle");
    if (reportTitle) {
        reportTitle.innerText = month === "all" 
            ? "Overall Attendance History" 
            : `Attendance Summary - ${month}`;
    }

    const tbody = document.getElementById("reportTableBody");
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Calculating attendance metrics...</td></tr>`;
    }

    try {
        const result = await apiGet(`/attendance/report/${encodeURIComponent(month)}`);

        if (!result || !result.report) {
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No attendance data found for this selection.</td></tr>`;
            }
            return;
        }

        renderReportTable(result.report);
    } catch (err) {
        console.error("Error generating report:", err);
        showToast("Error retrieving attendance report", "error");
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Failed to load report data.</td></tr>`;
        }
    }
}

function renderReportTable(reports) {
    const tbody = document.getElementById("reportTableBody");
    if (!tbody) return;

    if (!reports || reports.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No student records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = "";

    reports.forEach(r => {
        const pctVal = typeof r.percent_val === "number" ? r.percent_val : parseFloat(r.percentage) || 0;
        
        let barColor = "var(--success)";
        if (pctVal < 60) {
            barColor = "var(--danger)";
        } else if (pctVal < 75) {
            barColor = "var(--warning)";
        }

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>#${r.id}</strong></td>
            <td>
                <div class="student-name-cell">
                    <span class="avatar-letter">${(r.name || 'S').charAt(0)}</span>
                    <span class="font-medium">${r.name}</span>
                </div>
            </td>
            <td><code>${r.roll}</code></td>
            <td>${r.department || 'Computer Science'}</td>
            <td>${r.total_days} days</td>
            <td class="text-success font-medium">${r.days_present}</td>
            <td class="text-danger font-medium">${r.days_absent}</td>
            <td>
                <div class="progress-container">
                    <div class="progress-bar-wrap">
                        <div class="progress-bar-fill" style="width: ${Math.min(100, pctVal)}%; background-color: ${barColor};"></div>
                    </div>
                    <span class="progress-text">${r.percentage}</span>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
