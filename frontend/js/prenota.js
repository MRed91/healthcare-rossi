const doctorSelect = document.getElementById("doctor-select");
const daySelect = document.getElementById("day-input");
const slotsSection = document.getElementById("slots-section");
const slotsBox = document.getElementById("slots");
const confirmBtn = document.getElementById("confirm-btn");
const messageBox = document.getElementById("booking-message");

let selectedSlot = null;

function showMessage(type, html) {
    messageBox.className = "alert alert-" + type;
    messageBox.innerHTML = html;
    messageBox.hidden = false;
}

async function loadDoctors() {
    const page = await apiGet("/api/doctors?size=100");
    for (const doc of page.items) {
        const option = document.createElement("option");
        option.value = doc.id;
        option.textContent = `${doc.last_name} ${doc.first_name} - ${doc.specialization}`;
        doctorSelect.appendChild(option);
    }
    const wanted = new URLSearchParams(window.location.search).get("doctor");
    if (wanted) doctorSelect.value = wanted;
}

async function loadPatientsForAdmin() {
    const user = getUser();
    if (!user || user.role !== "admin") return;
    document.getElementById("patient-field").hidden = false;
    const page = await apiGet("/api/patients?size=100");
    const select = document.getElementById("patient-select");
    for (const p of page.items) {
        const option = document.createElement("option");
        option.value = p.id;
        option.textContent = `${p.last_name} ${p.first_name} (${p.fiscal_code})`;
        select.appendChild(option);
    }
}

async function loadSlots() {
    selectedSlot = null;
    confirmBtn.disabled = true;
    slotsBox.innerHTML = "";
    messageBox.hidden = true;
    if (!doctorSelect.value || !daySelect.value) return;

    const slots = await apiGet(`/api/doctors/${doctorSelect.value}/slots?day=${daySelect.value}`);
    slotsSection.hidden = false;
    if (slots.length === 0) {
        slotsBox.innerHTML = '<p class="hint">Nessun orario disponibile in questa giornata.</p>';
        return;
    }
    for (const iso of slots) {
        const btn = document.createElement("button");
        btn.className = "slot";
        btn.textContent = iso.slice(11, 16);
        btn.addEventListener("click", () => {
            document.querySelectorAll(".slot.selected").forEach((s) => s.classList.remove("selected"));
            btn.classList.add("selected");
            selectedSlot = iso;
            confirmBtn.disabled = false;
        });
        slotsBox.appendChild(btn);
    }
}

async function confirmBooking() {
    const user = getUser();
    if (!user) {
        window.location.href = "/login.html?next=" + encodeURIComponent("/prenota.html?doctor=" + doctorSelect.value);
        return;
    }
    const data = {
        doctor_id: Number(doctorSelect.value),
        scheduled_at: selectedSlot,
        reason: document.getElementById("reason-input").value || null,
    };
    if (user.role === "admin") {
        data.patient_id = Number(document.getElementById("patient-select").value);
    }
    try {
        const appointment = await apiSend("POST", "/api/appointments", data);
        const when = new Date(appointment.scheduled_at).toLocaleString("it-IT",
            { dateStyle: "full", timeStyle: "short" });
        const link = user.role === "admin" ? "/admin.html" : "/area-personale.html";
        await loadSlots();
        showMessage("success",
            `Prenotazione confermata per ${when} con il Dott. ${appointment.doctor.last_name}. ` +
            `<a href="${link}">Vai alle prenotazioni</a>`);
    } catch (err) {
        showMessage("error", err.message);
    }
}

daySelect.min = new Date().toISOString().slice(0, 10);
doctorSelect.addEventListener("change", loadSlots);
daySelect.addEventListener("change", loadSlots);
confirmBtn.addEventListener("click", confirmBooking);

loadDoctors().then(loadSlots);
loadPatientsForAdmin();
