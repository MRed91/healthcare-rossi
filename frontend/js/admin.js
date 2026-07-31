const adminUser = getUser();
if (!adminUser || adminUser.role !== "admin") {
    window.location.href = "/login.html?next=%2Fadmin.html";
}

function showPageMessage(type, text) {
    const box = document.getElementById("page-message");
    box.className = "alert alert-" + type;
    box.textContent = text;
    box.hidden = false;
    setTimeout(() => { box.hidden = true; }, 4000);
}

function formatTime(iso) {
    return iso.slice(11, 16);
}

function statusBadge(status) {
    return `<span class="badge badge-${status}">${status}</span>`;
}

// --- tab ---

document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        for (const name of ["agenda", "patients", "doctors"]) {
            document.getElementById("tab-" + name).hidden = name !== btn.dataset.tab;
        }
    });
});

// --- agenda ---

const agendaDay = document.getElementById("agenda-day");
const agendaDoctor = document.getElementById("agenda-doctor");

async function loadAgenda() {
    let path = `/api/appointments?size=100&day=${agendaDay.value}`;
    if (agendaDoctor.value) path += `&doctor_id=${agendaDoctor.value}`;
    const page = await apiGet(path);
    const body = document.getElementById("agenda-body");
    body.innerHTML = "";
    for (const appt of page.items) {
        const row = document.createElement("tr");
        const actions = appt.status === "prenotata"
            ? `<button class="btn-secondary btn-small" data-action="complete" data-id="${appt.id}">Completata</button>
               <button class="btn-danger" data-action="cancel" data-id="${appt.id}">Annulla</button>`
            : "";
        row.innerHTML = `<td>${formatTime(appt.scheduled_at)}</td>` +
            `<td>${appt.doctor.last_name} (${appt.doctor.specialization})</td>` +
            `<td>${appt.patient.last_name} ${appt.patient.first_name}</td>` +
            `<td>${appt.reason || "-"}</td><td>${statusBadge(appt.status)}</td><td>${actions}</td>`;
        body.appendChild(row);
    }
    document.getElementById("agenda-empty").hidden = body.children.length > 0;

    body.querySelectorAll("button[data-id]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const verb = btn.dataset.action === "cancel" ? "annullare" : "completare";
            if (!confirm(`Confermi di voler ${verb} questa prenotazione?`)) return;
            try {
                await apiSend("POST", `/api/appointments/${btn.dataset.id}/${btn.dataset.action}`);
                await loadAgenda();
            } catch (err) {
                showPageMessage("error", err.message);
            }
        });
    });
}

async function loadAgendaDoctors() {
    const page = await apiGet("/api/doctors?size=100");
    for (const doc of page.items) {
        const option = document.createElement("option");
        option.value = doc.id;
        option.textContent = `${doc.last_name} ${doc.first_name}`;
        agendaDoctor.appendChild(option);
    }
}

agendaDay.value = new Date().toISOString().slice(0, 10);
agendaDay.addEventListener("change", loadAgenda);
agendaDoctor.addEventListener("change", loadAgenda);

// --- pazienti ---

const patientSearch = document.getElementById("patient-search");
const patientForm = document.getElementById("patient-form");

function fillPatientForm(p) {
    document.getElementById("patient-id").value = p ? p.id : "";
    document.getElementById("patient-form-title").textContent =
        p ? `Modifica paziente: ${p.last_name} ${p.first_name}` : "Nuovo paziente";
    document.getElementById("p-first").value = p ? p.first_name : "";
    document.getElementById("p-last").value = p ? p.last_name : "";
    document.getElementById("p-cf").value = p ? p.fiscal_code : "";
    document.getElementById("p-birth").value = p ? p.birth_date : "";
    document.getElementById("p-email").value = p ? p.email : "";
    document.getElementById("p-phone").value = p && p.phone ? p.phone : "";
}

