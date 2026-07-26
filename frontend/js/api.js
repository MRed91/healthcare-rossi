async function apiGet(path) {
    const res = await fetch(path);
    if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body && body.detail ? body.detail : `Errore HTTP ${res.status}`);
    }
    return res.json();
}

async function apiSend(method, path, data) {
    const res = await fetch(path, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: data !== undefined ? JSON.stringify(data) : undefined,
    });
    if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body && body.detail ? body.detail : `Errore HTTP ${res.status}`);
    }
    return res.status === 204 ? null : res.json();
}
