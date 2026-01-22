document.addEventListener("DOMContentLoaded", loadStudents);

async function loadStudents() {
    const students = await apiGet("/students");

    if (!students) return;

    const tbody = document.querySelector("#studentsTable tbody");
    tbody.innerHTML = "";

    students.forEach(s => {
        tbody.innerHTML += `
            <tr>
                <td>${s.id}</td>
                <td>${s.name}</td>
                <td>${s.roll}</td>
            </tr>
        `;
    });
}
