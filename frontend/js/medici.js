const filterSelect = document.getElementById("specialization-filter");
const list = document.getElementById("doctors-list");
const message = document.getElementById("doctors-message");

async function loadSpecializations() {
    const specializations = await apiGet("/api/doctors/specializations");
    for (const spec of specializations) {
        const option = document.createElement("option");
        option.value = spec;
        option.textContent = spec;
        filterSelect.appendChild(option);
    }
}

async function loadDoctors() {
    const spec = filterSelect.value;
    const url = spec ? `/api/doctors?specialization=${encodeURIComponent(spec)}` : "/api/doctors";
    message.hidden = true;
    list.innerHTML = "";

    try {
        const page = await apiGet(url);
        if (page.items.length === 0) {
            message.textContent = "Nessun medico trovato per questa specializzazione.";
            message.hidden = false;
            return;
        }
        for (const doc of page.items) {
            const card = document.createElement("article");
            card.className = "doctor-card";
            card.innerHTML = `
                <h3>Dott. ${doc.first_name} ${doc.last_name}</h3>
                <p class="specialization">${doc.specialization}</p>
                <p class="detail">Durata visita: ${doc.visit_duration_minutes} minuti</p>
                <p style="margin-top: 0.75rem;">
                    <a class="btn-secondary btn-small" style="text-decoration: none;"
                       href="/prenota.html?doctor=${doc.id}">Prenota</a>
                </p>
            `;
            list.appendChild(card);
        }
    } catch (err) {
        message.textContent = err.message;
        message.hidden = false;
    }
}

filterSelect.addEventListener("change", loadDoctors);

loadSpecializations().then(loadDoctors).catch(() => {
    message.textContent = "Servizio non raggiungibile";
    message.hidden = false;
});
