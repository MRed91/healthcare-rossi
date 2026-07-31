const currentUser = getUser();
if (!currentUser) {
    window.location.href = "/login.html?next=%2Farea-personale.html";
} else if (currentUser.role === "admin") {
    window.location.href = "/admin.html";
}

function formatDate(iso) {
    return new Date(iso).toLocaleString("it-IT", { dateStyle: "medium", timeStyle: "short" });
}

function statusBadge(status) {
    return `<span class="badge badge-${status}">${status}</span>`;
}

function showPageMessage(type, text) {
    const box = document.getElementById("page-message");
    box.className = "alert alert-" + type;
    box.textContent = text;
    box.hidden = false;
}

async function cancelAppointment(id) {
    if (!confirm("Vuoi annullare questa prenotazione?")) return;
    try {
        await apiSend("POST", `/api/appointments/${id}/cancel`);
        showPageMessage("success", "Prenotazione annullata.");
        await loadAppointments();
    } catch (err) {
        showPageMessage("error", err.message);
    }
}

async function loadAppointments() {
    const page = await apiGet("/api/appointments?size=100");
    const now = new Date();
    const upcoming = document.getElementById("upcoming-body");
    const past = document.getElementById("past-body");
    upcoming.innerHTML = "";
    past.innerHTML = "";

    for (const appt of page.items) {
        const when = new Date(appt.scheduled_at);
        const doctor = `${appt.doctor.last_name} (${appt.doctor.specialization})`;
        const reason = appt.reason || "-";
        if (when >= now && appt.status === "prenotata") {
            const row = document.createElement("tr");
            row.innerHTML = `<td>${formatDate(appt.scheduled_at)}</td><td>${doctor}</td>` +
                `<td>${reason}</td><td>${statusBadge(appt.status)}</td>` +
                `<td><button class="btn-danger" data-id="${appt.id}">Annulla</button></td>`;
            upcoming.appendChild(row);
        } else {
            const row = document.createElement("tr");
            row.innerHTML = `<td>${formatDate(appt.scheduled_at)}</td><td>${doctor}</td>` +
                `<td>${reason}</td><td>${statusBadge(appt.status)}</td>`;
            past.appendChild(row);
        }
    }

    document.getElementById("upcoming-empty").hidden = upcoming.children.length > 0;
    document.getElementById("past-empty").hidden = past.children.length > 0;

    upcoming.querySelectorAll("button[data-id]").forEach((btn) => {
        btn.addEventListener("click", () => cancelAppointment(btn.dataset.id));
    });
}

if (currentUser && currentUser.role === "patient") {
    const patient = currentUser.patient;
    document.getElementById("welcome").textContent =
        `Ciao ${patient.first_name}, qui trovi le tue prenotazioni al Centro Medico Rossi.`;
    loadAppointments().catch((err) => showPageMessage("error", err.message));
}
