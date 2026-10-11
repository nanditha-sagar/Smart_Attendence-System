// Student Management Logic

let allStudents = [];

document.addEventListener("DOMContentLoaded", loadStudents);

async function loadStudents() {
    try {
        const students = await apiGet("/students");
        if (students && Array.isArray(students)) {
            allStudents = students;
            renderStudentsTable(allStudents);
        } else {
            renderStudentsTable([]);
        }
    } catch (err) {
        console.error("Failed to load students:", err);
        showToast("Error loading student records", "error");
    }
}

function renderStudentsTable(students) {
    const tbody = document.querySelector("#studentsTable tbody");
    if (!tbody) return;

    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No students registered yet. Fill the form above to add a student.</td></tr>`;
        return;
    }

    tbody.innerHTML = "";

    students.forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>#${s.id}</strong></td>
            <td>
                <div class="student-name-cell">
                    <span class="avatar-letter">${(s.name || 'S').charAt(0)}</span>
                    <span class="font-medium">${s.name}</span>
                </div>
            </td>
            <td><code>${s.roll}</code></td>
            <td>${s.department || 'Computer Science'}</td>
            <td>${s.email || '--'}</td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteStudent(${s.id}, '${escapeHtml(s.name)}')">
                        🗑️ Delete
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterStudentsTable() {
    const query = document.getElementById("studentSearchInput").value.toLowerCase().trim();
    if (!query) {
        renderStudentsTable(allStudents);
        return;
    }

    const filtered = allStudents.filter(s => 
        (s.name && s.name.toLowerCase().includes(query)) ||
        (s.roll && s.roll.toLowerCase().includes(query)) ||
        (s.department && s.department.toLowerCase().includes(query)) ||
        (s.id && s.id.toString().includes(query))
    );

    renderStudentsTable(filtered);
}

async function handleRegisterStudent(event) {
    event.preventDefault();

    const name = document.getElementById("newStudentName").value.trim();
    const roll = document.getElementById("newStudentRoll").value.trim();
    const dept = document.getElementById("newStudentDept").value.trim();
    const email = document.getElementById("newStudentEmail").value.trim();
    const idVal = document.getElementById("newStudentId").value.trim();

    if (!name || !roll) {
        showToast("Full Name and Roll Number are required.", "error");
        return;
    }

    const payload = {
        name: name,
        roll: roll,
        department: dept,
        email: email
    };

    if (idVal) {
        payload.id = parseInt(idVal, 10);
    }

    const submitBtn = document.getElementById("saveStudentBtn");
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = "Saving...";
    }

    const res = await apiPost("/students", payload);

    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = "Save & Register";
    }

    if (res && res.success) {
        showToast(res.message || "Student registered successfully!", "success");
        document.getElementById("addStudentForm").reset();
        loadStudents();
    } else {
        showToast(res?.message || "Failed to register student", "error");
    }
}

async function confirmDeleteStudent(studentId, studentName) {
    if (!confirm(`Are you sure you want to delete student "${studentName}" (ID: ${studentId}) and all their attendance records?`)) {
        return;
    }

    const res = await apiDelete(`/students/${studentId}`);
    if (res && res.success) {
        showToast(`Student #${studentId} deleted successfully.`, "success");
        loadStudents();
    } else {
        showToast(res?.message || "Failed to delete student", "error");
    }
}

async function trainModelAction() {
    showToast("Retraining face recognition model...", "info");
    const res = await apiPost("/train", {});
    if (res && res.success) {
        showToast(res.message || "Face model retrained successfully!", "success");
    } else {
        showToast(res?.message || "Retraining failed", "error");
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/'/g, "\\'");
}