async function loadPatients() {
    const q = patientSearch.value ? `&q=${encodeURIComponent(patientSearch.value)}` : "";
    const page = await apiGet(`/api/patients?size=50${q}`);
    const body = document.getElementById("patients-body");
    body.innerHTML = "";
    for (const p of page.items) {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${p.last_name}</td><td>${p.first_name}</td><td>${p.fiscal_code}</td>` +
            `<td>${p.email}</td><td>${p.phone || "-"}</td>` +
            `<td><button class="btn-secondary btn-small" data-action="edit" data-id="${p.id}">Modifica</button>
                 <button class="btn-danger" data-action="delete" data-id="${p.id}">Elimina</button></td>`;
        body.appendChild(row);
        row.querySelector('[data-action="edit"]').addEventListener("click", () => fillPatientForm(p));
        row.querySelector('[data-action="delete"]').addEventListener("click", async () => {
            if (!confirm(`Eliminare il paziente ${p.last_name} ${p.first_name}?`)) return;
            try {
                await apiSend("DELETE", `/api/patients/${p.id}`);
                await loadPatients();
            } catch (err) {
                showPageMessage("error", err.message);
            }
        });
    }
}

patientForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("patient-id").value;
    const data = {
        first_name: document.getElementById("p-first").value,
        last_name: document.getElementById("p-last").value,
        fiscal_code: document.getElementById("p-cf").value,
        birth_date: document.getElementById("p-birth").value,
        email: document.getElementById("p-email").value,
        phone: document.getElementById("p-phone").value || null,
    };
    try {
        if (id) {
            await apiSend("PATCH", `/api/patients/${id}`, data);
        } else {
            await apiSend("POST", "/api/patients", data);
        }
        fillPatientForm(null);
        showPageMessage("success", "Paziente salvato.");
        await loadPatients();
    } catch (err) {
        showPageMessage("error", err.message);
    }
});

document.getElementById("patient-form-reset").addEventListener("click", () => fillPatientForm(null));
patientSearch.addEventListener("input", loadPatients);

// --- medici ---

const doctorForm = document.getElementById("doctor-form");

function fillDoctorForm(d) {
    document.getElementById("doctor-id").value = d ? d.id : "";
    document.getElementById("doctor-form-title").textContent =
        d ? `Modifica medico: ${d.last_name} ${d.first_name}` : "Nuovo medico";
    document.getElementById("d-first").value = d ? d.first_name : "";
    document.getElementById("d-last").value = d ? d.last_name : "";
    document.getElementById("d-spec").value = d ? d.specialization : "";
    document.getElementById("d-email").value = d ? d.email : "";
    document.getElementById("d-phone").value = d && d.phone ? d.phone : "";
    document.getElementById("d-duration").value = d ? d.visit_duration_minutes : 30;
}

async function loadDoctorsAdmin() {
    const page = await apiGet("/api/doctors?size=100");
    const body = document.getElementById("doctors-body");
    body.innerHTML = "";
    for (const d of page.items) {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${d.last_name}</td><td>${d.first_name}</td><td>${d.specialization}</td>` +
            `<td>${d.email}</td><td>${d.visit_duration_minutes} min</td>` +
            `<td><button class="btn-secondary btn-small" data-action="edit">Modifica</button>
                 <button class="btn-danger" data-action="delete">Elimina</button></td>`;
        body.appendChild(row);
        row.querySelector('[data-action="edit"]').addEventListener("click", () => fillDoctorForm(d));
        row.querySelector('[data-action="delete"]').addEventListener("click", async () => {
            if (!confirm(`Eliminare il medico ${d.last_name} ${d.first_name}?`)) return;
            try {
                await apiSend("DELETE", `/api/doctors/${d.id}`);
                await loadDoctorsAdmin();
            } catch (err) {
                showPageMessage("error", err.message);
            }
        });
    }
}

doctorForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("doctor-id").value;
    const data = {
        first_name: document.getElementById("d-first").value,
        last_name: document.getElementById("d-last").value,
        specialization: document.getElementById("d-spec").value,
        email: document.getElementById("d-email").value,
        phone: document.getElementById("d-phone").value || null,
        visit_duration_minutes: Number(document.getElementById("d-duration").value),
    };
    try {
        if (id) {
            await apiSend("PATCH", `/api/doctors/${id}`, data);
        } else {
            await apiSend("POST", "/api/doctors", data);
        }
        fillDoctorForm(null);
        showPageMessage("success", "Medico salvato.");
        await loadDoctorsAdmin();
    } catch (err) {
        showPageMessage("error", err.message);
    }
});

document.getElementById("doctor-form-reset").addEventListener("click", () => fillDoctorForm(null));

// --- avvio ---

if (adminUser && adminUser.role === "admin") {
    Promise.all([loadAgendaDoctors(), loadAgenda(), loadPatients(), loadDoctorsAdmin()])
        .catch((err) => showPageMessage("error", err.message));
}
