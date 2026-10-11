// Smart Attendance Dashboard Logic

let allAttendanceRecords = [];
let cameraActive = false;
let autoRefreshTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    // Format and display current date
    const dateBadge = document.getElementById("currentDateBadge");
    if (dateBadge) {
        const today = new Date();
        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        dateBadge.innerText = today.toLocaleDateString(undefined, options);
    }

    loadDashboard();
});

async function loadDashboard() {
    try {
        // 1. Fetch attendance records
        const data = await apiGet("/attendance/today");
        if (data && Array.isArray(data)) {
            allAttendanceRecords = data;
            renderAttendanceTable(allAttendanceRecords);
            populateStudentDropdown(allAttendanceRecords);
        }

        // 2. Fetch stats
        const stats = await apiGet("/attendance/stats");
        if (stats) {
            document.getElementById("total").innerText = stats.total ?? 0;
            document.getElementById("present").innerText = stats.present ?? 0;
            document.getElementById("absent").innerText = stats.absent ?? 0;
            document.getElementById("rate").innerText = stats.rate ?? "0%";
        } else if (allAttendanceRecords.length > 0) {
            // Local fallback calculation
            const total = allAttendanceRecords.length;
            const present = allAttendanceRecords.filter(d => d.status === "Present").length;
            const absent = total - present;
            document.getElementById("total").innerText = total;
            document.getElementById("present").innerText = present;
            document.getElementById("absent").innerText = absent;
            document.getElementById("rate").innerText = `${((present / total) * 100).toFixed(1)}%`;
        }
    } catch (err) {
        console.error("Dashboard load failed:", err);
        showToast("Error loading dashboard data", "error");
    }
}

function renderAttendanceTable(records) {
    const tableBody = document.getElementById("attendanceTable");
    if (!tableBody) return;

    if (!records || records.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No student records found. Add students first.</td></tr>`;
        return;
    }

    tableBody.innerHTML = "";

    records.forEach(r => {
        const isPresent = r.status === "Present";
        const badgeClass = isPresent ? "badge-present" : "badge-absent";
        const actionBtn = isPresent
            ? `<span class="text-muted text-sm">Checked In</span>`
            : `<button class="btn btn-sm btn-outline-success" onclick="markRowPresent(${r.id})">Mark Present</button>`;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>#${r.id}</strong></td>
            <td>
                <div class="student-name-cell">
                    <span class="avatar-letter">${(r.name || 'S').charAt(0)}</span>
                    <span>${r.name}</span>
                </div>
            </td>
            <td><code>${r.roll}</code></td>
            <td>${r.department || 'Computer Science'}</td>
            <td><span class="status-badge ${badgeClass}">${r.status}</span></td>
            <td>${r.time || '--'}</td>
            <td>${actionBtn}</td>
        `;
        tableBody.appendChild(tr);
    });
}

function populateStudentDropdown(records) {
    const select = document.getElementById("studentSelect");
    if (!select) return;

    select.innerHTML = '<option value="">-- Choose Student --</option>';
    records.forEach(r => {
        const opt = document.createElement("option");
        opt.value = r.id;
        opt.textContent = `${r.name} (${r.roll})`;
        select.appendChild(opt);
    });
}

function filterAttendanceTable() {
    const query = document.getElementById("searchInput").value.toLowerCase().trim();
    if (!query) {
        renderAttendanceTable(allAttendanceRecords);
        return;
    }

    const filtered = allAttendanceRecords.filter(r => 
        (r.name && r.name.toLowerCase().includes(query)) ||
        (r.roll && r.roll.toLowerCase().includes(query)) ||
        (r.department && r.department.toLowerCase().includes(query)) ||
        (r.id && r.id.toString().includes(query))
    );

    renderAttendanceTable(filtered);
}

function toggleCamera() {
    const feed = document.getElementById("cameraFeed");
    const placeholder = document.getElementById("cameraPlaceholder");
    const btn = document.getElementById("toggleCamBtn");
    const badge = document.getElementById("camStatusBadge");

    if (!cameraActive) {
        // Start streaming
        feed.src = `${BASE_URL}/video_feed?t=${Date.now()}`;
        feed.style.display = "block";
        placeholder.style.display = "none";
        btn.innerText = "Stop Scanner";
        btn.className = "btn btn-danger btn-sm";
        badge.innerText = "Active & Scanning";
        badge.className = "status-badge badge-active";
        cameraActive = true;
        showToast("Camera scanner activated. Auto-attendance enabled.", "info");

        // Periodically refresh attendance table during live video scan
        autoRefreshTimer = setInterval(() => {
            loadDashboard();
        }, 5000);
    } else {
        // Stop streaming
        feed.src = "";
        feed.style.display = "none";
        placeholder.style.display = "flex";
        btn.innerText = "Start Scanner";
        btn.className = "btn btn-primary btn-sm";
        badge.innerText = "Camera Standby";
        badge.className = "status-badge badge-idle";
        cameraActive = false;
        if (autoRefreshTimer) {
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = null;
        }
        showToast("Camera scanner paused.", "info");
    }
}

async function manualMarkAttendance() {
    const select = document.getElementById("studentSelect");
    const studentId = select ? select.value : null;

    if (!studentId) {
        showToast("Please choose a student from the dropdown.", "error");
        return;
    }

    const res = await apiPost("/attendance/mark", { id: studentId });
    if (res && res.success) {
        showToast(res.message || "Attendance marked successfully!", "success");
        loadDashboard();
    } else {
        showToast(res?.message || "Failed to mark attendance", "error");
    }
}

async function markRowPresent(studentId) {
    const res = await apiPost("/attendance/mark", { id: studentId });
    if (res && res.success) {
        showToast(res.message || "Attendance marked!", "success");
        loadDashboard();
    } else {
        showToast(res?.message || "Failed to mark attendance", "error");
    }
}

async function retrainModel() {
    showToast("Training face recognizer model...", "info");
    const res = await apiPost("/train", {});
    if (res && res.success) {
        showToast(res.message || "Face model trained successfully!", "success");
    } else {
        showToast(res?.message || "Training failed", "error");
    }
}
