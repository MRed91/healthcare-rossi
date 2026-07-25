async function checkHealth() {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");
    const version = document.getElementById("status-version");

    try {
        const res = await fetch("/health");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        dot.classList.add("ok");
        text.textContent = "Servizio attivo";
        version.textContent = `API v${data.version}`;
    } catch (err) {
        dot.classList.add("ko");
        text.textContent = "Servizio non raggiungibile";
    }
}

checkHealth();
